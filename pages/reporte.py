import streamlit as st
import src.config as config
config.init_config()

from src.auth import init_app_state, login_view, menu, validate_login
from src.io_files import get_records_df
from src.ui_components import data_filters
from src.util import get_photo

init_app_state()
validate_login()

# Authentication gate
if not st.session_state["auth"]["is_logged_in"]:
    login_view()
    st.stop()

st.header("Reporte de :red[Lesiones]", divider=True)

menu()

jugadora_seleccionada, posicion = data_filters()

st.divider()


if jugadora_seleccionada and isinstance(jugadora_seleccionada, dict):
    nombre_completo = (jugadora_seleccionada["nombre"] + " " + jugadora_seleccionada["apellido"]).upper()
    id_jugadora = jugadora_seleccionada["identificacion"]
    posicion = jugadora_seleccionada["posicion"]
    records = get_records_df() 
else:
    st.info("Selecciona una jugadora para continuar.")
    st.stop()

if id_jugadora == "X2486103X":

    col1, col2 = st.columns([1,2])
    
    with col1:
        response = get_photo("https://ligaf.es/media/images/2026/img_players/144992.jpg")
        if response and response.status_code == 200 and 'image' in response.headers.get("Content-Type", ""):
            st.image(response.content, width=250)

    with col2:
        st.text(f"**Jugadora:** {nombre_completo}  \n**ID:** {id_jugadora}  \n**Posición:** {posicion}")


