import streamlit as st
import pandas as pd
import time
from database import EQUIPMENT_SCHEMA, TABLE_MAPPING

def render_equipment_management(conn, cursor):
    st.header("Equipment Registry Management")
    m_tab1, m_tab2, m_tab3 = st.tabs(["Deploy New Asset", "Update Existing Asset", "Delete Asset"])
    
    # Sub-Tab A: Deploy New Machinery
    with m_tab1:
        st.subheader("Deploy New Base Machinery & Specifications")
        df_plants = pd.read_sql_query("SELECT * FROM plants", conn)
        plant_options = {row['name']: row['plant_id'] for _, row in df_plants.iterrows()}
        
        c_sel1, c_sel2 = st.columns(2)
        with c_sel1:
            selected_plant = st.selectbox("Deploy Target Sector Unit", list(plant_options.keys()))
        with c_sel2:
            asset_type = st.selectbox("Component Taxonomy Class", list(EQUIPMENT_SCHEMA.keys()))
        
        asset_name = st.text_input("Machine/Equipment Label Code", placeholder="e.g. HT Induction Motor 5001")
        st.markdown(f"##### {asset_type} Engineering Specifications")
        
        spec_inputs = {}
        cols = st.columns(4)
        idx = 0
        
        for field, f_type in EQUIPMENT_SCHEMA[asset_type].items():
            clean_label = field.replace('_', ' ').title()
            with cols[idx % 4]:
                if f_type == int:
                    spec_inputs[field] = st.number_input(clean_label, step=1, value=0)
                elif f_type == float:
                    spec_inputs[field] = st.number_input(clean_label, format="%.2f", value=0.0)
                else:
                    spec_inputs[field] = st.text_input(clean_label, placeholder="Value")
            idx += 1
        
        if st.button("Commit Complete Asset to Infrastructure"):
            if asset_name:
                p_id = plant_options[selected_plant]
                cursor.execute("INSERT INTO assets (plant_id, name, asset_type, status) VALUES (%s, %s, %s, %s)", (p_id, asset_name, asset_type, "Operational"))
                new_asset_id = cursor.lastrowid
                
                s_cols = list(spec_inputs.keys())
                placeholders = ", ".join(["%s"] * len(s_cols))
                query = f"INSERT INTO {TABLE_MAPPING[asset_type]} (asset_id, {', '.join(s_cols)}) VALUES (%s, {placeholders})"
                vals = [new_asset_id] + list(spec_inputs.values())
                
                cursor.execute(query, tuple(vals))
                conn.commit()
                st.success(f"SUCCESS: {asset_name} deployed to {selected_plant} with all engineering specifications attached!")
                time.sleep(1.5)
                st.rerun()
            else:
                st.warning("Equipment requires a valid identifier name.")
    
    # Sub-Tab B: Update Existing Machinery
    with m_tab2:
        st.subheader("Asset Correction Protocol")
        update_id = st.number_input("Target Equipment ID to Update:", min_value=1, step=1)
        
        cursor.execute("SELECT plant_id, name, asset_type, status FROM assets WHERE asset_id = %s", (update_id,))
        asset_data = cursor.fetchone()
        
        if asset_data:
            p_id, a_name, a_type, a_status = asset_data
            st.info(f"Loaded: **{a_name}** | Type: **{a_type}**")
            
            df_plants = pd.read_sql_query("SELECT * FROM plants", conn)
            plant_options = {row['name']: row['plant_id'] for _, row in df_plants.iterrows()}
            default_plant_name = [k for k, v in plant_options.items() if v == p_id][0]
            
            u_col1, u_col2 = st.columns(2)
            with u_col1:
                new_plant_name = st.selectbox("Update Sector Unit", list(plant_options.keys()), index=list(plant_options.keys()).index(default_plant_name))
                new_name = st.text_input("Update Equipment Label", value=a_name)
            with u_col2:
                valid_statuses = ["Operational", "Under Repair", "Decommissioned"]
                default_status_idx = valid_statuses.index(a_status) if a_status in valid_statuses else 0
                new_status = st.selectbox("Update Status", valid_statuses, index=default_status_idx)
            
            st.markdown(f"##### Update {a_type} Specifications")
            target_table = TABLE_MAPPING[a_type]
            cursor.execute(f"SELECT * FROM {target_table} WHERE asset_id = %s", (update_id,))
            spec_data = cursor.fetchone()
            
            spec_cols = [desc[0] for desc in cursor.description] if spec_data else []
            spec_dict = dict(zip(spec_cols, spec_data)) if spec_data else {}
            
            update_inputs = {}
            cols_upd = st.columns(4)
            idx_upd = 0
            
            for field, f_type in EQUIPMENT_SCHEMA[a_type].items():
                clean_label = field.replace('_', ' ').title()
                current_val = spec_dict.get(field, 0 if f_type in [int, float] else "")
                
                with cols_upd[idx_upd % 4]:
                    if f_type == int:
                        update_inputs[field] = st.number_input(f"{clean_label}", step=1, value=int(current_val) if current_val else 0)
                    elif f_type == float:
                        update_inputs[field] = st.number_input(f"{clean_label}", format="%.2f", value=float(current_val) if current_val else 0.0)
                    else:
                        update_inputs[field] = st.text_input(f"{clean_label}", value=str(current_val))
                idx_upd += 1
                
            if st.button("Commit Updates to Database"):
                new_p_id = plant_options[new_plant_name]
                cursor.execute("UPDATE assets SET plant_id=%s, name=%s, status=%s WHERE asset_id=%s", (new_p_id, new_name, new_status, update_id))
                
                if spec_data:
                    set_clause = ", ".join([f"{k} = %s" for k in update_inputs.keys()])
                    vals = list(update_inputs.values()) + [update_id]
                    cursor.execute(f"UPDATE {target_table} SET {set_clause} WHERE asset_id = %s", tuple(vals))
                else:
                    ins_cols = list(update_inputs.keys())
                    ins_placeholders = ", ".join(["%s"] * len(ins_cols))
                    ins_query = f"INSERT INTO {target_table} (asset_id, {', '.join(ins_cols)}) VALUES (%s, {ins_placeholders})"
                    ins_vals = [update_id] + list(update_inputs.values())
                    cursor.execute(ins_query, tuple(ins_vals))
                    
                conn.commit()
                st.success(f"Asset #{update_id} has been completely updated.")
                time.sleep(1.5)
                st.rerun()
        else:
            st.warning("Enter a valid Equipment ID to load parameters.")

    # Sub-Tab C: Delete Machinery
    with m_tab3:
        st.subheader("Asset Deletion Protocol")
        with st.form("delete_asset_form"):
            delete_id = st.number_input("Target Equipment ID to Delete:", min_value=1, step=1)
            if st.form_submit_button("Permanently Delete Asset"):
                cursor.execute("SELECT name FROM assets WHERE asset_id = %s", (delete_id,))
                asset_to_delete = cursor.fetchone()
                if asset_to_delete:
                    cursor.execute("DELETE FROM assets WHERE asset_id = %s", (delete_id,))
                    conn.commit()
                    st.error(f"DELETED: Asset #{delete_id} ({asset_to_delete[0]}) has been removed from the database.")
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.warning("Action Failed: Equipment ID not found in the current registry.")