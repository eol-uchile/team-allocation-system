import streamlit as st
from db import get_connection, release_connection
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import secrets
import os
import base64
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

DOMAIN = os.getenv("DOMAIN", "localhost:8501")
FORMS_PASSWORD = st.secrets["FORMS_PASSWORD"]

with open("./templates/join_group.html", "r") as f:
    JOIN_GROUP_HTML_TEMPLATE = f.read()


def check_registration_access():
    if st.session_state.get("public_authenticated", False):
        return True
    st.title("Registration Access")
    code_input = st.text_input("Password", type="password")
    if st.button("Enter"):
        if code_input == FORMS_PASSWORD:
            st.session_state.public_authenticated = True
            st.rerun()
        else:
            st.error("Invalid Password")
    return False

def get_group_leader_email(group_id):
    leader_email = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT email FROM members WHERE group_link = %s AND status = 'Leader' LIMIT 1", (str(group_id),))
        result = cur.fetchone()
        if result:
            leader_email = result[0]
    except Exception as e:
        print(e)
    finally:
        if cur:
            cur.close()
        if conn:
            release_connection(conn)
    return leader_email

def send_application_alert_to_leader(leader_email, applicant_name, group_name, reason, application_token):
    try:
        # 1. Setup Gmail API Service
        creds_info = st.secrets["GMAIL_TOKEN"]
        creds = Credentials.from_authorized_user_info(creds_info)
        service = build('gmail', 'v1', credentials=creds)
        
        sender_email = st.secrets["EMAIL"]
        domain = os.getenv("DOMAIN", "localhost:8501") # Ensure DOMAIN is accessible here

        # 2. Prepare the Message Content
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = leader_email
        msg["Subject"] = f"New Application for {group_name}"

        # Using https as standard for the accept_url
        accept_url = f"https://{domain}/?page=accept_member&token={application_token}"
        
        body = JOIN_GROUP_HTML_TEMPLATE.format(
            applicant_name=applicant_name, 
            group_name=group_name, 
            reason=reason, 
            accept_url=accept_url
        )
        msg.attach(MIMEText(body, "html"))

        # 3. Encode the message for Gmail API
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        
        # 4. Send the message
        service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        
        return True

    except Exception as e:
        # Log the error for debugging on the server console
        print(f"Leader Notification Error: {e}")
        return False

def main():
    if not check_registration_access():
        st.stop()

    st.title("Join a Group")
    st.info("Already registered? Select an incomplete group to send your application.")
    
    email_input = st.text_input("Enter your registered email to verify your identity")
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT id, group_name FROM groups WHERE is_complete = False")
        groups = cur.fetchall()
    except Exception as e:
        st.error("Could not fetch groups.")
        groups = []

    group_options = {name: gid for gid, name in groups}
    selected_group_name = st.selectbox("Select the group you want to join", options=["Select..."] + list(group_options.keys()))
    
    join_reason = st.text_area("Why do you want to join this specific group?", placeholder="Share your motivation or relevant skills with the group leader...")

    if st.button("Submit Application", type="primary", use_container_width=True):
        if email_input and selected_group_name != "Select..." and join_reason.strip() != "":
            try:
                cur.execute("SELECT name, group_link FROM members WHERE email = %s", (email_input,))
                user = cur.fetchone()

                if not user:
                    st.error("Email not found. Please register as an individual first.")
                elif user[1] is not None:
                    st.error("You are already assigned to a group.")
                else:
                    target_group_id = group_options[selected_group_name]
                    application_token = secrets.token_urlsafe(32)
                    cur.execute("""
                        UPDATE members 
                        SET status = 'pending', group_link = %s, application_token = %s 
                        WHERE email = %s
                    """, (str(target_group_id), application_token, email_input))

                    target_group_id = group_options[selected_group_name]
                    update_query = """
                        UPDATE members 
                        SET status = 'pending', group_link = %s 
                        WHERE email = %s
                    """
                    cur.execute(update_query, (target_group_id, email_input))
                    conn.commit()
                    leader_email = get_group_leader_email(target_group_id)
                    if leader_email:
                        send_application_alert_to_leader(leader_email, user[0], selected_group_name, join_reason, application_token)
                    st.success(f"Application sent! The leader of {selected_group_name} has been notified.")
                    time.sleep(3)
                    st.query_params.clear()
                    st.rerun()

            except Exception as e:
                if conn:    
                    conn.rollback()
                st.error("Connection Lost. Please refresh the page to reconnect.")
                if st.button("Refresh Page"):
                    st.rerun()
            finally:
                if cur:
                    cur.close()
                if conn:
                    release_connection(conn)    
        else:
            st.warning("Please fill in all fields, including your reason for joining.")
    else:
        if cur:
            cur.close()
        if conn:
            release_connection(conn)

if __name__ == "__main__":
    main()
