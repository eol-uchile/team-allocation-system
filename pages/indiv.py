import streamlit as st
import psycopg2

NATIONALITIES = ["Select...", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Côte d'Ivoire", "Cabo Verde", "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros", "Congo (Congo-Brazzaville)", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czechia (Czech Republic)", "Democratic Republic of the Congo", "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Ethiopia", "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Holy See", "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar (formerly Burma)", "Namibia", "Nauru", "Nepal", "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan", "Palau", "Panama", "Papua New Guinea", "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe", "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States of America", "Uruguay", "Uzbekistan", "Vanuatu", "Venezuela", "Vietnam", "Yemen", "Zambia", "Zimbabwe"] 
GENDERS = ["Select...", "Male", "Female"]
EDUCATION_LEVELS = ["Select...", "Undergraduate", "Graduate", "PhD", "Other"]
DATABASE_URL = ""

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
        "major": major
    }

def main():
    st.title("Individual Registration")
    st.info("Register as an individual to be matched with a group later.")

    user_data = render_individual_form()

    st.markdown("### Additional Details")
    interest_desc = st.text_area("Research Interests / Skills", 
                                placeholder="Describe what you bring to a potential group...")

    # Submission Logic
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
                conn = psycopg2.connect(DATABASE_URL)
                cur = conn.cursor()
                
                insert_query = """
                    INSERT INTO individual_register (
                        name, email, nationality, gender,
                        university, major, introductory_text
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s);
                """
                
                cur.execute(insert_query, (
                    user_data['name'],
                    user_data['email'],
                    user_data['nat'],
                    user_data['gender'],
                    user_data['university'],
                    user_data['major'],
                    interest_desc
                ))

                conn.commit()
                st.success("Your registration has been submitted successfully.")
                
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
                    conn.close()

if __name__ == "__main__":
    main()
