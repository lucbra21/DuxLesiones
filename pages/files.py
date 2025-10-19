import streamlit as st
import json
import random
import datetime
from pathlib import Path
import pandas as pd

import src.config as config
config.init_config()

from src.auth import init_app_state, login_view, menu, validate_login
from src.io_files import get_records_df
init_app_state()

validate_login()

# Authentication gate
if not st.session_state["auth"]["is_logged_in"]:
    login_view()
    st.stop()

st.header("Administrador de :red[Archivos]", divider=True)

menu()

df = get_records_df()

st.dataframe(df)

csv_data = df.to_csv(index=False).encode("utf-8")

st.download_button(
        label="Descargar registros en CSV",
        data=csv_data,
        file_name="registros_lesiones.csv",
        mime="text/csv"
    )