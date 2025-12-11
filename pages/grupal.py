import streamlit as st
import plotly.express as px
from src.i18n.i18n import t
import src.app_config.config as config
config.init_config()

from src.ui.ui_components import data_filters_advanced
from src.reports.ui_grupal import groupal_metrics
from src.db.db_records import get_records_plus_players_db
from src.util.util import clean_df

st.header(t("Análisis :red[grupal]"), divider=True)

competicion, posicion, tipo_lesion, fechas, df_filtrado = data_filters_advanced()

st.divider()

# Si la carga de datos falló, detenemos la ejecución del resto del script.
if df_filtrado.empty:
    st.info("No se encontraron registros de lesiones. Por favor, añade datos para continuar.")
    st.stop()

groupal_metrics(df_filtrado)

graficos, tablas = st.tabs([t("Graficos"), t("Registros")])

with graficos:
    # ----------------- GRAFICOS -----------------

    # --- Fila 2: Gráficos de Distribución (Dos Columnas de Ancho) ---
    #st.markdown("---")
    col_left, col_right = st.columns(2)

    # --- GRÁFICOS EN COLUMNA IZQUIERDA ---
    with col_left:
        #st.subheader("1. Distribución por Tipo de Lesión")
        
        # KPI 1: Lesiones por Tipo (Gráfico Circular)
        conteo_tipo = df_filtrado['tipo_lesion'].value_counts().reset_index()
        conteo_tipo.columns = ['Tipo de Lesión', 'Total']
        
        fig_tipo = px.pie(
            conteo_tipo,
            names='Tipo de Lesión',
            values='Total',
            title=t('Distribución por Tipo de Lesión'),
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_tipo.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_tipo)

        #st.subheader("3. Lesiones por Lugar de Ocurrencia")
        # KPI 3: Lesiones por Lugar (Gráfico de Barras)
        conteo_lugar = df_filtrado['lugar'].value_counts().reset_index()
        conteo_lugar.columns = ['Lugar', 'Total']

        fig_lugar = px.bar(
            conteo_lugar,
            x='Lugar',
            y='Total',
            color='Lugar',
            title=t('Lesiones por Lugar de Ocurrencia')
        )
        fig_lugar.update_layout(xaxis_title="", yaxis_title=t("Número de Lesiones"))
        st.plotly_chart(fig_lugar)

    # --- GRÁFICOS EN COLUMNA DERECHA ---
    with col_right:
        #st.subheader("2. Concentración por Zona del Cuerpo")

        # KPI 2: Lesiones por Zona del Cuerpo (Gráfico de Barras Horizontales)
        conteo_zona = df_filtrado['zona_cuerpo'].value_counts().reset_index()
        conteo_zona.columns = ['Zona del Cuerpo', 'Total']

        fig_zona = px.bar(
            conteo_zona.sort_values(by='Total', ascending=True),
            x='Total',
            y='Zona del Cuerpo',
            orientation='h', # Horizontal
            color='Total',
            color_continuous_scale=px.colors.sequential.Sunset,
            title=t('Concentración por Zona del Cuerpo')
        )
        fig_zona.update_layout(xaxis_title=t("Número de Lesiones"), yaxis_title="")
        st.plotly_chart(fig_zona)

        #st.subheader("4. Tiempo de Baja por Tipo de Lesión")
        # KPI 4: Tiempo Promedio de Baja por Tipo de Lesión (Gráfico de Barras)
        df_tiempo = df_filtrado.groupby('tipo_lesion')['dias_baja_estimado'].mean().reset_index()
        df_tiempo.columns = ['Tipo de Lesión', 'Promedio Días de Baja']

        fig_tiempo = px.bar(
            df_tiempo.sort_values(by='Promedio Días de Baja', ascending=False),
            x='Tipo de Lesión',
            y='Promedio Días de Baja',
            color='Promedio Días de Baja',
            title=t('Tiempo de Baja por Tipo de Lesión')
        )
        fig_tiempo.update_layout(yaxis_title=t("Días de Baja (Estimado)"))
        st.plotly_chart(fig_tiempo)

with tablas:
    records = get_records_plus_players_db()
    records_clean = clean_df(records)
    records_filtrados = records_clean[records_clean["id_lesion"].isin(df_filtrado["id_lesion"])]
    st.dataframe(records_filtrados)