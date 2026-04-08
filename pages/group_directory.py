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

def get_group_data():
    """Fetches groups and their associated members in one go."""
    conn = get_connection()
    try:
        # Fetch Groups
        groups_df = pd.read_sql("SELECT * FROM groups ORDER BY is_complete ASC, group_name ASC", conn)
        
        # Fetch Members
        members_df = pd.read_sql("""
            SELECT name, nationality, university, major, education_level, group_link 
            FROM members 
            WHERE group_link IS NOT NULL
        """, conn)
        
        return groups_df, members_df
    except Exception as e:
        st.error(f"Error fetching group data: {e}")
        return pd.DataFrame(), pd.DataFrame()
    finally:
        if conn:
            release_connection(conn)

def render_group_card(group_row, group_members):
    """Renders an individual group card with its member list."""
    with st.container(border=True):
        st.subheader(group_row['group_name'])
        st.markdown(f"**Topic:** {group_row['topic_introduction']}")
        
        # Show status badge
        if group_row['is_complete']:
            st.success("Status: Complete")
        else:
            st.warning("Status: Looking for Members")

        st.divider()
        
        # Group Details
        st.write("**About the Project:**")
        st.write(group_row['description_existing_members'])
        
        if not group_row['is_complete']:
            st.write("**Who they are looking for:**")
            st.write(group_row['expected_members'])

        if st.button("View Full Details", key=f"details_{group_row['id']}", use_container_width=True):
            st.query_params["page"] = "group_info"
            st.query_params["group_id"] = group_row['id']
            st.rerun()

def main():
    if not check_registration_access():
        st.stop()

    st.title("👥 Group Directory")
    
    groups_df, members_df = get_group_data()
    
    if groups_df.empty:
        st.info("No groups have been registered yet.")
        return

    tab1, tab2 = st.tabs(["Incomplete Groups", "Complete Groups"])

    with tab1:
        incomplete = groups_df[groups_df['is_complete'] == False]
        if incomplete.empty:
            st.write("All groups are currently full!")
        else:
            cols_per_row = 2
            for i in range(0, len(incomplete), cols_per_row):
                row_data = incomplete.iloc[i : i + cols_per_row]
                cols = st.columns(cols_per_row)
                for j, (idx, g_row) in enumerate(row_data.iterrows()):
                    with cols[j]:
                        # Filter members for this specific group
                        g_members = members_df[members_df['group_link'] == g_row['id']]
                        render_group_card(g_row, g_members)

    with tab2:
        complete = groups_df[groups_df['is_complete'] == True]
        if complete.empty:
            st.write("No groups are marked as complete yet.")
        else:
            cols_per_row = 2
            for i in range(0, len(complete), cols_per_row):
                row_data = complete.iloc[i : i + cols_per_row]
                cols = st.columns(cols_per_row)
                for j, (idx, g_row) in enumerate(row_data.iterrows()):
                    with cols[j]:
                        g_members = members_df[members_df['group_link'] == g_row['id']]
                        render_group_card(g_row, g_members)

if __name__ == "__main__":
    main()
