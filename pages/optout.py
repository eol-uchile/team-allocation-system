import streamlit as st
from db import get_connection, release_connection

def main():
    if "opt_out_done" not in st.session_state:
        st.session_state.opt_out_done = False

    if st.session_state.opt_out_done:
        st.title("Opt-out Successful")
        st.success("You have been successfully removed from the group.")
        st.info("Your individual registration remains active. You can now close this window.")
        return

    token = st.query_params.get("token")
    
    if not token:
        st.error("Invalid or missing access token.")
        return

    st.title("Confirm Group Opt-out")
    
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT id, name FROM members WHERE opt_out_token = %s", (token,))
        member = cur.fetchone()
        
        if not member:
            st.error("This link is invalid or has already been used.")
            return

        member_id, member_name = member
        st.warning(f"Hello {member_name}, are you sure you want to leave your assigned group?")
        
        if st.button("Confirm Opt-out", type="primary", use_container_width=True):
            cur.execute("""
                UPDATE members 
                SET group_link = NULL, opt_out_token = NULL 
                WHERE id = %s
            """, (member_id,))
            conn.commit()
            
            st.session_state.opt_out_done = True
            st.rerun()

    except Exception as e:
        st.error(f"Database error: {e}")
    finally:
        if conn:
            release_connection(conn)
