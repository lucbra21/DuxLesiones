import pandas as pd
import streamlit as st
import src.config as config
config.init_config()

from src.auth import init_app_state, login_view, menu, validate_login
from src.io_files import save_if_modified, load_users
from src.util import generar_lesiones_aleatorias, load_lesiones_jsonl

init_app_state()
validate_login()

# Authentication gate
if not st.session_state["auth"]["is_logged_in"]:
    login_view()
    st.stop()

if st.session_state["auth"]["rol"] != "developer":
    st.switch_page("app.py")

st.header("Area de:red[Desarrollo]", divider=True)

#st.header("Simulador de :red[Lesiones]", divider=True)

menu()

usuarios, simulador = st.tabs(["USUARIOS", "SIMULADOR"])
with usuarios:
    data = load_users()
    df = pd.DataFrame(data)
    #df = get_records_plus_players_df()
    #st.dataframe(df)
    df_edited = st.data_editor(df, num_rows="dynamic")
    save_if_modified(df, df_edited, "usuarios")

with simulador:

    #output_lesiones="data/lesiones.jsonl"
    jugadoras_path="data/jugadoras.jsonl"

    if st.button("Generar lesiones aleatorias"):
        try:
            output_lesiones = generar_lesiones_aleatorias(
                jugadoras_path="data/jugadoras.jsonl",
                output_dir="data",
                lesiones_por_jugadora=10
            )
            st.success(f"✅ Lesiones generadas correctamente en: {output_lesiones.name}")

            df, error = load_lesiones_jsonl(output_lesiones)

            if error:
                st.error(error)
            else:
                st.success(f"Se cargaron {len(df)} lesiones correctamente.")
                st.dataframe(df)
        except Exception as e:
                st.error(f"❌ Error al generar lesiones: {e}")


