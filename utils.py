from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import streamlit as st
import base64

def send_email(recipients, subject, html_body):
    """
    Unified function to send one or multiple emails via Gmail API.
    'recipients' can be a string (single email) or a list of strings.
    """
    try:
        # Setup Gmail API Service
        creds_info = st.secrets["GMAIL_TOKEN"]
        creds = Credentials.from_authorized_user_info(creds_info)
        service = build('gmail', 'v1', credentials=creds)
        platform_email = st.secrets["EMAIL"]
        
        if isinstance(recipients, str):
            recipients = [recipients]

        for email in recipients:
            msg = MIMEMultipart()
            msg["From"] = platform_email
            msg["To"] = email
            msg["Subject"] = subject
            msg.attach(MIMEText(html_body, "html"))

            # Encode and Send
            raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            service.users().messages().send(userId='me', body={'raw': raw_message}).execute()
        
        return True

    except Exception as e:
        print(f"Gmail API Error: {e}")
        return False
