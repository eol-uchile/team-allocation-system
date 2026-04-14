import streamlit as st
import pandas as pd
import time
from db import get_connection, release_connection
from utils import send_email

FORMS_PASSWORD = st.secrets["FORMS_PASSWORD"]

with open("./templates/indiv_directory_contact.html", "r") as f:
    INDIV_DIRECTORY_CONTACT_HTML_TEMPLATE = f.read()

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

@st.dialog("Contact Member")
def contact_dialog(member_name, member_email):
    st.write(f"Send a message to **{member_name}**")
    sender_mail = st.text_input("Your Email Address (Please use the education email address of your institution, it will be shared with this participant)")
    message = st.text_area("Your Message", height=150)
    
    if st.button("Send Email", type="primary", use_container_width=True):
        if sender_mail and message:
            with st.spinner(text="Sending email...", show_time=False, width="content"):                
                html_body = INDIV_DIRECTORY_CONTACT_HTML_TEMPLATE.format(
                    recipient_name=member_name,
                    sender_email=sender_mail,
                    message_body=message
                )
                if send_email(member_email, "Inquiry: Poverty Alleviation Challenge Connection", html_body):
                    st.success("Message sent!")
                    time.sleep(2)
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
            SELECT name, nationality, university, major, education_level, personal_profile, email 
            FROM members 
            WHERE group_link IS NULL 
            ORDER BY name ASC
        """
        df = pd.read_sql(query, conn)
    except Exception as e:
        st.error("Database connection error.")
        print(f'Error on indiv_directory: {e}')
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
                        st.write(row['personal_profile'])
                    
                    if st.button("Contact Member", key=f"contact_{idx}", use_container_width=True):
                        contact_dialog(row['name'], row['email'])

if __name__ == "__main__":
    main()
