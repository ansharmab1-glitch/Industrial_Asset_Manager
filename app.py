import streamlit as st
import os
from dotenv import load_dotenv

# Must be the first Streamlit command
st.set_page_config(page_title="Industrial Asset Core", layout="wide")

# Load the hidden environment variables
load_dotenv()

from database import get_db_connection

# Ensure your 'views' folder is set up properly with these files imported!
from views.dashboard import render_dashboard
from views.equipment import render_equipment_management
from views.tickets import render_ticket_management
from views.query import render_query_system
from views.engineer import render_engineer_view


# 1. AUTHENTICATION & LOGIN LOGIC

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "role" not in st.session_state:
    st.session_state["role"] = ""

if not st.session_state["authenticated"]:
    st.title("Enterprise Multi-Plant Management Hub")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        m_user = os.getenv("MANAGER_USER")
        m_pass = os.getenv("MANAGER_PASS")
        e_user = os.getenv("ENGINEER_USER")
        e_pass = os.getenv("ENGINEER_PASS")
        
        st.info(f"**Demo Access (Manager):** \nUser: `{m_user}` | Pass: `{m_pass}`\n\n**Demo Access (Engineer):** \nUser: `{e_user}` | Pass: `{e_pass}`")
        
        with st.form("login_form"):
            st.subheader("System Login")
            input_user = st.text_input("UserID")
            input_pass = st.text_input("Password", type="password")
            
            if st.form_submit_button("Authenticate"):
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT username, role FROM users WHERE username = %s AND password = %s", (input_user, input_pass))
                user_check = cursor.fetchone()
                cursor.close()
                conn.close()
                
                if user_check:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = user_check[0]
                    st.session_state["role"] = user_check[1]
                    st.rerun()
                else:
                    st.error("Invalid credentials. Access denied.")
else:

    # 2. MAIN APPLICATION ROUTING

    conn = get_db_connection()
    cursor = conn.cursor()
    
    h_col1, h_col2 = st.columns([4, 1])
    with h_col1:
        st.title("Multi-Plant Asset and Maintenance Hub")
    with h_col2:
        st.write(f"Logged in as: **{st.session_state['username']}** ({st.session_state['role']})")
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.session_state["role"] = ""
            st.session_state["username"] = ""
            st.rerun()
            
    st.markdown("---")

    if st.session_state["role"] == "Manager":
        tab1, tab2, tab3, tab4 = st.tabs([
            "Plant Dashboard", 
            "Equipment Management", 
            "Ticket Management", 
            "Unified Query System"
        ])

        with tab1:
            render_dashboard(conn, cursor)
        with tab2:
            render_equipment_management(conn, cursor)
        with tab3:
            render_ticket_management(conn, cursor)
        with tab4:
            render_query_system(conn, cursor)

    elif st.session_state["role"] == "Engineer":
        render_engineer_view(conn, cursor)

    cursor.close()
    conn.close()