import pandas as pd
import streamlit as st
import src.config as config
config.init_config()

from src.auth_system.auth_core import init_app_state, validate_login
from src.auth_system.auth_ui import login_view, menu
from src.db_login import load_all_users_from_db

init_app_state()
validate_login()

# Authentication gate
if not st.session_state["auth"]["is_logged_in"]:
    login_view()
    st.stop()

if st.session_state["auth"]["rol"].lower() != "developer":
    st.switch_page("app.py")

st.header("Area de:red[Desarrollo]", divider=True)

menu()

usuarios, simulador, bd = st.tabs(["USUARIOS", "SIMULADOR", "BASE DE DATOS"])
with usuarios:
    st.text("Gestión de usuarios del sistema")
    df = load_all_users_from_db()
    st.dataframe(df)

with simulador:
    st.text("Generar lesiones aleatorias para pruebas")
with bd:
    if st.button(":material/update: Recargar datos"):
        st.cache_data.clear()
        st.rerun()
