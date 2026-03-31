import streamlit as st
import pandas as pd
from db import get_connection, release_connection
import os

MANAGER_PASSWORD = st.secrets["MANAGER_PASSWORD"]

def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if st.session_state.authenticated:
        return True
    st.title("Manager Access Required")
    pwd_input = st.text_input("Enter Manager Password", type="password")
    if st.button("Login"):
        if pwd_input == MANAGER_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Invalid Password")
    return False

def force_full_width():
    st.markdown(
        """
        <style>
            .block-container {
                max-width: 100% !important;
                padding: 5rem 2rem 2rem 2rem !important;
            }
            .stDataEditor { width: 100% !important; }
        </style>
        """,
        unsafe_allow_html=True
    )

def update_table(df_to_save, table_name):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        if table_name == "members":
            for _, row in df_to_save.iterrows():
                cur.execute("""
                    UPDATE members 
                    SET name=%s, email=%s, university=%s, nationality=%s, 
                        gender=%s, major=%s, introductory_text=%s 
                    WHERE id=%s
                """, (
                    row['name'], row['email'], row['university'], row['nationality'],
                    row['gender'], row['major'], row['introductory_text'], row['id']
                ))
        elif table_name == "groups":
            for _, row in df_to_save.iterrows():
                cur.execute("""
                    UPDATE groups 
                    SET group_name=%s, topic_introduction=%s, 
                        description_existing_members=%s, expected_members=%s 
                    WHERE id=%s
                """, (
                    row['group_name'], row['topic_introduction'], 
                    row['description_existing_members'], row['expected_members'], row['id']
                ))
        conn.commit()
        cur.close()
    except Exception as e:
        if conn:
            conn.rollback()
        st.error("Connection Timeout")
        st.info("The database connection timed out due to inactivity. Please refresh the page to continue.")
        if st.button("Refresh Page"):
            st.rerun()
        # Stops the traceback from showing when there is an error with the table queries by
        # stopping the app
        st.stop()
    finally:
        if conn:
            release_connection(conn)

@st.dialog("Confirm Changes")
def confirm_save(df, table_name):
    st.markdown(f"### 📋 Review {table_name.replace('_', ' ').title()}")
    st.write("Are you sure you want to push these edits to the live database?")
    st.divider()
    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button("Confirm and Save", type="primary", use_container_width=True):
            update_table(df, table_name)
            st.session_state.show_toast = "Changes saved successfully!"
            st.rerun()
    with col_cancel:
        if st.button("Cancel", use_container_width=True):
            st.rerun()

def main():
    if not check_password():
        st.stop()

    st.set_page_config(layout="wide", page_title="Manager Dashboard")
    force_full_width()

    if "show_toast" in st.session_state:
        st.toast(st.session_state.show_toast)
        del st.session_state.show_toast

    if "view" not in st.session_state:
        st.session_state.view = "home"

    if st.session_state.view == "home":
        st.title("Group Admin")
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("👤 Individuals")
            if st.button("Manage Individuals →", use_container_width=True):
                st.session_state.view = "individuals"
                st.rerun()
        with col2:
            st.subheader("👥 Groups")
            if st.button("Manage Groups →", use_container_width=True):
                st.session_state.view = "groups"
                st.rerun()

    elif st.session_state.view == "individuals":
        if st.button("← Back to Home"):
            st.session_state.view = "home"
            st.rerun()
            
        st.title("👤 Individual Participants")
        
        conn = None
        try:
            conn = get_connection()
            df = pd.read_sql("SELECT * FROM members ORDER BY id ASC", conn)
        except Exception as e:
            print(f"Database Error: {e}")
            st.error("Connection Lost")
            st.info("The database connection timed out. Please refresh the page to reconnect.")
            
            if st.button("Refresh Page"):
                st.rerun()
            st.stop()
        finally:
            if conn:
                release_connection(conn)
        
        indiv_config = {
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "name": st.column_config.TextColumn("Full Name"),
            "email": st.column_config.TextColumn("Email"),
            "nationality": st.column_config.TextColumn("Nationality"),
            "gender": st.column_config.TextColumn("Gender"),
            "university": st.column_config.TextColumn("University"),
            "major": st.column_config.TextColumn("Major"),
            "introductory_text": st.column_config.TextColumn("Introductory Text", width="large"),
        }
        
        edited_df = st.data_editor(
            df, 
            column_config=indiv_config,
            use_container_width=True, 
            height=600, 
            key="indiv_editor",
            hide_index=True
        )
        if st.button("💾 Save Individual Changes", type="primary"):
            confirm_save(edited_df, "members")

    elif st.session_state.view == "groups":
        if st.button("← Back to Home"):
            st.session_state.view = "home"
            st.rerun()
            
        st.title("👥 Group Registrations")
        
        conn = None
        try:
            conn = get_connection()
            df = pd.read_sql("SELECT * FROM groups ORDER BY id ASC", conn)
        finally:
            if conn:
                release_connection(conn)
        
        df['Status'] = df['is_complete'].map({True: "COMPLETE", False: "INCOMPLETE"})

        group_config = {
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "is_complete": None,
            "Status": st.column_config.TextColumn("Status", disabled=True),
            "group_name": st.column_config.TextColumn("Group Name", width="medium"),
            "description_existing_members": st.column_config.TextColumn("Existing members description", width="large"),
            "expected_members": st.column_config.TextColumn("Expected Members Introduction", width="large"),
            "topic_introduction": st.column_config.TextColumn("Topic Introduction", width="large"),
            "team_leader_email": st.column_config.TextColumn("Leader Email", disabled=True)
        }

        edited_df = st.data_editor(
            df, 
            column_config=group_config, 
            use_container_width=True, 
            height=600, 
            key="group_editor",
            hide_index=True
        )
        if st.button("💾 Save Group Changes", type="primary"):
            confirm_save(edited_df, "groups")

if __name__ == "__main__":
    main()
