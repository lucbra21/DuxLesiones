import streamlit as st
from src.i18n.i18n import t

def groupal_metrics(df_filtrado):

    # --- PASO 1: CÁLCULOS BASE ---
    total_lesiones = len(df_filtrado)
    activas = df_filtrado[df_filtrado["estado_lesion"] == "ACTIVO"].shape[0] if "estado_lesion" in df_filtrado else 0
    porcentaje_activas = round((activas / total_lesiones) * 100, 1) if total_lesiones > 0 else 0
    tiempo_promedio = round(df_filtrado["dias_baja_estimado"].mean(), 1) if "dias_baja_estimado" in df_filtrado else 0

    # --- ZONA CORPORAL MÁS AFECTADA ---
    if "zona_cuerpo" in df_filtrado.columns and not df_filtrado["zona_cuerpo"].dropna().empty:
        zona_top = df_filtrado["zona_cuerpo"].mode()[0]
        zona_count = df_filtrado["zona_cuerpo"].value_counts().iloc[0]
        zona_pct = round((zona_count / total_lesiones) * 100, 1)
    else:
        zona_top, zona_count, zona_pct = "N/A", 0, 0

    # --- TIPO DE LESIÓN MÁS FRECUENTE ---
    if "tipo_lesion" in df_filtrado.columns and not df_filtrado["tipo_lesion"].dropna().empty:
        tipo_top = df_filtrado["tipo_lesion"].mode()[0]
        tipo_count = df_filtrado["tipo_lesion"].value_counts().iloc[0]
        tipo_pct = round((tipo_count / total_lesiones) * 100, 1)
    else:
        tipo_top, tipo_count, tipo_pct = "N/A", 0, 0

    # --- PORCENTAJE DE RECAÍDAS ---
    if "es_recidiva" in df_filtrado.columns:
        recidivas = df_filtrado[df_filtrado["es_recidiva"] == True].shape[0]
        pct_recidivas = round((recidivas / total_lesiones) * 100, 1) if total_lesiones > 0 else 0
    else:
        recidivas, pct_recidivas = 0, 0

    # ==================== PASO 3: INTERFAZ ====================
    col1, col2, col3, col4 = st.columns(4, border=True)
    with col1:
        st.metric(t("Total de Lesiones"), total_lesiones)
    with col2:
        st.metric(t("Lesiones Activas"), activas, f"{porcentaje_activas}%")
    with col3:
        st.metric(t("Días de Baja Promedio"), f"{tiempo_promedio:.1f} días")
    with col4:
        st.metric(t("Recaídas"), recidivas, f"{pct_recidivas}%")
