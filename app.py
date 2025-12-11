import streamlit as st
from src.i18n.i18n import t

import src.app_config.config as config
config.init_config()

from src.auth_system.auth_core import init_app_state, validate_login
from src.auth_system.auth_ui import login_view, menu

from src.util.util import clean_df
from src.ui.ui_components import main_metrics
from src.db.db_records import get_records_plus_players_db

st.header(t("Resumen de :red[Lesiones] (1er Equipo)"), divider=True)

records = get_records_plus_players_db(plantel="1FF")
resumen = main_metrics(records)

st.subheader(t("Ultimas :red[lesiones]"))
df_filtrado = clean_df(resumen)
st.dataframe(df_filtrado)