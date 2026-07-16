import streamlit as st
import pandas as pd
import time

def render_engineer_view(conn, cursor):
    st.header("Assigned Maintenance Tickets")
    st.markdown("Review and resolve open equipment malfunctions across the industrial sectors below.")
    
    engineer_query = """
        SELECT t.ticket_id AS `Ticket ID`, p.name AS `Plant Location`, 
               a.name AS `Equipment Name`, t.issue_description AS `Failure Description`, 
               t.urgency_level AS `Urgency (1-5)`, t.date_raised AS `Date Logged`
        FROM tickets t
        JOIN assets a ON t.asset_id = a.asset_id
        JOIN plants p ON a.plant_id = p.plant_id
        WHERE t.status = 'Open'
        ORDER BY t.urgency_level DESC, t.ticket_id ASC
    """
    df_eng_tickets = pd.read_sql_query(engineer_query, conn)
    
    if not df_eng_tickets.empty:
        df_eng_tickets.reset_index(drop=True, inplace=True)
        df_eng_tickets.index = df_eng_tickets.index + 1
        st.dataframe(df_eng_tickets, use_container_width=True)
        
        st.markdown("---")
        st.subheader("Resolve a Ticket")
        with st.form("engineer_close_ticket"):
            ticket_choices = {f"Ticket #{row['Ticket ID']} | {row['Plant Location']} - {row['Equipment Name']}": row['Ticket ID'] for _, row in df_eng_tickets.iterrows()}
            selected_ticket_str = st.selectbox("Select resolved issue:", list(ticket_choices.keys()))
            
            if st.form_submit_button("Mark as Resolved"):
                resolved_t_id = ticket_choices[selected_ticket_str]
                cursor.execute("SELECT asset_id FROM tickets WHERE ticket_id = %s", (resolved_t_id,))
                linked_asset_id = cursor.fetchone()[0]
                
                cursor.execute("UPDATE tickets SET status = 'Closed' WHERE ticket_id = %s", (resolved_t_id,))
                cursor.execute("UPDATE assets SET status = 'Operational' WHERE asset_id = %s", (linked_asset_id,))
                conn.commit()
                st.success(f"Successfully closed Ticket #{resolved_t_id}. Hardware marked as Operational.")
                time.sleep(1.5)
                st.rerun()
    else:
        st.success("All systems nominal. There are currently no active maintenance tickets assigned.")