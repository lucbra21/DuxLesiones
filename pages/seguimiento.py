import pandas as pd
import streamlit as st
import src.config as config
config.init_config()

from src.io_files import get_records_df, load_jugadoras, upsert_jsonl, load_competiciones
from src.ui_components import view_registro_lesion, data_filters
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

jugadora_seleccionada, posicion = data_filters(modo=2)
st.divider()

records = get_records_df()  # Carga y cachea los datos

if records.empty:    
    st.warning("No hay datos de lesiones disponibles.")
    st.stop()   
    
if not jugadora_seleccionada:
    st.info("Selecciona una jugadora para continuar.")
    st.stop()

nombre_completo = (jugadora_seleccionada["nombre"] + " " + jugadora_seleccionada["apellido"]).upper()
records = records[records["id_jugadora"] == jugadora_seleccionada["identificacion"]]

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