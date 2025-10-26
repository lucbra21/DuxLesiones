import streamlit as st
import src.config as config
config.init_config()

from src.auth import init_app_state, login_view, menu, validate_login

init_app_state()
validate_login()

from src.ui_components import data_filters
from src.records_ui import view_registro_lesion

# Authentication gate
if not st.session_state["auth"]["is_logged_in"]:
    login_view()
    st.stop()

st.header("Registro de :red[Lesiones]", divider=True)

menu()

jugadora_seleccionada, posicion = data_filters()

st.divider()

if jugadora_seleccionada and isinstance(jugadora_seleccionada, dict):
    nombre_completo = (jugadora_seleccionada["nombre"] + " " + jugadora_seleccionada["apellido"]).upper()
    id_jugadora = jugadora_seleccionada["identificacion"]
    posicion = jugadora_seleccionada["posicion"]

    jugadora_info = {
    "id_jugadora": jugadora_seleccionada.get("identificacion"),
    "nombre_completo": f"{jugadora_seleccionada.get('nombre', '')} {jugadora_seleccionada.get('apellido', '')}".upper().strip(),
    "posicion": jugadora_seleccionada.get("posicion"),
    "id_lesion": None}

else:
    st.info("Selecciona una jugadora para continuar.")
    st.stop()

view_registro_lesion(jugadora_info=jugadora_info)