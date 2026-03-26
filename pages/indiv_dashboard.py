import streamlit as st
import psycopg2
import pandas as pd
from db import get_connection, release_connection

def get_individual_data():
    """Fetches all registered students from the DB"""
    try:
        conn = get_connection()
        query = """
            SELECT name, nationality, major, university, gender, introductory_text 
            FROM individual_register
        """
        df = pd.read_sql(query, conn)
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()
    finally:
        if conn:
            conn.rollback()
            release_connection(conn)

def main():
    st.title("👤 Individual Member Directory")
    st.markdown("""
    Groups looking for members can browse the list below.
    """)

    # Fetch Data
    df = get_individual_data()

    if df.empty:
        st.info("No individuals have registered yet.")
    else:
        st.dataframe(
            df,
            column_config={
                "name": "Full Name",
                "nationality": "Nationality",
                "major": "Major",
                "university": "University",
                "gender": "Gender",
                "introductory_text": "Introductory Text",
                "education_level": "Level",
                "interest_description": st.column_config.TextColumn(
                    "About / Skills", width="large"
                )
            },
            hide_index=True,
            use_container_width=True
        )


if __name__ == "__main__":
    main()
