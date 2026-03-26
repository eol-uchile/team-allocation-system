import streamlit as st
import psycopg2
import pandas as pd

DATABASE_URL = ""

def get_complete_groups():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        query = """
            SELECT 
                g.id as "Group ID", 
                g.team_leader_email as "Leader Contact", 
                g.topic_introduction as "Topic",
                COUNT(m.id) as "Member Count",
                STRING_AGG(m.nationality, ', ') as "Nationalities"
            FROM groups g
            JOIN group_members m ON g.id = CAST(m.group_id AS INTEGER)
            WHERE g.is_complete = TRUE
            GROUP BY g.id, g.team_leader_email, g.topic_introduction
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Database Error: {e}")
        return pd.DataFrame()

st.title("Complete Groups")
st.info("The following groups have met all registration and diversity requirements.")

df = get_complete_groups()

if df.empty:
    st.write("No groups have completed their registration yet.")
else:
    st.dataframe(df, hide_index=True, use_container_width=True)
