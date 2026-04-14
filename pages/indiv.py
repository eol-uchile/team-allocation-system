import streamlit as st
import psycopg2
from db import get_connection, release_connection
import time
from utils import send_email

NATIONALITIES = ["Select...", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Côte d'Ivoire", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar (formerly Burma)", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"] 
GENDERS = ["Select...", "Male", "Female", "Confidential"]
EDUCATION_LEVELS = ["Select...", "Undergraduate", "Master", "PhD"]
FORMS_PASSWORD = st.secrets["FORMS_PASSWORD"]

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

with open("./templates/indiv_template.html", "r") as f:
    INDIV_HTML_TEMPLATE = f.read()

st.set_page_config(page_title="Individual Registration - Poverty Alleviation", page_icon="📋", layout="wide")


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

def render_individual_form():
    st.markdown("#### Personal Information")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name", key="indiv_name")
        email = st.text_input("Email Address (Please use the education email address of your institution)", key="indiv_email")
        nationality = st.selectbox("Nationality", options=NATIONALITIES, key="indiv_nat")
        gender = st.selectbox("Gender", options=GENDERS, key="indiv_gender")
        phone = st.text_input("Phone Number (Optional)", key="indiv_phone")
    with col2:
        selected_existing_uni = st.selectbox("Current University/Cooperating Institution", options=list(UNIVERSITY_TO_COUNTRY.keys()), key="indiv_uni")
        # Logic for other universities
        university = selected_existing_uni
        if selected_existing_uni == "Other":
            university = st.text_input("Add your University/Cooperating Institution Name", key="indiv_uni_custom")
        department = st.text_input("Department", key="indiv_dept")
        major = st.text_input("Major", key="indiv_major")
        ed_level = st.selectbox("Education Level", options=EDUCATION_LEVELS, key="indiv_ed")
    
    return {
        "name": name, "email": email, "nat": nationality,
        "gender": gender, "university": university,
        "dept": department, "major": major, "ed_level": ed_level, "phone": phone
    }

def main():
    if not check_registration_access():
        st.stop()

    st.title("Individual Registration")
    st.info("Register as an individual to be matched with a group later.")

    user_data = render_individual_form()

    st.divider()
    
    st.markdown("### Participation History")
    prev_participation = st.radio(
        "Previous Participation (2024/2025)?", 
        options=["No", "Yes"], 
        horizontal=True, 
        key="hist_part"
    )

    hist_disabled = (prev_participation == "No")
    
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        prev_award = st.selectbox("Previous Award?", options=["No", "Yes"], key="hist_award", disabled=hist_disabled)
        project_name = st.text_input("Project Name", key="hist_proj_name", disabled=hist_disabled)        
    with col_h2:
        reusing_project = st.selectbox("Reusing project for 2026?", options=["No", "Yes"], key="hist_reuse", disabled=hist_disabled)

    st.divider()
    st.markdown("### Profile Details")
    personal_profile = st.text_area("Personal Profile & Experience [Required] (Max 500 words): Describe your professional skills, strengths, teamwork, and poverty alleviation experience/awards.", key="prof_pers", height=150)
    teammate_profile = st.text_area("Target Transnational Teammate Profile [Required] (Max 500 words): Describe the qualities/backgrounds you seek in transnational partners.", key="prof_team", height=150)
    research_topic = st.text_area("Interested Research Topic / Direction [Required] (Max 1000 words): Introduce your topic of interest, key issues, and any initial ideas.", key="prof_res", height=200)

    if st.button("Submit Registration", type="primary", use_container_width=True):
        incomplete = any([
            user_data["name"].strip() == "",
            user_data["email"].strip() == "",
            user_data["university"] == "Select..." or user_data["university"].strip() == "",
            user_data["dept"].strip() == "",
            user_data["major"].strip() == "",
            user_data["nat"] == "Select...",
            user_data["gender"] == "Select...",
            user_data["ed_level"] == "Select...",
            personal_profile.strip() == "",
            teammate_profile.strip() == "",
            research_topic.strip() == "",
            (prev_participation == "Yes" and project_name.strip() == "")
        ])
        
        if incomplete:
            st.error("Please fill in all required fields.")
        else:
            try:
                uni_country = UNIVERSITY_TO_COUNTRY.get(user_data["university"], "")

                conn = get_connection()
                cur = conn.cursor()
                
                cur.execute("""
                    INSERT INTO members (
                        name, email, nationality, gender, university, university_country, 
                        department, major, education_level, personal_profile, teammate_profile, 
                        research_topic, phone_number, status, registration_type,
                        previous_participation, previous_award, project_name, reusing_project
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, (
                    user_data['name'], user_data['email'], user_data['nat'], user_data['gender'],
                    user_data['university'], uni_country, user_data['dept'],
                    user_data['major'], user_data['ed_level'], personal_profile,
                    teammate_profile, research_topic, user_data['phone'], "", "individual",
                    prev_participation, prev_award, project_name, reusing_project
                ))
                with st.spinner():
                    conn.commit()
                    # Handle email logic
                    html_content = INDIV_HTML_TEMPLATE.format(name=user_data['name'])
                    send_email(user_data['email'], "Registration Confirmed!", html_content)
                    st.success("Registration Successful! Redirecting...")
                    time.sleep(5)
                    st.query_params.clear() 
                    st.rerun()
                
            except psycopg2.errors.UniqueViolation:
                st.error("This email has already been registered.")
            except Exception as e:
                st.error(f"Error: {e}")
            finally:
                if cur:
                    cur.close()
                if conn:
                    release_connection(conn)

if __name__ == "__main__":
    main()
