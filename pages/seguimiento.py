import pandas as pd
import streamlit as st
import src.config as config
config.init_config()

from src.records_ui import view_registro_lesion
from src.ui_components import data_filters
from src.auth import init_app_state, login_view, menu, validate_login
from src.util import clean_df, sanitize_lesion_data

init_app_state()
validate_login()

# Authentication gate
if not st.session_state["auth"]["is_logged_in"]:
    login_view()
    st.stop()

st.header("Seguimiento de :red[Lesiones]", divider="red")

menu()

jugadora_seleccionada, posicion, records = data_filters(modo=2)
st.divider()

#records = get_records_df()  # Carga y cachea los datos

if records.empty:    
    st.warning("No hay datos de lesiones disponibles.")
    st.stop()   
    
if not jugadora_seleccionada:
    st.info("Selecciona una jugadora para continuar.")
    st.stop()

if jugadora_seleccionada and isinstance(jugadora_seleccionada, dict):
    nombre_completo = (jugadora_seleccionada["nombre"] + " " + jugadora_seleccionada["apellido"]).upper()
    id_jugadora = jugadora_seleccionada["identificacion"]
    posicion = jugadora_seleccionada["posicion"]

    jugadora_info = {
        "id_jugadora": jugadora_seleccionada.get("identificacion"),
        "nombre_completo": f"{jugadora_seleccionada.get('nombre', '')} {jugadora_seleccionada.get('apellido', '')}".upper().strip(),
        "posicion": jugadora_seleccionada.get("posicion"),
        "id_lesion": None
    }

    records = records[records["id_jugadora"] == jugadora_seleccionada["identificacion"]]

#nombre_completo = (jugadora_seleccionada["nombre"] + " " + jugadora_seleccionada["apellido"]).upper()
    
# if records.empty:
#     st.warning("No hay datos que mostrar para la jugadora seleccionada.")
#     st.stop()

# === Mostrar resultado ===
st.markdown(f"**{len(records)} lesiones encontradas**")
df_filtrado = clean_df(records)
st.dataframe(df_filtrado)

#st.divider()
st.subheader(":red[Buscar] lesión", divider="red")
col1, col2 = st.columns([1,2])

with col1:
    input_id = st.text_input("Introduce el ID de la lesión:", value="AC20251026-2", placeholder="Ejemplo: AJB20251013-4")

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
        lesion_data = sanitize_lesion_data(lesion_data)
        #with st.expander(f"Registro médico de la lesión",expanded=True):
        view_registro_lesion(modo="editar", jugadora_info=jugadora_info, lesion_data=lesion_data)
    else:
        st.error("No se encontró ninguna lesion con ese ID.")