import ee
import streamlit as st


def initialize_gee():
    """GEE initialize — Service Account অথবা personal auth"""
    try:
        # Option 1: Service Account (deploy এর জন্য recommended)
        credentials = ee.ServiceAccountCredentials(
            email=st.secrets["GEE_SERVICE_ACCOUNT"],
            key_file="gee_auth/service_account.json",
        )
        ee.Initialize(credentials)

        # Option 2: Personal auth (local test এর জন্য)
        # ee.Initialize()

        return True
    except Exception as e:
        st.error(f"GEE connection failed: {e}")
        return False
