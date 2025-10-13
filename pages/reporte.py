import streamlit as st
import src.config as config
config.init_config()

from src.auth import init_app_state, login_view, menu, validate_login
from src.io_files import get_records_df, load_jugadoras, load_competiciones
init_app_state()
validate_login()

# Authentication gate
if not st.session_state["auth"]["is_logged_in"]:
    login_view()
    st.stop()

st.header("Reporte de :red[Lesiones]", divider=True)

menu()

# Lista de jugadoras predefinidas
jug_df, jug_error = load_jugadoras()
comp_df, comp_error = load_competiciones()

# Organiza el formulario en columnas
col1, col2, col3 = st.columns([2,1,1])

with col1:
    competiciones_options = comp_df.to_dict("records")
    competicion = st.selectbox(
        "Competición",
        options=competiciones_options,
        format_func=lambda x: f'{x["nombre"]} ({x["codigo"]})',
        placeholder="Seleccione una Competición",
        #index=None
    )
    
with col2:
    posicion = st.selectbox("Posición", ["PORTERA", "DEFENSA", "CENTRO", "DELANTERA"],
    placeholder="Seleccione una Posición",
    #index=None
    )
    
with col3:
    if competicion:
        codigo_competicion = competicion["codigo"]
        jug_df_filtrado = jug_df[jug_df["competicion"] == codigo_competicion]

        # Convertir el DataFrame filtrado a lista de opciones
        jugadoras_filtradas = jug_df_filtrado.to_dict("records")
    else:
        jugadoras_filtradas = jug_df.to_dict("records")

    # La nueva columna para el nombre de la jugadora
    jugadora_seleccionada = st.selectbox(
        "Jugadora",
        options=jugadoras_filtradas,
        format_func=lambda x: f'{jugadoras_filtradas.index(x) + 1} - {x["nombre"]} {x["apellido"]}',
        placeholder="Seleccione una Jugadora",
        #index=None
    )