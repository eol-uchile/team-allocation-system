import os
import streamlit as st
from psycopg2 import pool

DATABASE_URL = os.environ.get("DATABASE_URL") or st.secrets.get("DATABASE_URL")

@st.cache_resource
def get_pool():
    return pool.SimpleConnectionPool(minconn=1, maxconn=10, dsn=DATABASE_URL)

def get_connection():
    return get_pool().getconn()

def release_connection(conn):
    get_pool().putconn(conn)
