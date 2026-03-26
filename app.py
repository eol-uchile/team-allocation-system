import streamlit as st

# Define the Pages
home_page = st.Page("app.py", title="Home", icon="🏠", default=True)
indiv_reg = st.Page("pages/indiv.py", title="Individual Registration", icon="👤")
group_reg = st.Page("pages/group.py", title="Group Registration", icon="👥")
view_indiv_data = st.Page("pages/indiv_dashboard.py", title="Check Individual Registrations")
complete_view = st.Page("pages/complete_groups_dashboard.py", title="Complete Groups")
incomplete_view = st.Page("pages/incomplete_groups_dashboard.py", title="Incomplete Groups")

# Initialize Navigation
pg = st.navigation([
    home_page, 
    indiv_reg, 
    group_reg, 
    view_indiv_data, 
    complete_view, 
    incomplete_view
])


if st.get_option("client.showSidebarNavigation") is False:
    pass

# Landing Page Content
def show_home():
    st.title("Welcome to the Course Registration")
    st.write("Text.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Individual Registration"):
            st.switch_page(indiv_reg)
    with col2:
        if st.button("Group Registration"):
            st.switch_page(group_reg)

if pg == home_page:
    show_home()
else:
    pg.run()
