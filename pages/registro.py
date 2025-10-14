import streamlit as st
import src.config as config
config.init_config()

from src.auth import init_app_state, login_view, menu, validate_login
from src.ui_components import view_registro_lesion, data_filters
init_app_state()
validate_login()

# Authentication gate
if not st.session_state["auth"]["is_logged_in"]:
    login_view()
    st.stop()

st.header("Registro de :red[Lesiones]", divider=True)

menu()

jugadora_seleccionada, posicion = data_filters()
st.divider()
view_registro_lesion(jugadora_seleccionada=jugadora_seleccionada, posicion=posicion)