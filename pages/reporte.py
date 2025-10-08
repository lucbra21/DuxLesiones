import streamlit as st
import src.config as config
config.init_config()

from src.auth import init_app_state, login_view, menu, validate_login
init_app_state()
validate_login()

# Authentication gate
if not st.session_state["auth"]["is_logged_in"]:
    login_view()
    st.stop()

st.header("Reporte de :red[Lesiones]", divider=True)

menu()