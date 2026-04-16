import streamlit as st
import pandas as pd
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

def main():
    if not check_registration_access():
        st.stop()

    group_id = st.query_params.get("group_id")

    if not group_id:
        st.error("No group selected.")
        if st.button("← Back to Directory"):
            st.query_params["page"] = "group_directory"
            st.rerun()
        return

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT 
                group_name, 
                topic_introduction, 
                description_existing_members, 
                expected_members, 
                is_complete,
                previous_participation,
                previous_award,
                project_name,
                reusing_project
            FROM groups WHERE id = %s
        """, (group_id,))
        group = cur.fetchone()

        if not group:
            st.error("Group not found.")
            return

        cur.execute("""
            SELECT name, nationality, university, department, major, education_level, status
            FROM members 
            WHERE group_link = %s
            AND status IN ('Leader', 'Mentoring Recorder', 'Member', 'N Member')
            ORDER BY CASE 
                WHEN status = 'Leader' THEN 1 
                WHEN status = 'Mentoring Recorder' THEN 2 
                WHEN status = 'Member' THEN 3
                ELSE 4 END ASC
        """, (group_id,))
        members = cur.fetchall()
        
        members_df = pd.DataFrame(members, columns=[
            "Name", "Nationality", "University",
            "Department", "Major", "Education Level", "Role"
        ])

        # --- UI RENDERING ---
        st.title(f"Team: {group[0]}")
        
        if group[4]:
            st.success("✅ This team is currently Complete.")
        else:
            st.warning("🔍 This team is currently Recruiting Members.")
        
        st.divider()

        # Topic Introduction
        st.header("Topic Introduction")
        st.write(group[1])
        st.divider()

        # Existing Situation
        st.header("Situation of Existing Members")
        st.write(group[2])
        st.divider()

        # Expected Members
        st.header("Expected Transnational Members")
        st.write(group[3])
        st.divider()

        # Participation History
        st.header("Participation History")
        st.write(f"**Participated in 2024/2025:** {group[5]}")
        if group[5] == "Yes":
            st.write(f"**Previous Team Award:** {group[6]}")
            if group[6] == "Yes":
                st.write(f"**Previous Project Name:** {group[7]}")
            st.write(f"**Reusing/Building on past project:** {group[8]}")
        st.divider()

        # Members Table
        st.header("Current Members")
        if members_df.empty:
            st.info("No members found for this group.")
        else:
            st.dataframe(members_df, use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"Error loading group details: {e}")
    finally:
        if cur:
            cur.close()
        if conn:
            release_connection(conn)

    st.write("")
    if st.button("← Back to Directory", use_container_width=True):
        st.query_params["page"] = "group_directory"
        if "group_id" in st.query_params:
            del st.query_params["group_id"]
        st.rerun()

if __name__ == "__main__":
    main()
