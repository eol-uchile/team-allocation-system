import streamlit as st
from pages import accept_member, indiv, group, manager, optout, join_group, indiv_directory, group_directory, accept_member, group_info

st.set_page_config(page_title="2026 Poverty Alleviation Challenge Registration", page_icon="📋", layout="centered", initial_sidebar_state="collapsed")

def show_home():
    st.title("2026 Poverty Alleviation Challenge Registration")
    
    # Registration Section
    st.markdown("### 📝 Registration & Groups")
    st.write("Choose how you would like to participate:")
    reg_col1, reg_col2, reg_col3 = st.columns(3)
    
    with reg_col1:
        if st.button("Individual Registration", use_container_width=True):
            st.query_params["page"] = "indiv"
            st.rerun()
            
    with reg_col2:
        if st.button("Group Registration", use_container_width=True):
            st.query_params["page"] = "group"
            st.rerun()
            
    with reg_col3:
        if st.button("Join a Group", use_container_width=True):
            st.query_params["page"] = "join_group"
            st.rerun()

    st.divider()

    # Directories Section
    st.markdown("### 🔍 Directories")
    st.write("View registered participants and existing teams:")
    dir_col1, dir_col2 = st.columns(2)
    
    with dir_col1:
        if st.button("Individual Directory", use_container_width=True):
            st.query_params["page"] = "indiv_directory"
            st.rerun()
            
    with dir_col2:
        if st.button("Group Directory", use_container_width=True):
            st.query_params["page"] = "group_directory"
            st.rerun()

current_page = st.query_params.get("page", "home")

if current_page == "optout":
    optout.main()

elif current_page == "home":
    show_home()

elif current_page == "indiv":
    if st.button("← Back to Home"):
        st.query_params.clear()
        st.rerun()
    indiv.main()

elif current_page == "group":
    if st.button("← Back to Home"):
        st.query_params.clear()
        if 'extra_members' in st.session_state:
            del st.session_state.extra_members
        st.rerun()
    group.main()

elif current_page == "join_group":
    if st.button("← Back to Home"):
        st.query_params.clear()
        st.rerun()
    join_group.main()

elif current_page == "indiv_directory":
    if st.button("← Back to Home"):
        st.query_params.clear()
        st.rerun()
    indiv_directory.main()

elif current_page == "group_directory":
    if st.button("← Back to Home"):
        st.query_params.clear()
        st.rerun()
    group_directory.main()

elif current_page == "accept_member":
    accept_member.main()

elif current_page == "group_info":
    group_info.main()

elif current_page == "manager":
    manager.main()
