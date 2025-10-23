# app.py - DIAGNOSTIC VERSION
import streamlit as st
import pandas as pd
import sqlite3

# Page config
st.set_page_config(
    page_title="WUSA Schedule Reports",
    page_icon="⚾",
    layout="wide"
)

# Load data (cached so it's fast)
@st.cache_data
def load_games():
    conn = sqlite3.connect('wusa_schedule.db')
    df = pd.read_sql("SELECT * FROM games", conn)
    conn.close()
    return df

try:
    df = load_games()
    
    st.title("🔍 Column Names Diagnostic")
    st.write("### Your actual column names are:")
    st.write(list(df.columns))
    
    st.write("### First few rows of data:")
    st.dataframe(df.head())
    
    st.write("### Data types:")
    st.write(df.dtypes)
    
except Exception as e:
    st.error(f"Error loading data: {e}")