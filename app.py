import streamlit as st
from pages import indiv, group, manager

st.set_page_config(layout="centered", initial_sidebar_state="collapsed")

def show_home():
    st.title("Poverty Alleviation Challenge Registration")
    st.set_page_config(page_title="Poverty Alleviation Challenge Registration", page_icon="📋")
    st.write("Please choose your registration type:")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Individual Registration", use_container_width=True):
            st.query_params["page"] = "indiv"
            st.rerun()
    with col2:
        if st.button("Group Registration", use_container_width=True):
            st.query_params["page"] = "group"
            st.rerun()

current_page = st.query_params.get("page", "home")

if current_page == "home":
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

elif current_page == "manager":
    manager.main()
