import streamlit as st
import psycopg2
from db import get_connection, release_connection
import os
import time
import secrets
from utils import send_email

NATIONALITIES = ["Select...", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Côte d'Ivoire", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar (formerly Burma)", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"] 
GENDERS = ["Select...", "Male", "Female", "Confidential"]
EDUCATION_LEVELS = ["Select...", "Undergraduate", "Master", "PhD"]
FORMS_PASSWORD = st.secrets["FORMS_PASSWORD"]
DOMAIN = os.getenv("DOMAIN", "localhost:8501")

UNIVERSITY_TO_COUNTRY = {
    "Select...": None,
    "Tsinghua University (China)": "China",
    "Federal University of Rio de Janeiro (Brazil)": "Brazil",
    "São Paulo School of Business Administration of Fundação Getulio Vargas (FGV EAESP) (Brazil)": "Brazil",
    "Universidad de Chile (Chile)": "Chile",
    "Pontificia Universidad Católica de Chile (Chile)": "Chile",
    "Pontificia Universidad Católica del Perú (Peru)": "Peru",
    "University of the Pacific (Peru)": "Peru",
    "Other": ""
}

with open("./templates/group_template.html", "r") as f:
    GROUP_TEMPLATE_HTML = f.read()

with open("./templates/leader_template.html", "r") as f:
    LEADER_TEMPLATE_HTML = f.read()

st.set_page_config(page_title="Group Registration", page_icon="📋", layout="wide")

def lookup_member(key_prefix):
    email = st.session_state[f"{key_prefix}_email"].strip()
    if not email:
        return
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT name, nationality, gender, university, education_level, major, group_link, department FROM members WHERE email = %s", (email,))
        res = cur.fetchone()
        if res:
            st.session_state[f"{key_prefix}_name"] = res[0]
            st.session_state[f"{key_prefix}_nat"] = res[1]
            st.session_state[f"{key_prefix}_gender"] = res[2]
            # Handle other university logic
            db_uni = res[3]
            if db_uni in UNIVERSITY_TO_COUNTRY:
                st.session_state[f"{key_prefix}_uni"] = db_uni
            else:
                st.session_state[f"{key_prefix}_uni"] = "Other"
                st.session_state[f"{key_prefix}_uni_custom"] = db_uni
            st.session_state[f"{key_prefix}_ed"] = res[4]
            st.session_state[f"{key_prefix}_major"] = res[5]
            st.session_state[f"{key_prefix}_dept"] = res[7]
            st.session_state[f"{key_prefix}_locked"] = True
    finally:
        if conn: release_connection(conn)

def render_member_form(label, key_prefix, show_role_toggle=False, is_leader=False):
    is_locked = st.session_state.get(f"{key_prefix}_locked", False)
    st.markdown(f"#### {label}")
    col1, col2 = st.columns(2)
    with col1:
        email = st.text_input("Email (Please use the education email address of your institution)", key=f"{key_prefix}_email", on_change=lookup_member, args=(key_prefix,))
        name = st.text_input("Full Name", key=f"{key_prefix}_name", disabled=is_locked)
        nat = st.selectbox("Nationality", options=NATIONALITIES, key=f"{key_prefix}_nat", disabled=is_locked)
        gender = st.selectbox("Gender", options=GENDERS, key=f"{key_prefix}_gender", disabled=is_locked)
        phone = st.text_input("Phone (Optional)", key=f"{key_prefix}_phone") if is_leader else None
    with col2:
        selected_uni = st.selectbox(
            "Current University", 
            options=list(UNIVERSITY_TO_COUNTRY.keys()), 
            key=f"{key_prefix}_uni", 
            disabled=is_locked
        )
        uni = selected_uni
        if selected_uni == "Other":
            uni = st.text_input(
                "Add your University Name", 
                key=f"{key_prefix}_uni_custom", 
                disabled=is_locked
            )
        dept = st.text_input("Department", key=f"{key_prefix}_dept", disabled=is_locked)
        major = st.text_input("Major", key=f"{key_prefix}_major", disabled=is_locked)
        ed = st.selectbox("Education Level", options=EDUCATION_LEVELS, key=f"{key_prefix}_ed", disabled=is_locked)
        is_recorder = st.checkbox("Mentoring Recorder?", key=f"{key_prefix}_recorder") if show_role_toggle else False
    st.divider()
    return {"name": name, "email": email, "nat": nat, "gender": gender, "university": uni, "department": dept, "education_level": ed, "major": major, "is_recorder": is_recorder, "phone": phone}


def check_registration_access():
    """
    Password check for registration forms
    """
    if "public_authenticated" not in st.session_state:
        st.session_state.public_authenticated = False

    if st.session_state.public_authenticated:
        return True
    st.set_page_config(page_title="2026 Poverty Alleviation Challenge Registration", page_icon="📋")
    st.title("Registration Access")
    st.write("Please enter the password to access the registration form.")
        
    code_input = st.text_input("Password", type="password")
    
    col1, col2 = st.columns([1, 4])
    with col1:
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

    st.set_page_config(page_title="Group Registration - 2026 Poverty Alleviation Challenge Registration", page_icon="📋")

    st.title("Group Registration")

    st.info("Groups reach full capacity at **5 members** (including the leader). We strongly encourage forming **international teams**.")
    if 'extra_members' not in st.session_state:
        st.session_state.extra_members = 1
    if "n_members" not in st.session_state: 
        st.session_state.n_members = 0

    leader_data = render_member_form("Group Leader", "leader", is_leader=True)
    member_container = st.container()
    member_data_list = []
    with member_container:
        for i in range(st.session_state.extra_members):
            data = render_member_form(f"Member {i+1}", f"member_{i}", show_role_toggle=True)
            member_data_list.append(data)

    col_a, col_b, _ = st.columns([1, 1, 2])
    with col_a: 
        if st.button("➕ Add Member") and st.session_state.extra_members < 4:
            st.session_state.extra_members += 1
            st.rerun()
    with col_b:
        if st.button("➖ Remove Member") and st.session_state.extra_members > 1:
            st.session_state.extra_members -= 1
            st.rerun()

    st.divider()

    # N member section
    include_n = st.checkbox("Include Optional 'N' Members?", value=st.session_state.n_members > 0)
    n_member_data_list = []
    if include_n:
        if st.session_state.n_members == 0: st.session_state.n_members = 1
        n_container = st.container()
        with n_container:
            for i in range(st.session_state.n_members):
                n_data = render_member_form(f"N Member {i+1}", f"n_member_{i}", show_role_toggle=False)
                n_member_data_list.append(n_data)
        
        col_na, col_nb, _ = st.columns([1.2, 1.2, 1.6])
        with col_na:
            if st.button("➕ Add N Member") and st.session_state.n_members < 2:
                st.session_state.n_members += 1
                st.rerun()
        with col_nb:
            if st.button("➖ Remove N Member") and st.session_state.n_members > 0:
                st.session_state.n_members -= 1
                st.rerun()

    # Participation History Section
    st.markdown("### Participation History")
    prev_participation = st.radio(
        "Any members participated in 2024/2025?", 
        options=["No", "Yes"], 
        horizontal=True, 
        key="hist_part_group"
    )

    hist_disabled = (prev_participation == "No")
    
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        prev_award = st.selectbox("Previous Team Award?", options=["No", "Yes"], key="hist_award_group", disabled=hist_disabled)
        project_name = st.text_input("Project Name", key="hist_proj_name_group", disabled=hist_disabled)
        
    with col_h2:
        reusing_project = st.selectbox("Reusing/Building on past project for 2026?", options=["No", "Yes"], key="hist_reuse_group", disabled=hist_disabled)

    st.divider()

    st.markdown("### Group Details")
    group_name = st.text_input("Choose a team name", placeholder="")
    desc_1 = """Team Profile & Experience [Required] (Max 500 words): Describe current members' skills, strengths, and poverty alleviation experience/awards."""
    desc_2 = """Target International Teammate Profile [Required] (Max 500 words): Specify skills/experience you hope international members possess."""
    desc_3 =  """Topic Introduction [Required] (Max 1000 words): Describe the team’s understanding of the topic and research foundations."""
    description_existing_members = st.text_area(desc_1, placeholder="")
    expected_members = st.text_area(desc_2, placeholder="")
    topic_introduction = st.text_area(desc_3, placeholder="")

    registration_successful = False

    if st.button("Submit Group Registration", type="primary", use_container_width=True):
        all_provided_members = [leader_data] + member_data_list + n_member_data_list
        all_emails = [m['email'].strip() for m in all_provided_members if m['email'].strip()]

        required_members = [leader_data] + member_data_list
        req_incomplete = any(
            m['name'].strip() == "" or m['email'].strip() == "" or m['nat'] == "Select..." or
            m['university'].strip() == "" or m['university'] == "Other" or
            m['department'].strip() == "" or m['major'].strip() == "" or
            m['education_level'] == "Select..." for m in required_members
        )
        
        n_incomplete = any(
            m['nat'] == "Select..." or
            m['university'].strip() == "" or m['university'] == "Other" or m['department'].strip() == "" or
            m['major'].strip() == "" for m in n_member_data_list
        )

        group_fields_incomplete = any(f.strip() == "" for f in [group_name, description_existing_members, expected_members, topic_introduction])
        hist_incomplete = (prev_participation == "Yes" and project_name.strip() == "")
        has_recorder = any(m.get('is_recorder', False) for m in member_data_list)

        if req_incomplete or n_incomplete or group_fields_incomplete or hist_incomplete:
            st.error("Please fill all required fields.")
        elif not has_recorder:
            st.error("At least one member (other than the leader) must be designated as a Mentoring Recorder.")
        else:
            conn = None
            cur = None
            try:
                conn = get_connection()
                cur = conn.cursor()

                cur.execute("SELECT email FROM members WHERE email IN %s AND group_link IS NOT NULL", (tuple(all_emails),))
                already_taken = cur.fetchall()

                if already_taken:
                    taken_emails = ", ".join([res[0] for res in already_taken])
                    st.error(f"Registration stopped. Members already assigned: {taken_emails}")
                else:
                    core_team_count = 1 + len(member_data_list)
                    is_complete = (core_team_count == 5)

                    cur.execute("""
                        INSERT INTO groups (
                            team_leader_email, is_complete, description_existing_members, 
                            expected_members, group_name, topic_introduction,
                            previous_participation, previous_award, project_name, reusing_project
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
                    """, (
                        leader_data['email'], is_complete, description_existing_members, 
                        expected_members, group_name, topic_introduction,
                        prev_participation, prev_award, project_name, reusing_project
                    ))
                    group_id = cur.fetchone()[0]

                    # Leader
                    leader_uni_country = UNIVERSITY_TO_COUNTRY.get(leader_data['university'], "")
                    cur.execute("""
                        INSERT INTO members (group_link, name, gender, nationality, university, university_country, department, education_level, major, email, status, phone_number)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'Leader', %s)
                        ON CONFLICT (email) DO UPDATE SET group_link = EXCLUDED.group_link, status = EXCLUDED.status, phone_number = EXCLUDED.phone_number;
                    """, (group_id, leader_data['name'], leader_data['gender'], leader_data['nat'], leader_data['university'], leader_uni_country, leader_data['department'], leader_data['education_level'], leader_data['major'], leader_data['email'], leader_data['phone']))

                    # Regular Members
                    for m in member_data_list:
                        token = secrets.token_urlsafe(16)
                        m['token'] = token
                        status = 'Mentoring Recorder' if m['is_recorder'] else 'Member'
                        member_uni_country = UNIVERSITY_TO_COUNTRY.get(m['university'], "")
                        cur.execute("""
                            INSERT INTO members (group_link, name, gender, nationality, university, university_country, department, education_level, major, email, opt_out_token, status, registration_type)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'group_added')
                            ON CONFLICT (email) DO UPDATE SET group_link = EXCLUDED.group_link, status = EXCLUDED.status, opt_out_token = EXCLUDED.opt_out_token;
                        """, (group_id, m['name'], m['gender'], m['nat'], m['university'], member_uni_country, m['department'], m['education_level'], m['major'], m['email'], token, status))

                    # N Members
                    for m in n_member_data_list:
                        n_member_uni_country = UNIVERSITY_TO_COUNTRY.get(m['university'], "")
                        cur.execute("""
                            INSERT INTO members (group_link, name, gender, nationality, university, university_country, department, education_level, major, email, status, registration_type)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'N Member', 'group_added')
                            ON CONFLICT (email) DO UPDATE SET group_link = EXCLUDED.group_link, status = EXCLUDED.status;
                        """, (group_id, m['name'], m['gender'], m['nat'], m['university'], n_member_uni_country, m['department'], m['education_level'], m['major'], m['email']))

                with st.spinner(text="Registering group and sending emails...", show_time=False, width="content"):
                    conn.commit()
                    # Handle email logic
                    # Send Email to Leader
                    leader_body = LEADER_TEMPLATE_HTML.format(group_name=group_name)
                    send_email(leader_data['email'], f"Group Registered: {group_name}", leader_body)

                    # Send Email to Members
                    for m in member_data_list:
                        opt_out_link = f"http://{DOMAIN}/?page=optout&token={m['token']}"
                        
                        member_body = GROUP_TEMPLATE_HTML.format(
                            name=m['name'],
                            group_name=group_name,
                            opt_out_link=opt_out_link
                        )
                        send_email(m['email'], f"Added to group: {group_name}", member_body)
                registration_successful = True

            except psycopg2.errors.UniqueViolation:
                st.warning(f"The group name '{group_name}' is already taken.")
            except Exception as e:
                st.error(f"Error: {e}")
            finally:
                if cur: cur.close()
                if conn: release_connection(conn)

    if registration_successful:
        st.success("Group Registration Successful!")
        time.sleep(3)
        st.query_params.clear() 
        st.session_state.page = "home"
        st.rerun()

if __name__ == "__main__":
    main()
