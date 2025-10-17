import streamlit as st
import pandas as pd
import datetime

import src.config as config
config.init_config()

from src.auth import init_app_state, login_view, menu, validate_login
from src.io_files import get_records_plus_players_df
from src.util import clean_df

init_app_state()
validate_login()

# Authentication gate
if not st.session_state["auth"]["is_logged_in"]:
    #st.text("🔐 Por favor, inicie sesión para acceder a esta página.")
    login_view()
    st.stop()

st.header("Resumen de :red[Lesiones]", divider=True)

menu()

#SHEET_NAME = 'Propuesta tablas'
WORKSHEET_NAME = 'Tabla I invent jugadores' # Asegúrate de que este nombre sea exacto

records = get_records_plus_players_df()  # Carga y cachea los datos

if records.empty:    
    st.warning("No hay datos de lesiones disponibles.")
    st.stop()   

# === Filtros ===
periodo = st.radio("Agrupar por:", ["Semana", "Mes"], horizontal=True)

articulo = "el último"

records["fecha_alta_diagnostico"] = pd.to_datetime(records["fecha_alta_diagnostico"], errors="coerce")
if periodo == "Semana":
    articulo = "la última"
    records["periodo"] = records["fecha_alta_diagnostico"].dt.isocalendar().week
    ultimos = records[records["fecha_alta_diagnostico"] >= (records["fecha_alta_diagnostico"].max() - pd.Timedelta(days=7))]
else:
    records["periodo"] = records["fecha_alta_diagnostico"].dt.month
    ultimos = records[records["fecha_alta_diagnostico"] >= (records["fecha_alta_diagnostico"].max() - pd.Timedelta(days=30))]

# === Métricas base ===
total_lesiones = len(records)
activas = records[records["estado_lesion"] == "ACTIVO"].shape[0]
porcentaje_activas = round((activas / total_lesiones) * 100, 1)
promedio_dias_baja = round(records["dias_baja_estimado"].mean(), 1)
zona_top = records["zona_cuerpo"].mode()[0]
zona_count = records["zona_cuerpo"].value_counts().iloc[0]
zona_pct = round((zona_count / total_lesiones) * 100, 1)

# === Series por periodo ===

# Total de lesiones por periodo (para el gráfico principal)
trend_total = records.groupby("periodo").size().reset_index(name="cantidad")

trend_activas = (
    records[records["estado_lesion"] == "ACTIVO"]
    .groupby("periodo")
    .size()
    .reset_index(name="count")
)
chart_activas = trend_activas["count"].tolist()

trend_dias = (
    records.groupby("periodo")["dias_baja_estimado"]
    .mean()
    .reset_index(name="avg_days")
)

# Redondeamos a 2 decimales
trend_dias["avg_days"] = trend_dias["avg_days"].round(2)
chart_dias = trend_dias["avg_days"].tolist()

trend_zonas = (
    records[records["zona_cuerpo"] == zona_top]
    .groupby("periodo")
    .size()
    .reset_index(name="count")
)
chart_zonas = trend_zonas["count"].tolist()

# === Calcular deltas ===
def calc_delta(values):
    if len(values) < 2:
        return 0
    return round(((values[-1] - values[-2]) / values[-2]) * 100, 1) if values[-2] != 0 else 0

delta_activas = calc_delta(chart_activas)
delta_dias = calc_delta(chart_dias)
delta_zona = calc_delta(chart_zonas)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        "Lesiones activas",
        activas,
        f"{delta_activas:+.1f}%",
        chart_data=chart_activas,
        chart_type="line",
        border=True,
        delta_color="inverse",  # 🔴 if increased, 🟢 if decreased
        help=f"Variación en las lesiones activas en comparación con {articulo} {periodo.lower()}."
    )
with col2:
    st.metric(
        "Días de recuperación promedio",
        promedio_dias_baja,
        f"{delta_dias:+.1f}%",
        chart_data=chart_dias,
        chart_type="area",
        border=True,
        delta_color="normal",  # 🟢 increase = longer recovery
        help=f"Variación del tiempo promedio de recuperación por {periodo.lower()}."
    )
with col3:
    st.metric(
        f"Zona más afectada: {zona_top}",
        f"{zona_count} cases",
        f"{delta_zona:+.1f}%",
        chart_data=chart_zonas,
        chart_type="bar",
        border=True,
        delta_color="inverse",  # 🔴 more injuries in this zone = bad
        help=f"Frecuencia de lesiones en {zona_top} comparado con {articulo} {periodo.lower()}."
    )

#     st.metric(
#         f"Most Affected Zone",
#         zona_top,
#         f"{zona_pct}%",
#         help="Zone with highest injury frequency"
#     )

st.divider()

st.subheader("Ultimas :red[lesiones]")
df_filtrado = clean_df(ultimos)
st.dataframe(df_filtrado)