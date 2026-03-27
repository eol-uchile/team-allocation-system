import streamlit as st
import psycopg2
from db import get_connection, release_connection
import os
import time

NATIONALITIES = ["Select...", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Côte d'Ivoire", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar (formerly Burma)", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"] 
GENDERS = ["Select...", "Male", "Female"]
EDUCATION_LEVELS = ["Select...", "Undergraduate", "Graduate", "PhD", "Other"]

def render_individual_form():
    st.markdown("#### Personal Information")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Full Name")
        email = st.text_input("Email Address")
        nationality = st.selectbox("Nationality", options=NATIONALITIES)
        gender = st.selectbox("Gender", options=GENDERS)
    with col2:
        university = st.text_input("University")
        ed_level = st.selectbox("Education Level", options=EDUCATION_LEVELS)
        major = st.text_input("Major")
    
    return {
        "name": name, "email": email, "nat": nationality,
        "gender": gender, "university": university,
        "major": major, "ed_level": ed_level
    }


def check_registration_access():
    """
    Password check for registration forms
    """
    if "public_authenticated" not in st.session_state:
        st.session_state.public_authenticated = False

    if st.session_state.public_authenticated:
        return True

    st.title("Registration Access")
    st.write("Please enter the password to access the registration form.")
    
    access_code = os.getenv("REGISTRATION_CODE", "user123")
    
    code_input = st.text_input("Password", type="password")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Enter"):
            if code_input == access_code:
                st.session_state.public_authenticated = True
                st.rerun()
            else:
                st.error("Invalid Password")
            
    return False

def main():
    if not check_registration_access():
        st.stop()
        
    st.title("Individual Registration")

    st.info("Register as an individual to be matched with a group later.")

    user_data = render_individual_form()

    st.markdown("### Additional Details")
    interest_desc = st.text_area("Introduction (This includes the current professional abilities, personal strengths, teamwork skills, as well as any existing academic or practical experience in poverty alleviation, and any poverty alleviation projects that have been initiated or funded.) Within 500 words.", 
                                placeholder="Describe what you bring to a potential group...")

    registration_successful = False

    if st.button("Submit Registration", type="primary", use_container_width=True):
        # Validation
        incomplete = any(
            user_data[field] == "" or user_data[field] == "Select..." 
            for field in ["name", "email", "nat", "gender"]
        )
        
        if incomplete:
            st.error("Please fill in all required fields.")
        else:
            try:
                conn = get_connection()
                cur = conn.cursor()
                
                insert_query = """
                    INSERT INTO members (
                        name, email, nationality, gender,
                        university, major, education_level, introductory_text, status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                """
                
                cur.execute(insert_query, (
                    user_data['name'], user_data['email'], user_data['nat'],
                    user_data['gender'], user_data['university'], user_data['major'],
                    user_data['ed_level'], interest_desc, ""
                ))

                conn.commit()
                registration_successful = True
                
            except psycopg2.errors.UniqueViolation:
                st.error("This email has already been registered.")
                conn.rollback()
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

    if registration_successful:
        st.success("Registration Successful!")
        st.write("Redirecting you to the home page in 5 seconds...")
        st.session_state.page = "home"
        st.query_params.clear() 
        time.sleep(5)
        st.rerun()

if __name__ == "__main__":
    main()
