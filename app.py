import streamlit as st
import pandas as pd

import src.config as config
config.init_config()

from src.auth import init_app_state, login_view, menu, validate_login
from src.io_files import get_records_plus_players_df
from src.util import clean_df
from src.ui_components import main_metrics

init_app_state()
validate_login()

# Authentication gate
if not st.session_state["auth"]["is_logged_in"]:
    #st.text("🔐 Por favor, inicie sesión para acceder a esta página.")
    login_view()
    st.stop()

st.header("Resumen de :red[Lesiones] (1er Equipo)", divider=True)

menu()

#competicion, posicion, tipo_lesion, fechas, records = data_filters_advanced()
records = get_records_plus_players_df(plantel="1FF")  # Carga y cachea los datos
resumen = main_metrics(records)

st.subheader("Ultimas :red[lesiones]")
df_filtrado = clean_df(resumen)
st.dataframe(df_filtrado)