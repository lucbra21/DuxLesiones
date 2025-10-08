import pandas as pd
import streamlit as st
import src.config as config
config.init_config()

from src.io_files import get_records_df
from src.auth import init_app_state, login_view, menu, validate_login
init_app_state()
validate_login()

# Authentication gate
if not st.session_state["auth"]["is_logged_in"]:
    login_view()
    st.stop()

st.header("Historico de :red[Lesiones]", divider="red")

menu()

records = get_records_df()  # Carga y cachea los datos
records["fecha_alta_diagnostico"] = pd.to_datetime(records["fecha_alta_diagnostico"], errors="coerce")

# === Filtros ===
#st.subheader("Filtros", divider="gray")

col1, col2, col3, col4 = st.columns(4)

with col1:
    jugadoras = sorted(records["nombre_jugadora"].dropna().unique())
    selected_jugadora = st.selectbox("Filtrar por jugadora", ["Todas"] + jugadoras)

with col2:
    tipos = sorted(records["tipo_lesion"].dropna().unique())
    selected_tipo = st.selectbox("Tipo de lesión", ["Todas"] + tipos)

with col3:
    gravedades = sorted(records["gravedad"].dropna().unique())
    selected_gravedad = st.selectbox("Gravedad", ["Todas"] + gravedades)

with col4:
    # Filtro por rango de fechas
    min_fecha = records["fecha_alta_diagnostico"].min()
    max_fecha = records["fecha_alta_diagnostico"].max()
    fecha_inicio, fecha_fin = st.date_input(
        "Rango de fechas (diagnóstico)",
        [min_fecha, max_fecha]
    )

# === Aplicar filtros dinámicamente ===
filtered = records.copy()

if selected_jugadora != "Todas":
    filtered = filtered[filtered["nombre_jugadora"] == selected_jugadora]

if selected_tipo != "Todas":
    filtered = filtered[filtered["tipo_lesion"] == selected_tipo]

if selected_gravedad != "Todas":
    filtered = filtered[filtered["gravedad"] == selected_gravedad]

filtered = filtered[
    (filtered["fecha_alta_diagnostico"].dt.date >= fecha_inicio)
    & (filtered["fecha_alta_diagnostico"].dt.date <= fecha_fin)
]

# === Mostrar resultado ===
st.markdown(f"**{len(filtered)} lesiones encontradas**")
st.dataframe(filtered, use_container_width=True)

