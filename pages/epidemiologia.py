import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np 

import src.config as config
config.init_config()

from src.auth import init_app_state, login_view, menu, validate_login
from src.io_files import get_records_df, load_jugadoras
init_app_state()

validate_login()

# Authentication gate
if not st.session_state["auth"]["is_logged_in"]:
    #st.text("🔐 Por favor, inicie sesión para acceder a esta página.")
    login_view()
    st.stop()

st.header("Análisis :red[Epidemiológico]", divider=True)

menu()

jug_df, jug_error = load_jugadoras()
records = get_records_df() 

# Si la carga de datos falló, detenemos la ejecución del resto del script.
if records.empty:
    st.info("No se encontraron registros de lesiones. Por favor, añade datos para continuar.")
    st.stop()

#st.dataframe(jug_df)

# ----------------- PASO 2: CÁLCULO DE KPIS RESUMEN -----------------

# Calculamos el promedio solo de los valores no nulos
tiempo_promedio = records['dias_baja_estimado'].mean() 
total_lesiones = len(records)

# ----------------- PASO 3: INTERFAZ Y VISUALIZACIÓN -----------------

st.markdown("Dashboard de métricas descriptivas clave para la prevención.")

# --- Fila 1: KPIS Resumen (Métricas) ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Total de Lesiones Registradas", value=f"{total_lesiones}")

with col2:
    # Usamos 1f para mostrar un decimal en el promedio
    st.metric(label="Tiempo Promedio de Baja (Estimado)", value=f"{tiempo_promedio:,.1f} días")

# --- Fila 2: Gráficos de Distribución (Dos Columnas de Ancho) ---
st.markdown("---")
col_left, col_right = st.columns(2)

# --- GRÁFICOS EN COLUMNA IZQUIERDA ---
with col_left:
    st.subheader("1. Distribución por Tipo de Lesión")
    
    # KPI 1: Lesiones por Tipo (Gráfico Circular)
    conteo_tipo = records['tipo_lesion'].value_counts().reset_index()
    conteo_tipo.columns = ['Tipo de Lesión', 'Total']
    
    fig_tipo = px.pie(
        conteo_tipo,
        names='Tipo de Lesión',
        values='Total',
        title='Lesiones por Tipo',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig_tipo.update_traces(textinfo='percent+label')
    st.plotly_chart(fig_tipo, use_container_width=True)

    st.subheader("3. Lesiones por Lugar de Ocurrencia")
    # KPI 3: Lesiones por Lugar (Gráfico de Barras)
    conteo_lugar = records['lugar'].value_counts().reset_index()
    conteo_lugar.columns = ['Lugar de Lesión', 'Total']

    fig_lugar = px.bar(
        conteo_lugar,
        x='Lugar de Lesión',
        y='Total',
        color='Lugar de Lesión',
        title='Lesiones por Lugar'
    )
    fig_lugar.update_layout(xaxis_title="", yaxis_title="Número de Lesiones")
    st.plotly_chart(fig_lugar, use_container_width=True)


# --- GRÁFICOS EN COLUMNA DERECHA ---
with col_right:
    st.subheader("2. Concentración por Zona del Cuerpo")

    # KPI 2: Lesiones por Zona del Cuerpo (Gráfico de Barras Horizontales)
    conteo_zona = records['zona_cuerpo'].value_counts().reset_index()
    conteo_zona.columns = ['Zona del Cuerpo', 'Total']

    fig_zona = px.bar(
        conteo_zona.sort_values(by='Total', ascending=True),
        x='Total',
        y='Zona del Cuerpo',
        orientation='h', # Horizontal
        color='Total',
        color_continuous_scale=px.colors.sequential.Sunset,
        title='Zonas Más Lesionadas'
    )
    fig_zona.update_layout(xaxis_title="Número de Lesiones", yaxis_title="")
    st.plotly_chart(fig_zona, use_container_width=True)

    st.subheader("4. Tiempo de Baja por Tipo de Lesión")
    # KPI 4: Tiempo Promedio de Baja por Tipo de Lesión (Gráfico de Barras)
    df_tiempo = records.groupby('tipo_lesion')['dias_baja_estimado'].mean().reset_index()
    df_tiempo.columns = ['Tipo de Lesión', 'Promedio Días de Baja']

    fig_tiempo = px.bar(
        df_tiempo.sort_values(by='Promedio Días de Baja', ascending=False),
        x='Tipo de Lesión',
        y='Promedio Días de Baja',
        color='Promedio Días de Baja',
        title='Impacto en Días de Baja por Tipo'
    )
    fig_tiempo.update_layout(yaxis_title="Días de Baja (Estimado)")
    st.plotly_chart(fig_tiempo, use_container_width=True)
