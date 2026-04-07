import streamlit as st
from db import get_connection, release_connection
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib


def send_application_result_email(recipient_email, recipient_name, group_name, accepted=True):
    platform_email = st.secrets["EMAIL"]
    app_password = st.secrets["EMAIL_PASSWORD"]

    msg = MIMEMultipart()
    msg["From"] = platform_email
    msg["To"] = recipient_email
    msg["Subject"] = f"Update: Your application to {group_name}"

    status_text = "accepted" if accepted else "declined"
    color = "#28a745" if accepted else "#dc3545"

    body = f"""
    <div style="font-family: sans-serif; color: #222;">
        <p>Hi {recipient_name},</p>
        <p>The group leader of <strong>{group_name}</strong> has reviewed your application.</p>
        <p>Your request has been <strong style="color: {color};">{status_text}</strong>.</p>
        <p>Best regards,<br>The Poverty Alleviation Challenge Team</p>
    </div>
    """
    
    msg.attach(MIMEText(body, "html"))
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(platform_email, app_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False


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
        cur.execute("SELECT group_name FROM groups WHERE id = %s", (group_id,))
        group_res = cur.fetchone()
        group_name = group_res[0] if group_res else "Unknown Group"

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
                    SELECT COUNT(id), COUNT(DISTINCT university_country)
                    FROM members
                    WHERE group_link = %s AND status != 'pending'
                """, (group_id,))
                
                count, distinct_uni_countries = cur.fetchone()
                
                is_complete = (count > 1 and distinct_uni_countries > 1)
                
                cur.execute("""
                    UPDATE groups
                    SET is_complete = %s
                    WHERE id = %s
                """, (is_complete, group_id))
                
                conn.commit()
                send_application_result_email(member_email, member_name, group_name, accepted=True)
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
                conn.commit()
                st.info("Application declined.")
                send_application_result_email(member_email, member_name, group_name, accepted=False)
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
