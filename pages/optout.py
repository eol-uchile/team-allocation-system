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
            cur.execute("SELECT group_link FROM members WHERE id = %s", (member_id,))
            group_id = cur.fetchone()[0]

            # Perform the opt-out
            cur.execute("""
                UPDATE members 
                SET group_link = NULL, opt_out_token = NULL 
                WHERE id = %s
            """, (member_id,))
            
            if group_id:
                # Count remaining members and unique nationalities
                cur.execute("""
                    SELECT COUNT(id), COUNT(DISTINCT nationality) 
                    FROM members 
                    WHERE group_link = %s
                """, (group_id,))
                
                count, nationalities = cur.fetchone()
                
                # Check if the conditions for a complete group are still met
                is_complete = (count > 1 and nationalities > 1)
                
                # Update the groups table accordingly
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
        if conn:
            release_connection(conn)
