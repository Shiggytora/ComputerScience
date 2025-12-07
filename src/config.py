import os
from dotenv import load_dotenv
import streamlit as st


# Returns a secret value. Works locally via .env and also online via Streamlit Secrets.

# 1. Streamlit Secrets
def get_secret(key: str):
    if key in st.secrets:
        return st.secrets[key]
    
    load_dotenv()
    return os.getenv(key)