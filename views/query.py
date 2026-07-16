import streamlit as st
import pandas as pd
from database import TABLE_MAPPING

def render_query_system(conn, cursor):
    st.header("Unified Asset Query System")
    st.markdown("Filter and inspect industrial equipment across all sectors using the parameters below.")
    
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    
    df_plants = pd.read_sql_query("SELECT name FROM plants ORDER BY name", conn)
    plant_options = ["All Plants"] + df_plants['name'].tolist()
    with f_col1:
        sel_plant = st.selectbox("Plant Sector:", plant_options)
        
    df_cats = pd.read_sql_query("SELECT DISTINCT asset_type FROM assets ORDER BY asset_type", conn)
    cat_options = ["All Categories"] + df_cats['asset_type'].tolist()
    with f_col2:
        sel_cat = st.selectbox("Equipment Category:", cat_options)
        
    with f_col3:
        sel_status = st.selectbox("Operational Status:", ["All Statuses", "Operational", "Under Repair"])
        
    with f_col4:
        search_text = st.text_input("Keyword / ID Search:", placeholder="e.g. Motor or 5012")
        
    base_query = """
        SELECT a.asset_id AS `Equipment ID`, p.name AS `Plant Unit`, 
               a.name AS `Equipment Name`, a.asset_type AS `Category`, 
               a.status AS `Current State`
        FROM assets a
        JOIN plants p ON a.plant_id = p.plant_id
        WHERE 1=1
    """
    params = []
    
    if sel_plant != "All Plants":
        base_query += " AND p.name = %s"
        params.append(sel_plant)
    if sel_cat != "All Categories":
        base_query += " AND a.asset_type = %s"
        params.append(sel_cat)
    if sel_status != "All Statuses":
        base_query += " AND a.status = %s"
        params.append(sel_status)
    if search_text:
        base_query += " AND (a.name LIKE %s OR a.asset_id LIKE %s)"
        wildcard = f"%{search_text}%"
        params.extend([wildcard, wildcard])
        
    base_query += " ORDER BY a.asset_id"
    df_results = pd.read_sql_query(base_query, conn, params=tuple(params))
    
    st.markdown("---")
    st.subheader(f"Query Results: {len(df_results):,} matching records found.")
    
    if not df_results.empty:
        df_results.reset_index(drop=True, inplace=True)
        df_results.index = df_results.index + 1
        df_results.index.name = "Row #"
        st.dataframe(df_results, use_container_width=True)
    else:
        st.warning("Zero industrial assets match your selected filter criteria.")

    # EQUIPMENT DEEP DIVE / SPECIFICATIONS
    st.markdown("---")
    st.subheader("Equipment Deep Dive: Hardware Specifications")
    
    with st.form("equipment_details_form"):
        col_id, col_btn = st.columns([3, 1])
        with col_id:
            detail_id = st.number_input("Target Equipment ID:", min_value=1, step=1)
        with col_btn:
            st.markdown("<br>", unsafe_allow_html=True) 
            submit_details = st.form_submit_button("Fetch Specifications", use_container_width=True)
        
        if submit_details:
            cursor.execute("SELECT name, asset_type, status FROM assets WHERE asset_id = %s", (detail_id,))
            asset_info = cursor.fetchone()
            
            if asset_info:
                a_name, a_type, a_status = asset_info
                st.info(f"**Selected Asset:** {a_name} | **Category:** {a_type} | **State:** {a_status}")
                
                target_table = TABLE_MAPPING.get(a_type)
                if target_table:
                    query = f"SELECT * FROM {target_table} WHERE asset_id = %s"
                    cursor.execute(query, (detail_id,))
                    specs = cursor.fetchone()
                    
                    if specs:
                        columns = [desc[0] for desc in cursor.description]
                        spec_dict = dict(zip(columns, specs))
                        if 'asset_id' in spec_dict:
                            del spec_dict['asset_id']
                        
                        st.write("### Technical Parameters")
                        spec_cols = st.columns(4)
                        col_index = 0
                        
                        for key, value in spec_dict.items():
                            clean_label = key.replace('_', ' ').title()
                            with spec_cols[col_index % 4]:
                                st.metric(label=clean_label, value=str(value))
                            col_index += 1
                    else:
                        st.warning("No extended engineering specifications found for this equipment.")
            else:
                st.error(f"Action Failed: Equipment ID #{detail_id} not found in the registry.")