import streamlit as st
from db import get_connection, release_connection
from utils import send_email

with open("./templates/accept_member_template.html", "r") as f:
    ACCEPT_MEMBER_TEMPLATE = f.read()


def main():
    if "acceptance_done" not in st.session_state:
        st.session_state.acceptance_done = False

    if st.session_state.acceptance_done:
        st.title("Process Complete")
        st.success("The application has been processed successfully.")
        st.info("You can now close this tab.")
        return

    token = st.query_params.get("token")
    
    if not token:
        st.error("Invalid or missing access token.")
        return

    st.title("Review Group Application")
    
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Identify the pending member
        cur.execute("""
            SELECT id, name, group_link, email
            FROM members
            WHERE application_token = %s AND status = 'pending'
        """, (token,))
        member = cur.fetchone()
        
        if not member:
            st.error("This link is invalid or the application has already been processed.")
            return

        member_id, member_name, group_id, member_email = member       
         
        # Get Group Name
        cur.execute("SELECT group_name, is_complete FROM groups WHERE id = %s", (group_id,))
        group_res = cur.fetchone()
        
        if not group_res:
            st.error("Group not found.")
            return
            
        group_name, is_already_complete = group_res

        st.warning(f"As group leader, do you accept **{member_name}** into **{group_name}**?")
        
        col1, col2 = st.columns(2)
        with col1:
            # If the application gets accepted, update the accepted member on the db and notify
            # them
            if st.button("Confirm and Accept", type="primary", use_container_width=True):
                # Update status to 'Member' and clear application token
                cur.execute("""
                    UPDATE members
                    SET status = 'Member', application_token = NULL
                    WHERE id = %s
                """, (member_id,))
                
                # Recalculate group completion
                cur.execute("""
                    SELECT COUNT(id) FROM members 
                    WHERE group_link = %s AND status NOT IN ('pending', 'N Member')
                """, (group_id,))
                new_count = cur.fetchone()[0]
                
                # Update groups table if the group got filled
                if new_count >= 5:
                    cur.execute("UPDATE groups SET is_complete = TRUE WHERE id = %s", (group_id,))
  
                with st.spinner(text="Processing...", show_time=False, width="content"): 
                    conn.commit()
                    # Handle Email Logic
                    html_body = ACCEPT_MEMBER_TEMPLATE.format(
                        recipient_name=member_name,
                        group_name=group_name,
                        color="#28a745",
                        status_text="accepted"
                    )
                    send_email(member_email, f"Update: Your application to {group_name}", html_body)

                st.session_state.acceptance_done = True
                st.rerun()

        with col2:
            # If the application gets declined, update the declined member on the db and notify
            # them
            if st.button("Decline Application", use_container_width=True):
                cur.execute("""
                    UPDATE members
                    SET group_link = NULL, status = '', application_token = NULL
                    WHERE id = %s
                """, (member_id,))
                with st.spinner(text="Processing...", show_time=False, width="content"): 
                    conn.commit()
                    st.info("Application declined.")
                    # Handle Email Logic
                    html_body = ACCEPT_MEMBER_TEMPLATE.format(
                        recipient_name=member_name,
                        group_name=group_name,
                        color="#dc3545",
                        status_text="declined"
                    )
                    send_email(member_email, f"Update: Your application to {group_name}", html_body)

                st.session_state.acceptance_done = True
                st.rerun()

    except Exception as e:
        st.error(f"Database error: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.rollback()
            release_connection(conn)

if __name__ == "__main__":
    main()
