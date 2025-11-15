import streamlit as st
from src.i18n.i18n import t
import src.config as config
config.init_config()

from src.auth_system.auth_core import init_app_state, validate_login
from src.auth_system.auth_ui import login_view, menu

from src.util import clean_df
from src.ui_components import selection_header, main_metrics
from src.reports.ui_individual import (grafico_zonas_lesionadas, grafico_tipo_mecanismo, grafico_evolucion_lesiones, 
                      grafico_tratamientos, grafico_dias_baja, grafico_recidivas, player_block_dux)

init_app_state()
validate_login()

# Authentication gate
if not st.session_state["auth"]["is_logged_in"]:
    login_view()
    st.stop()
menu()

st.header(t("Análisis :red[individual]"), divider=True)

jugadora_seleccionada, posicion, records = selection_header(modo=2)

st.divider()

#st.dataframe(jugadora_seleccionada)
player_block_dux(jugadora_seleccionada)
resumen = main_metrics(records, modo="reporte")

#st.dataframe(records)

tab1, tab2 = st.tabs([t("Graficos"), t("Registros")])

with tab1:
    col1, col2 = st.columns([1,1])
    with col1:
        fig = grafico_evolucion_lesiones(records)
        if fig: st.plotly_chart(fig)

        fig = grafico_tipo_mecanismo(records)
        if fig: st.plotly_chart(fig)

        fig = grafico_dias_baja(records)
        if fig: st.plotly_chart(fig)

    with col2:
        fig = grafico_zonas_lesionadas(records)
        if fig: st.plotly_chart(fig)

        fig = grafico_tratamientos(records)
        if fig: st.plotly_chart(fig)

        fig = grafico_recidivas(records)
        if fig: st.plotly_chart(fig)

with tab2:
    records_clean = clean_df(records)
    st.dataframe(records_clean)