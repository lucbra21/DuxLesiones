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

# ----------------- PASO 1: FUNCIÓN DE CARGA DE DATOS REALES (JSONL) -----------------

@st.cache_data
def load_data():
    
    # RUTA DE ARCHIVO CONFIRMADA: data/jugadoras.jsonl
    DATA_FILE_PATH = "data/jugadoras.jsonl" 
    
    try:
        # Usamos pandas.read_json con el argumento 'lines=True' para leer JSONL
        df = pd.read_json(DATA_FILE_PATH, lines=True)

        # Verificar que el DataFrame no esté vacío
        if df.empty:
            st.warning("El archivo JSONL se leyó correctamente, pero está vacío. No hay datos para graficar.")
            return pd.DataFrame() 

        # --- Limpieza y Preparación de Datos ---
        
        # 1. Convierte la columna de días estimados a número.
        df['Dias_de_baja_(estimados)'] = pd.to_numeric(
            df['Dias_de_baja_(estimados)'], 
            errors='coerce' # Convierte cualquier valor no numérico a NaN
        )
        
        # 2. Columna clave para los cálculos de tiempo promedio
        df['dias_baja'] = df['Dias_de_baja_(estimados)'] 

        # 3. Rellena NaNs en columnas categóricas para evitar errores en gráficos
        df['Tipo_de_lesion'] = df['Tipo_de_lesion'].fillna('Desconocido')
        df['Zona_del_cuerpo'] = df['Zona_del_cuerpo'].fillna('Desconocido')
        df['Lugar'] = df['Lugar'].fillna('Desconocido')
        
        return df

    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo de datos JSONL en la ruta: {DATA_FILE_PATH}.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al procesar el archivo JSONL. Verifica el formato de los datos: {e}")
        return pd.DataFrame()

df = load_data()


# Si la carga de datos falló, detenemos la ejecución del resto del script.
if df.empty:
    st.stop()


# ----------------- PASO 2: CÁLCULO DE KPIS RESUMEN -----------------

# Calculamos el promedio solo de los valores no nulos
tiempo_promedio = df['dias_baja'].mean() 
total_lesiones = len(df)

# ----------------- PASO 3: INTERFAZ Y VISUALIZACIÓN -----------------

st.title("⚽ Análisis Epidemiológico de Lesiones Femenino")
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
