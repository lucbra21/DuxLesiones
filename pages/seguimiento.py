import pandas as pd
import streamlit as st
import src.config as config
config.init_config()

from src.io_files import get_records_df, load_jugadoras, upsert_jsonl, load_competiciones
from src.ui_components import view_registro_lesion
from src.auth import init_app_state, login_view, menu, validate_login
from src.util import clean_df

init_app_state()
validate_login()

# Authentication gate
if not st.session_state["auth"]["is_logged_in"]:
    login_view()
    st.stop()

st.header("Seguimiento de :red[Lesiones]", divider="red")

menu()

records = get_records_df()  # Carga y cachea los datos

if records.empty:    
    st.warning("No hay datos de lesiones disponibles.")
    st.stop()   
    
#records["fecha_alta_diagnostico"] = pd.to_datetime(records["fecha_alta_diagnostico"], errors="coerce")

jug_df, jug_error = load_jugadoras()
comp_df, comp_error = load_competiciones()

col1, col2, col3 = st.columns([2,2,1])

with col1:
    competiciones_options = comp_df.to_dict("records")
    competicion = st.selectbox(
        "Competición",
        options=competiciones_options,
        format_func=lambda x: f'{x["nombre"]} ({x["codigo"]})',
        placeholder="Seleccione una Competición",
        index=3
    )
    #jugadoras = sorted(records["nombre"].dropna().unique())
    #selected_jugadora = st.selectbox("Filtrar por jugadora", ["Todas"] + jugadoras)

with col2:

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
        index=None
    )
    
    if jugadora_seleccionada:
        nombre_completo = (jugadora_seleccionada["nombre"] + " " + jugadora_seleccionada["apellido"]).upper()
        records = records[records["id_jugadora"] == jugadora_seleccionada["identificacion"]]

with col3:
    #if jugadora_seleccionada:
    tipos = sorted(records["tipo_lesion"].dropna().unique())

    selected_tipo = st.selectbox("Tipo de lesión", ["Todas"] + tipos, disabled=jugadora_seleccionada is None)

    if selected_tipo and selected_tipo != "Todas":
        records = records[records["tipo_lesion"] == selected_tipo]

st.divider()

if not jugadora_seleccionada:
    st.info("Selecciona una jugadora para continuar.")
    st.stop()

if records.empty:
    st.warning("No hay datos que mostrar para la jugadora seleccionada.")
    st.stop()

# === Mostrar resultado ===
st.markdown(f"**{len(records)} lesiones encontradas**")

df_filtrado = clean_df(records)

st.dataframe(df_filtrado)

st.divider()
col1, col2 = st.columns([1,2])

with col1:
    input_id = st.text_input("Introduce el ID de la lesion:", placeholder="Ejemplo: AJB20251013-4")

# Si se introduce un ID y se presiona Enter
if input_id:
    # Intentamos convertir a número si aplica
    try:
        id_buscar = int(input_id)
    except ValueError:
        id_buscar = input_id  # por si los ID son strings

    # Buscar el registro
    lesion = records.loc[records["id_lesion"] == id_buscar]

    if not lesion.empty:
        lesion_data = lesion.iloc[0].to_dict()
        
        view_registro_lesion(modo="editar", jugadora_seleccionada=jugadora_seleccionada, lesion_data=lesion_data)
    else:
        st.error("No se encontró ninguna lesion con ese ID.")