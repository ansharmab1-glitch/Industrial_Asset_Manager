import streamlit as st
import pandas as pd
import time

def render_dashboard(conn, cursor):
    st.header("Operational Asset Map")
    c1, c2, c3 = st.columns(3)
    df_assets = pd.read_sql_query("SELECT * FROM assets", conn)
    df_tickets = pd.read_sql_query("SELECT * FROM tickets WHERE status='Open'", conn)
    
    c1.metric("Total Managed Equipment", f"{len(df_assets):,}")
    c2.metric("Active Maintenance Tickets", f"{len(df_tickets):,}")
    c3.metric("Machines Under Repair", f"{len(df_assets[df_assets['status'] == 'Under Repair'])}")
    
    st.subheader("Global Safety Status Matrix")
    df_safety = pd.read_sql_query("SELECT name AS `Plant`, fire_status AS `Fire Status`, gas_leakage_status AS `Gas Leakage Status` FROM plants", conn)
    
    def color_alerts(val):
        color = '#FF4B4B' if val == 'Alert' else ''
        return f'background-color: {color}'
    st.dataframe(df_safety.style.map(color_alerts, subset=['Fire Status', 'Gas Leakage Status']), use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.subheader("Emergency Override & Safety Controls")
    st.caption("Use this panel to manually trigger or resolve Fire and Gas leakage alerts across industrial sectors.")
    
    with st.form("safety_override_form"):
        df_plant_names = pd.read_sql_query("SELECT name FROM plants ORDER BY name", conn)
        target_plant = st.selectbox("Target Industrial Sector:", df_plant_names['name'])
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            sensor_type = st.selectbox("Sensor System:", ["Fire", "Gas Leakage"])
        with col_s2:
            new_status = st.selectbox("Override Status:", ["Normal", "Alert"])
            
        if st.form_submit_button("Update Plant Safety Protocols"):
            column_to_update = "fire_status" if sensor_type == "Fire" else "gas_leakage_status"
            cursor.execute(f"UPDATE plants SET {column_to_update} = %s WHERE name = %s", (new_status, target_plant))
            conn.commit()
            st.success(f"Safety protocols for {target_plant} successfully updated to {new_status} state.")
            time.sleep(1.5)
            st.rerun()

    st.markdown("---")
    st.subheader("Peak Emergency Level by Industrial Plant")
    df_chart = pd.read_sql_query("""
        SELECT p.name AS plant_name, IFNULL(MAX(t.urgency_level), 0) AS max_urgency
        FROM plants p
        LEFT JOIN assets a ON p.plant_id = a.plant_id
        LEFT JOIN tickets t ON a.asset_id = t.asset_id AND t.status = 'Open'
        GROUP BY p.name
    """, conn)
    st.bar_chart(data=df_chart, x='plant_name', y='max_urgency', color="#FF4B4B")