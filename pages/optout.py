import streamlit as st
from db import get_connection, release_connection

def main():
    if "opt_out_done" not in st.session_state:
        st.session_state.opt_out_done = False

    if st.session_state.opt_out_done:
        st.title("Opt-out Successful")
        st.success("You have been successfully removed from the group.")
        return

    token = st.query_params.get("token")
    
    if not token:
        st.error("Invalid or missing access token.")
        return

    st.title("Confirm Group Opt-out")
    
    conn = None
    cur = None
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
            # Fetch group_id and registration_type
            cur.execute("SELECT group_link, registration_type FROM members WHERE id = %s", (member_id,))
            res = cur.fetchone()
            group_id, reg_type = res[0], res[1]

            # Removal/Update Logic
            if reg_type == 'group_added':
                cur.execute("DELETE FROM members WHERE id = %s", (member_id,))
            else:
                cur.execute("""
                    UPDATE members 
                    SET group_link = NULL, opt_out_token = NULL, status = '' 
                    WHERE id = %s
                """, (member_id,))
            
            # Re-calculate Group Completion
            if group_id:
                # Count non N-members remaining
                cur.execute("""
                    SELECT COUNT(id) 
                    FROM members 
                    WHERE group_link = %s 
                    AND status NOT IN ('pending', 'N Member')
                """, (group_id,))
                
                remaining_core_count = cur.fetchone()[0]
                
                is_complete = (remaining_core_count >= 5)
                
                cur.execute("""
                    UPDATE groups 
                    SET is_complete = %s 
                    WHERE id = %s
                """, (is_complete, group_id))
            
            conn.commit()
            st.session_state.opt_out_done = True
            st.rerun()

    except Exception as e:
        st.error(f"Database error: {e}")
    finally:
        if cur:
            conn.rollback()
            cur.close()
        if conn:
            release_connection(conn)
