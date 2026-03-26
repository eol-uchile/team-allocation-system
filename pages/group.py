import streamlit as st
import psycopg2
from psycopg2.extras import execute_values
from db import get_connection, release_connection


NATIONALITIES = ["Select...", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Côte d'Ivoire", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar (formerly Burma)", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"] 
GENDERS = ["Select...", "Male", "Female"]
EDUCATION_LEVELS = ["Select...", "Undergraduate", "Graduate", "PhD", "Other"]
#TODO: use as a streamlit variable

def render_member_form(label, key_prefix):
    """Helper function to render a member input block"""
    st.markdown(f"#### {label}")
    
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name", key=f"{key_prefix}_name")
        email = st.text_input("Email Address", key=f"{key_prefix}_email")
        nationality = st.selectbox("Nationality", options=NATIONALITIES, key=f"{key_prefix}_nat")
        gender = st.selectbox("Gender", options=GENDERS, key=f"{key_prefix}_gender")
    
    with col2:
        university = st.text_input("University", key=f"{key_prefix}_uni")
        ed_level = st.selectbox("Education Level", options=EDUCATION_LEVELS, key=f"{key_prefix}_ed")
        major = st.text_input("Major", key=f"{key_prefix}_major")

    st.divider()
    return {
        "name": name, 
        "email": email, 
        "nat": nationality, 
        "gender": gender,
        "university": university,
        "education_level": ed_level,
        "major": major
    }

def main():
    st.title("Group Registration")
    st.info("Groups must have between 2 and 5 members (including the leader).")

    if 'extra_members' not in st.session_state:
        st.session_state.extra_members = 1

    leader_data = render_member_form("Group Leader", "leader")
    member_data_list = []
    for i in range(st.session_state.extra_members):
        data = render_member_form(f"Member {i+1}", f"member_{i}")
        member_data_list.append(data)

    col_add, col_rem, _ = st.columns([1, 1, 2])
    
    with col_add:
        if st.button("➕ Add Member") and st.session_state.extra_members < 4:
            st.session_state.extra_members += 1
            st.rerun()

    with col_rem:
        if st.button("➖ Remove Member") and st.session_state.extra_members > 1:
            st.session_state.extra_members -= 1
            st.rerun()

    st.markdown("### Group Details")
    desc_1 = """Situation of Existing Team Members
        (This includes the current professional abilities, personal strengths, teamwork skills, as well as any
        existing academic or practical experience in poverty alleviation, and any poverty alleviation projects that
        have been initiated or funded.)
        Within 500 words."""
    desc_2 = """Introduction of Expected Transnational Team Members
        (This includes the professional abilities, personal strengths, teamwork skills, as well as any existing
        academic or practical experience in poverty alleviation, and any poverty alleviation projects that have
        been initiated or funded, that the team hopes the transnational members will have.)
        Within 500 words.
        """
    desc_3 =  """Topic Introduction
        (This includes the understanding, interest, and research foundation related to the selected topic.)
        Within 1000 words.
        """
    description_existing_members = st.text_area(desc_1, placeholder="")
    expected_members = st.text_area(desc_2, placeholder="")
    topic_introduction = st.text_area(desc_3, placeholder="")

    st.write("")

    if st.button("Submit Group Registration", type="primary", use_container_width=True):
        all_members = [leader_data] + member_data_list
        
        incomplete = any(
            m['name'] == "" or m['email'] == "" or m['nat'] == "Select..." 
            for m in all_members
        )
        
        if incomplete:
            st.error("Please fill the fields for all members.")
        else:
            try:
                conn = get_connection()
                
                cur = conn.cursor()

                unique_nations = set(m['nat'] for m in all_members)
                is_complete = len(all_members) >= 2 and len(unique_nations) >= 2

                group_query = """
                    INSERT INTO groups (
                        team_leader_email, is_complete, 
                        description_existing_members, expected_members, topic_introduction
                    )
                    VALUES (%s, %s, %s, %s, %s) RETURNING id;
                """
                cur.execute(group_query, (
                    leader_data['email'], is_complete, description_existing_members, expected_members, topic_introduction
                ))
                group_id = cur.fetchone()[0]

                member_rows = [
                    (
                        group_id, m['name'], m['gender'], m['nat'], 
                        m['university'], m['education_level'], m['major'], m['email']
                    )
                    for m in all_members
                ]
                
                member_query = """
                    INSERT INTO group_members (
                        group_id, name, gender, nationality, 
                        university, education_level, major, email
                    )
                    VALUES %s
                """
                execute_values(cur, member_query, member_rows)

                conn.commit()
                st.success(f"Successfully registered Group #{group_id}!")

            except Exception as e:
                st.error(f"Postgres Error: {e}")
                if conn: 
                    conn.rollback()
            finally:
                if cur:
                    cur.close()
                if conn:
                    conn.rollback()
                    release_connection(conn)

if __name__ == "__main__":
    main()
