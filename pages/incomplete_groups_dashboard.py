import streamlit as st
import psycopg2
import pandas as pd

DATABASE_URL = ""

def get_incomplete_groups():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        query = """
            SELECT 
                g.id as "Group ID", 
                g.topic_introduction as "Project Topic",
                COUNT(m.id) as "Current Members",
                STRING_AGG(m.nationality, ', ') as "Current Nationalities",
                g.expected_members as "Looking For"
            FROM groups g
            LEFT JOIN group_members m ON g.id = m.group_id::integer
            WHERE g.is_complete = FALSE
            GROUP BY g.id, g.topic_introduction, g.expected_members
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Database Error: {e}")
        return pd.DataFrame()

st.title("Incomplete Groups")
st.markdown("These groups are currently forming.")

df = get_incomplete_groups()

if df.empty:
    st.success("All registered groups are currently complete!")
else:
    st.dataframe(df, hide_index=True, use_container_width=True)
