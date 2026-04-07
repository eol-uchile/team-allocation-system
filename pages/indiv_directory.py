import streamlit as st
import pandas as pd
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from db import get_connection, release_connection

FORMS_PASSWORD = st.secrets["FORMS_PASSWORD"]

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

def send_contact_email(recipient_email, recipient_name, sender_email, message_body):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    platform_email = st.secrets["EMAIL"]
    app_password = st.secrets["EMAIL_PASSWORD"]

    msg = MIMEMultipart()
    msg["From"] = platform_email
    msg["To"] = recipient_email
    msg["Subject"] = f"Inquiry: Poverty Alleviation Challenge Connection"

    body = f"""
    <html>
        <body>
            <p><strong>From:</strong> {sender_email}</p>
            <p><strong>Message:</strong></p>
            <p style="white-space: pre-wrap; background-color: #f9f9f9; padding: 10px; border-radius: 5px;">
                {message_body}
            </p>
            <hr>
            <p>To reply, please email <strong>{sender_email}</strong> directly.</p>
        </body>
    </html>
    """
    msg.attach(MIMEText(body, "html"))
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(platform_email, app_password)
        server.send_message(msg)
        server.quit()
        return True
    except:
        return False

@st.dialog("Contact Member")
def contact_dialog(member_name, member_email):
    st.write(f"Send a message to **{member_name}**")
    sender_mail = st.text_input("Your Email Address (Your email will be shared with these participant)")
    message = st.text_area("Your Message", height=150)
    
    if st.button("Send Email", type="primary", use_container_width=True):
        if sender_mail and message:
            with st.spinner(text="Sending email...", show_time=False, width="content"):
                if send_contact_email(member_email, member_name, sender_mail, message):
                    st.success("Message sent!")
                    time.sleep(1)
                    st.rerun()
        else:
            st.error("Please fill in all fields.")

def main():
    if not check_registration_access():
        st.stop()

    st.title("Individual Member Directory")
    st.markdown("Browse individual participants looking for a group. Search by name, major, or skills.")
    
    conn = get_connection()
    try:
        query = """
            SELECT name, nationality, university, major, education_level, introductory_text, email 
            FROM members 
            WHERE group_link IS NULL 
            ORDER BY name ASC
        """
        df = pd.read_sql(query, conn)
    except:
        st.error("Database connection error.")
        df = pd.DataFrame()
    finally:
        release_connection(conn)

    if df.empty:
        st.info("No members are currently listed as looking for a group.")
        return

    cols_per_row = 2
    for i in range(0, len(df), cols_per_row):
        row_data = df.iloc[i : i + cols_per_row]
        cols = st.columns(cols_per_row)
        
        for j, (idx, row) in enumerate(row_data.iterrows()):
            with cols[j]:
                with st.container(border=True):
                    # Header Section
                    st.subheader(row['name'])
                    st.caption(f"{row['nationality']} | {row['university']} ({row['education_level']})")
                    st.markdown(f"**Major:** {row['major']}")
                                        
                    # Introduction Display
                    with st.expander("View Introduction", expanded=False):
                        st.write(row['introductory_text'])
                    
                    if st.button("Contact Member", key=f"contact_{idx}", use_container_width=True):
                        contact_dialog(row['name'], row['email'])

if __name__ == "__main__":
    main()
