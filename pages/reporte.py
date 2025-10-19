import pandas as pd
import streamlit as st
import src.config as config
config.init_config()

from src.auth import init_app_state, login_view, menu, validate_login
from src.io_files import get_records_df
from src.ui_components import data_filters,player_block_dux
from src.util import get_photo, get_drive_direct_url

init_app_state()
validate_login()

# Authentication gate
if not st.session_state["auth"]["is_logged_in"]:
    login_view()
    st.stop()

st.header("Análisis :red[Individual]", divider=True)

menu()

jugadora_seleccionada, posicion = data_filters(modo=2)

st.divider()

player_block_dux(jugadora_seleccionada)

# if jugadora_seleccionada and isinstance(jugadora_seleccionada, dict):
#     nombre_completo = (jugadora_seleccionada["nombre"] + " " + jugadora_seleccionada["apellido"]).upper()
#     id_jugadora = jugadora_seleccionada["identificacion"]
#     posicion = jugadora_seleccionada["posicion"]
#     url_drive = jugadora_seleccionada["url"]
#     pais = jugadora_seleccionada["pais"]
#     records = get_records_df() 
# else:
#     st.info("Selecciona una jugadora para continuar.")
#     st.stop()

# #if id_jugadora == "X2486103X":

# col1, col2 = st.columns([1,2])

# with col1:
    
#     if pd.notna(url_drive) and url_drive and url_drive != "":
#         direct_url = get_drive_direct_url(url_drive)
#         response = get_photo(direct_url)
#         #st.text(response.headers.get("Content-Type", ""))
#         if response and response.status_code == 200 and 'image' in response.headers.get("Content-Type", ""):
#             st.image(response.content, width=250)
#         else:
#             #"https://cdn-icons-png.flaticon.com/512/5281/5281619.png"
#             st.image(f"assets/images/female.png", width=180)

# with col2:
#     st.text(f"**Jugadora:** {nombre_completo}  \n**ID:** {id_jugadora}  \n**Posición:** {posicion}")


