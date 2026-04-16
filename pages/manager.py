import streamlit as st
import pandas as pd
from db import get_connection, release_connection

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
                        gender=%s, major=%s, personal_profile=%s, department=%s,
                        phone_number=%s, teammate_profile=%s, research_topic=%s, previous_participation=%s, previous_award=%s, project_name=%s, reusing_project=%s, file_uploaded=%s
                    WHERE id=%s
                """, (
                    row['name'], row['email'], row['university'], row['nationality'],
                    row['gender'], row['major'], row['personal_profile'], row['department'], row['phone_number'], row['teammate_profile'], row['research_topic'], row['previous_participation'], row['previous_award'], row['project_name'], row['reusing_project'], row['file_uploaded'], row['id']
                ))
        elif table_name == "groups":
            for _, row in df_to_save.iterrows():
                cur.execute("""
                    UPDATE groups 
                    SET group_name=%s, topic_introduction=%s, 
                        description_existing_members=%s, expected_members=%s, previous_participation=%s, previous_award=%s, project_name=%s, reusing_project=%s, file_uploaded=%s
                    WHERE id=%s
                """, (
                    row['group_name'], row['topic_introduction'], 
                    row['description_existing_members'], row['expected_members'], row['previous_participation'], row['previous_award'], row['project_name'], row['reusing_project'], row['file_uploaded'], row['id']
                ))
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
            print(e)
        st.error("Connection Timeout")
        st.info("The database connection timed out due to inactivity. Please refresh the page to continue.")
        if st.button("Refresh Page"):
            st.rerun()
        # Stops the traceback from showing when there is an error with the table queries by
        # stopping the app
        st.stop()
    finally:
        if cur:
            cur.close()
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
        st.title("Participants and Teams Admin")
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("👤 Participants")
            if st.button("Manage Participants →", use_container_width=True):
                st.session_state.view = "individuals"
                st.rerun()
        with col2:
            st.subheader("👥 Teams")
            if st.button("Manage Teams →", use_container_width=True):
                st.session_state.view = "groups"
                st.rerun()

    elif st.session_state.view == "individuals":
        if st.button("← Back to Home"):
            st.session_state.view = "home"
            st.rerun()
            
        st.title("👤 Participants")

        filter_col1, _ = st.columns([1, 2])
        with filter_col1:
            member_filter = st.selectbox(
                "Filter View",
                options=[
                    "All Members",
                    "Members Without Group",
                    "Confirmed Team Members",
                    "Pending Team Requests"
                ]
            )

        conn = get_connection()
        try:
            query = """
                SELECT m.*, g.group_name as team_name
                FROM members m
                LEFT JOIN groups g ON m.group_link = g.id::text
                ORDER BY g.group_name ASC NULLS LAST, m.name ASC
            """
            df = pd.read_sql(query, conn)
            
            if member_filter == "Members Without Group":
                df = df[df['group_link'].isna() | (df['group_link'] == "")]
            
            elif member_filter == "Confirmed Team Members":
                df = df[(df['group_link'].notna()) & (df['group_link'] != "") & (df['status'] != 'pending')]
            
            elif member_filter == "Pending Team Requests":
                df = df[df['status'] == 'pending']

        finally:
            release_connection(conn)

        indiv_config = {
            "team_name": st.column_config.TextColumn("Team Name", width="medium", disabled=True),
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "name": st.column_config.TextColumn("Full Name"),
            "status": st.column_config.TextColumn("Status"),
            "email": st.column_config.TextColumn("Email"),
            "nationality": st.column_config.TextColumn("Nationality"),
            "gender": st.column_config.TextColumn("Gender"),
            "university": st.column_config.TextColumn("University"),
            "department": st.column_config.TextColumn("Department"),
            "major": st.column_config.TextColumn("Major"),
            "education_level": st.column_config.TextColumn("Educational level"),
            "department": st.column_config.TextColumn("Department"),
            "group_link": st.column_config.TextColumn("Group Id", disabled=True),
            "department": st.column_config.TextColumn("Department"),
            "opt_out_token": None,
            "application_token": None,
            "registration_type": None,
            "university_country": None,
            "phone_number": st.column_config.TextColumn("Phone number"),
            "personal_profile": st.column_config.TextColumn("Personal Profile"),
            "teammate_profile": st.column_config.TextColumn("Teammate Profile"),
            "research_topic": st.column_config.TextColumn("Research Topic"),
            "previous_participation": st.column_config.TextColumn("Previous Participation"),
            "previous_award": st.column_config.TextColumn("Previous Award"),
            "project_name": st.column_config.TextColumn("Project Name"),
            "reusing_project": st.column_config.TextColumn("Reusing Project"),
            "file_uploaded": st.column_config.SelectboxColumn("File Uploaded", options=[True, False], help="Select the upload status")
        }

        cols = df.columns.tolist()
        if "team_name" in cols:
            cols.insert(1, cols.pop(cols.index("team_name")))
        if "status" in cols:
            cols.insert(2, cols.pop(cols.index("status")))
        df = df[cols]

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
            
        st.title("👥 Team Management View")

        conn = get_connection()
        try:
            query_teams = """
                SELECT
                    id, is_complete, group_name, description_existing_members,
                    expected_members, topic_introduction, team_leader_email,
                    previous_participation, previous_award, project_name, reusing_project, file_uploaded
                FROM groups
                ORDER BY id ASC
            """
            df_teams = pd.read_sql(query_teams, conn)
            
            query_members = """
                SELECT group_link, name, email, status
                FROM members
                WHERE group_link IS NOT NULL
                AND status != 'pending'
                ORDER BY CASE WHEN status = 'Leader' THEN 1 ELSE 2 END, name ASC
            """
            df_members = pd.read_sql(query_members, conn)
        finally:
            release_connection(conn)

        df_teams['Status'] = df_teams['is_complete'].map({True: "COMPLETE", False: "INCOMPLETE"})

        # Flatten Members into Team Rows
        flattened_members = []
        for idx, team in df_teams.iterrows():
            team_id = str(team['id'])
            team_mems = df_members[df_members['group_link'] == team_id]
            regulars = team_mems[team_mems['status'] != 'N member'].reset_index()
            n_members = team_mems[team_mems['status'] == 'N member'].reset_index()
            
            row_data = {}
            
            for i in range(5):
                col_prefix = f"Member {i+1}"
                if i < len(regulars):
                    row_data[f"{col_prefix} Name"] = regulars.loc[i, 'name']
                    row_data[f"{col_prefix} Email"] = regulars.loc[i, 'email']
                    row_data[f"{col_prefix} Role"] = regulars.loc[i, 'status']
                else:
                    row_data[f"{col_prefix} Name"] = ""
                    row_data[f"{col_prefix} Email"] = ""
                    row_data[f"{col_prefix} Role"] = ""
            
            for i in range(2):
                col_prefix = f"N-Member {i+1}"
                if i < len(n_members):
                    row_data[f"{col_prefix} Name"] = n_members.loc[i, 'name']
                    row_data[f"{col_prefix} Email"] = n_members.loc[i, 'email']
                    row_data[f"{col_prefix} Role"] = n_members.loc[i, 'status']
                else:
                    row_data[f"{col_prefix} Name"] = ""
                    row_data[f"{col_prefix} Email"] = ""
                    row_data[f"{col_prefix} Role"] = ""
            flattened_members.append(row_data)

        df_display = pd.concat([df_teams, pd.DataFrame(flattened_members)], axis=1)

        group_config = {
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "is_complete": None,
            "Status": st.column_config.TextColumn("Status", disabled=True),
            "group_name": st.column_config.TextColumn("Team Name", width="medium"),
            "description_existing_members": st.column_config.TextColumn("Team Profile", width="large"),
            "expected_members": st.column_config.TextColumn("Expected Teammates Profile", width="large"),
            "topic_introduction": st.column_config.TextColumn("Topic Introduction", width="large"),
            "team_leader_email": st.column_config.TextColumn("Leader Email", disabled=True),
            "previous_participation": st.column_config.TextColumn("Previous Participation"),
            "previous_award": st.column_config.TextColumn("Previous Award"),
            "project_name": st.column_config.TextColumn("Project Name"),
            "reusing_project": st.column_config.TextColumn("Reusing Project"),
            "file_uploaded": st.column_config.SelectboxColumn("File Uploaded", options=[True, False], help="Select the upload status")
        }

        member_cols_config = {}
        for i in range(1, 8):
            label = f"Member {i}" if i <= 5 else f"N-Member {i-5}"
            
            member_cols_config[f"{label} Name"] = st.column_config.TextColumn(f"{label} Name", width="medium", disabled=True)
            member_cols_config[f"{label} Email"] = st.column_config.TextColumn(f"{label} Email", width="medium", disabled=True)
            member_cols_config[f"{label} Role"] = st.column_config.TextColumn(f"{label} Role", width="medium", disabled=True)

        # Merge configs
        full_config = {**group_config, **member_cols_config}

        st.info("Showing Team metadata and confirmed members. Member columns are read-only, but they can be modified on the admin individual view.")

        edited_df = st.data_editor(
            df_display,
            column_config=full_config,
            use_container_width=True,
            height=600,
            key="group_editor",
            hide_index=True
        )

        # Saving Logic
        if st.button("💾 Save Team Metadata", type="primary"):
            valid_db_columns = df_teams.columns.tolist()
            df_to_save = edited_df[valid_db_columns]
            confirm_save(df_to_save, "groups")
   
if __name__ == "__main__":
    main()
