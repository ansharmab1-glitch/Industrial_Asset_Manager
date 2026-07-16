import streamlit as st
import pandas as pd
import time

def render_ticket_management(conn, cursor):
    st.header("Diagnostic Ticket Management")
    col_raise, col_close = st.columns(2)
    
    with col_raise:
        st.subheader("File New Diagnostic Report")
        with st.form("ticket_form"):
            target_id = st.number_input("Target Equipment ID", min_value=1, step=1)
            issue_desc = st.text_area("Failure Symptoms Description")
            urgency = st.slider("Severity Rating (1-5)", 1, 5, 3)
            
            if st.form_submit_button("Dispatch Ticket") and issue_desc:
                cursor.execute("SELECT name FROM assets WHERE asset_id = %s", (target_id,))
                asset_check = cursor.fetchone()
                if asset_check:
                    cursor.execute("INSERT INTO tickets (asset_id, issue_description, urgency_level) VALUES (%s, %s, %s)", (target_id, issue_desc, urgency))
                    if urgency >= 4:
                        cursor.execute("UPDATE assets SET status = 'Under Repair' WHERE asset_id = %s", (target_id,))
                    conn.commit()
                    st.success(f"Ticket filed successfully for {asset_check[0]}.")
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error("Target Equipment ID not detected.")

    with col_close:
        st.subheader("Resolve Active Tickets")
        df_open = pd.read_sql_query("SELECT t.ticket_id, a.asset_id, a.name, t.urgency_level FROM tickets t JOIN assets a ON t.asset_id = a.asset_id WHERE t.status = 'Open'", conn)
        
        if not df_open.empty:
            with st.form("close_ticket_form"):
                ticket_map = {f"Ticket #{row['ticket_id']} | Asset {row['asset_id']} ({row['urgency_level']}/5)": row['ticket_id'] for _, row in df_open.iterrows()}
                selected_ticket = st.selectbox("Select Maintenance Issue to Mark as Resolved:", list(ticket_map.keys()))
                
                if st.form_submit_button("Close Ticket & Mark Operational"):
                    t_id = ticket_map[selected_ticket]
                    a_id = df_open.loc[df_open['ticket_id'] == t_id, 'asset_id'].values[0]
                    cursor.execute("UPDATE tickets SET status = 'Closed' WHERE ticket_id = %s", (t_id,))
                    cursor.execute("UPDATE assets SET status = 'Operational' WHERE asset_id = %s", int((a_id[0],)))
                    conn.commit()
                    st.success(f"Ticket #{t_id} Closed. Asset returned to Operational status.")
                    time.sleep(1.5)
                    st.rerun()
        else:
            st.success("All operational tickets are currently resolved!")