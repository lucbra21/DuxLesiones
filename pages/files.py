import pandas as pd
import streamlit as st
from src.io_files import save_if_modified, load_jugadoras, get_records_plus_players_df

import src.config as config
config.init_config()
from src.util import clean_df
from src.ui_components import data_filters
from src.auth import init_app_state, login_view, menu, validate_login

init_app_state()
validate_login()

# Authentication gate
if not st.session_state["auth"]["is_logged_in"]:
    login_view()
    st.stop()

st.header("Administrador de :red[Registros]", divider=True)

menu()

#df = get_records_plus_players_df()

jugadora_seleccionada, posicion, records = data_filters(modo=3)

if records.empty:    
    st.warning("No hay datos de lesiones disponibles.")
    st.stop()   

df_filtrado = clean_df(records)

disabled = records.columns.tolist()
df_edited = st.data_editor(df_filtrado, num_rows="dynamic", disabled=disabled)

#save_if_modified(df_filtrado, df_edited)
csv_data = df_edited.to_csv(index=False).encode("utf-8")

st.download_button(
        label="Descargar registros en CSV",
        data=csv_data,
        file_name="registros_lesiones.csv",
        mime="text/csv"
    )

if st.session_state["auth"]["rol"] == "developer":
    # Convertir a JSON (texto legible, sin índices)
    json_data = df_edited.to_json(orient="records", force_ascii=False, indent=2)
    json_bytes = json_data.encode("utf-8")

    # Botón de descarga
    st.download_button(
        label="📥 Descargar registros en JSON",
        data=json_bytes,
        file_name="registros_lesiones.json",
        mime="application/json"
    )