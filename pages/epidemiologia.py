# pages/epidemiologia.py

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np 

# ----------------- CONFIGURACIÓN BÁSICA DE LA PÁGINA -----------------
st.set_page_config(
    page_title="Análisis Epidemiológico",
    layout="wide" # Usa todo el ancho de la pantalla para los gráficos
)

# ----------------- PASO 1: FUNCIÓN DE CARGA DE DATOS -----------------
# !!! CUIDADO: DEBES REEMPLAZAR ESTA FUNCIÓN CON TU CÓDIGO REAL DE CARGA DE DATOS !!!
# Por ejemplo: leer un archivo CSV, consultar una base de datos o Google Sheets.
# Asegúrate que los nombres de las columnas que lees sean:
# 'Tipo_de_lesion', 'Zona_del_cuerpo', 'Lugar', 'Dias_de_baja_(estimados)'
@st.cache_data
def load_data():
    # --- CÓDIGO DE SIMULACIÓN (REEMPLAZAR) ---
    data = {
        'Jugadora': np.random.choice(['ADRIANA', 'CLAUDIA', 'MARIA', 'ANA'], size=50),
        'Tipo_de_lesion': np.random.choice(['MUSCULAR', 'ARTICULAR', 'TENDINOSA', 'ÓSEA'], size=50),
        'Zona_del_cuerpo': np.random.choice(['MUSLO', 'TOBILLO', 'RODILLA', 'ESPALDA', 'HOMBRO'], size=50),
        'Lugar': np.random.choice(['ENTRENAMIENTO', 'PARTIDO', 'GIMNASIO', 'OTRO'], size=50),
        'Fecha_de_la_lesion': pd.to_datetime(pd.date_range(start='2024-01-01', periods=50, freq='W')),
        'Dias_de_baja_(estimados)': np.random.randint(5, 45, size=50), 
        'Fecha_de_alta_(estimada)': pd.to_datetime(pd.date_range(start='2024-01-01', periods=50, freq='W')) + pd.to_timedelta(np.random.randint(5, 45, size=50), unit='D'),
    }
    df = pd.DataFrame(data)
    # ----------------------------------------
    
    # Columna clave para el cálculo del tiempo de baja. Usamos los días estimados.
    df['dias_baja'] = df['Dias_de_baja_(estimados)'] 
    
    return df

df = load_data()

# ----------------- PASO 2: CÁLCULO DE KPIS RESUMEN -----------------

tiempo_promedio = df['dias_baja'].mean() if not df.empty else 0
total_lesiones = len(df)

# ----------------- PASO 3: INTERFAZ Y VISUALIZACIÓN -----------------

st.title("⚽ Análisis Epidemiológico de Lesiones Femenino")
st.markdown("Dashboard de métricas descriptivas clave para la prevención.")

# --- Fila 1: KPIS Resumen (Métricas) ---
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Total de Lesiones Registradas", value=f"{total_lesiones}")

with col2:
    st.metric(label="Tiempo Promedio de Baja (Estimado)", value=f"{tiempo_promedio:,.1f} días")

# --- Fila 2: Gráficos de Distribución (Dos Columnas de Ancho) ---
st.markdown("---")
col_left, col_right = st.columns(2)

# --- GRÁFICOS EN COLUMNA IZQUIERDA ---
with col_left:
    st.subheader("1. Distribución por Tipo de Lesión")
    
    # KPI 1: Lesiones por Tipo (Gráfico Circular)
    conteo_tipo = df['Tipo_de_lesion'].value_counts().reset_index()
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
    conteo_lugar = df['Lugar'].value_counts().reset_index()
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
    conteo_zona = df['Zona_del_cuerpo'].value_counts().reset_index()
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
    df_tiempo = df.groupby('Tipo_de_lesion')['dias_baja'].mean().reset_index()
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
