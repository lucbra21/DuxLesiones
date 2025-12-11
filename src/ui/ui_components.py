import streamlit as st
import datetime
import pandas as pd

from src.i18n.i18n import t
import pandas as pd
import json

from src.db.db_records import load_jugadoras_db, load_competiciones_db, load_lesiones_db
from src.util.schema import MAP_POSICIONES

def load_posiciones_traducidas() -> dict:
    return {key: t(valor_es) for key, valor_es in MAP_POSICIONES.items()}

def selection_header(modo: int = 1):
    ALL_TEXT = t("Todas")

    jug_df, jug_error = load_jugadoras_db()   

    if jug_error:
        st.error(f"{jug_error}")
        st.stop()

    comp_df, comp_error = load_competiciones_db()
   
    if modo == 1:
        col1, col2, col3 = st.columns([2,1,2])
    else:
        records = load_lesiones_db() 

        if records.empty:    
            st.warning(t("No hay datos de lesiones disponibles."))
            st.stop()   
        col1, col2, col3, col4 = st.columns([2,1.3,2,1])

    with col1:
        competiciones_options = comp_df.to_dict("records")
        competicion = st.selectbox(
            t("Plantel"),
            options=competiciones_options,
            format_func=lambda x: f'{x["nombre"]} ({x["codigo"]})',
            placeholder=t("Seleccione un plantel"),
            index=3,
        )
        
    with col2:
        MAP_POSICIONES_TRADUCIDAS = load_posiciones_traducidas()
        MAP_POSICIONES_INVERTIDO = {v: k for k, v in MAP_POSICIONES_TRADUCIDAS.items()}

        posicion_traducida = st.selectbox(
            t("Posición"),
            options=list(MAP_POSICIONES_TRADUCIDAS.values()),
            placeholder=t("Seleccione una Posición"),
            index=None
        )
        
        clave = MAP_POSICIONES_INVERTIDO.get(posicion_traducida)
        posicion = MAP_POSICIONES.get(clave)
        #st.text(f"Clave interna: {posicion}")
    with col3:
        if competicion:
            codigo_competicion = competicion["codigo"]
            jug_df_filtrado = jug_df[jug_df["plantel"] == codigo_competicion]
        else:
            jug_df_filtrado = jug_df

        if posicion:
            jug_df_filtrado = jug_df_filtrado[jug_df_filtrado["posicion"] == posicion]

        jugadoras_filtradas = jug_df_filtrado.to_dict("records")

        jugadora_seleccionada = st.selectbox(
            t("Jugadora"),
            options=jugadoras_filtradas,
            format_func=lambda x: f'{jugadoras_filtradas.index(x) + 1} - {x["nombre"]} {x["apellido"]}',
            placeholder=t("Seleccione una Jugadora"),
            index=None
        )

    if modo >= 2:
        with col4:
            # Filtrado por jugadora seleccionada
            if jugadora_seleccionada:
                records = records[records["id_jugadora"] == jugadora_seleccionada["identificacion"]]
            else:
                if modo == 2:
                    records = pd.DataFrame()
                elif modo == 3:
                    # modo >= 3 → filtrar por todas las jugadoras del plantel o posición
                    if not jug_df_filtrado.empty and "identificacion" in jug_df_filtrado.columns:
                        ids_validos = jug_df_filtrado["identificacion"].astype(str).tolist()
                        records = records[records["id_jugadora"].astype(str).isin(ids_validos)]
                    else:
                        records = pd.DataFrame()

            # Verificar si hay registros
            if records.empty:
                selected_tipo = st.selectbox(
                t("Tipo de lesión"),
                [t("NO APLICA")],
                disabled=True)
            else:
                # Mostrar filtro activo si hay registros
                tipos = sorted(records["tipo_lesion"].dropna().unique())
                selected_tipo = st.selectbox(
                    t("Tipo de lesión"),
                    [ALL_TEXT] + tipos,
                    disabled=False
                )

                if selected_tipo and selected_tipo != ALL_TEXT:
                    records = records[records["tipo_lesion"] == selected_tipo]

   
    #st.dataframe(jug_df_filtrado)
    # Si no hay jugadoras en ese plantel o posición
    if jug_df_filtrado.empty:
        #st.warning("⚠️ No hay jugadoras disponibles para este plantel o posición seleccionada.")
        jugadora_seleccionada = None
        if modo == 1:
            return None, posicion
        else:
            return None, posicion, pd.DataFrame()  # Devuelve vacío

    if modo == 1:
        return jugadora_seleccionada, posicion
    else:
        return jugadora_seleccionada, posicion, records

def data_filters_advanced():
    ALL_TEXT = t("Todas")

    # --- Cargar datos ---
    jug_df, jug_error = load_jugadoras_db()

    if jug_df is None or "plantel" not in jug_df.columns:
        st.error(t("No se pudo cargar la lista de jugadoras o falta la columna 'plantel'."))
        st.stop()
    
    comp_df, comp_error = load_competiciones_db()
    records = load_lesiones_db()

    if records.empty:    
        st.warning(t("No hay datos de lesiones disponibles."))
        st.stop()   

    # --- Validación básica ---
    if jug_df is None or jug_df.empty or records is None or records.empty:
        st.warning(t("No hay datos disponibles para aplicar filtros."))
        return None, None, None, (None, None)

    col1, col2, col3, col4 = st.columns([3, 1.5, 1.5, 2])

    # --- FILTRO 1: Plantel / Competición ---
    with col1:
        competiciones_options = comp_df.to_dict("records") if comp_df is not None else []
        competicion = st.selectbox(
            t("Plantel"),
            options=competiciones_options,
            format_func=lambda x: f'{x["nombre"]} ({x["codigo"]})',
            placeholder=t("Seleccione un plantel"),
            index=3
        )

    # --- FILTRO 2: Posición ---
    with col2:
        MAP_POSICIONES_TRADUCIDAS = load_posiciones_traducidas()
        MAP_POSICIONES_INVERTIDO = {v: k for k, v in MAP_POSICIONES_TRADUCIDAS.items()}

        posicion_traducida = st.selectbox(
            t("Posición"),
            options=[ALL_TEXT] + list(MAP_POSICIONES_TRADUCIDAS.values()),
            placeholder=t("Seleccione una Posición"),
            index=None
        )
        
        if posicion_traducida == ALL_TEXT:
            posicion = ALL_TEXT
        else:
            clave = MAP_POSICIONES_INVERTIDO.get(posicion_traducida)
            posicion = MAP_POSICIONES.get(clave)
        
        #st.text(f"Clave interna: {posicion}")
    # --- FILTRO 3: Tipo de lesión (dependiente de jugadoras filtradas) ---
    with col3:
        # Filtrar jugadoras por competición y posición
        jugadoras_filtradas = jug_df.copy()

        if competicion:
            codigo_competicion = competicion["codigo"]
            jugadoras_filtradas = jugadoras_filtradas[
                jugadoras_filtradas["plantel"] == codigo_competicion
            ]

        if posicion and posicion != ALL_TEXT:
            jugadoras_filtradas = jugadoras_filtradas[
                jugadoras_filtradas["posicion"] == posicion
            ]

        # Filtrar registros por jugadoras filtradas
        if not jugadoras_filtradas.empty and "id_jugadora" in records.columns:
            records_filtrados = records[
                records["id_jugadora"].isin(jugadoras_filtradas["identificacion"])
            ]
        else:
            records_filtrados = records.iloc[0:0].copy()

        # Obtener solo los tipos de lesión que existen en el conjunto filtrado
        tipos = sorted(records_filtrados["tipo_lesion"].dropna().unique().tolist())
        tipo_lesion = st.selectbox("Tipo de lesión", [ALL_TEXT] + tipos)

        # Aplicar el filtro de tipo de lesión
        if tipo_lesion != ALL_TEXT:
            records_filtrados = records_filtrados[
                records_filtrados["tipo_lesion"] == tipo_lesion
            ]

    # --- FILTRO 4: Rango de fechas ---
    with col4:

        # Convertir fechas a datetime
        if "fecha_lesion" in records_filtrados.columns:
            records_filtrados["fecha_lesion"] = pd.to_datetime(records_filtrados["fecha_lesion"], errors="coerce")

        min_date = records_filtrados["fecha_lesion"].min()
        max_date = records_filtrados["fecha_lesion"].max()

        if pd.isna(min_date) or pd.isna(max_date):
            today = datetime.date.today()
            min_date = today - datetime.timedelta(days=15)
            max_date = today
        else:
            # 🔧 Solo convertir a .date() si son Timestamp
            if isinstance(min_date, pd.Timestamp):
                min_date = min_date.date()
            if isinstance(max_date, pd.Timestamp):
                max_date = max_date.date()

        # ✅ No aplicar .date() aquí — ya son tipo date
        default_value = (min_date, max_date)

        fecha_inicio, fecha_fin = st.date_input(
            t("Seleccionar rango"),
            value=(min_date, max_date) if min_date and max_date else (None, None),
            min_value=min_date,
            max_value=max_date,
            format="YYYY-MM-DD"
        )

        if fecha_inicio and fecha_fin:
            mask = (records_filtrados["fecha_lesion"] >= pd.to_datetime(fecha_inicio)) & (
                records_filtrados["fecha_lesion"] <= pd.to_datetime(fecha_fin)
            )
            records_filtrados = records_filtrados.loc[mask]

    # --- Resultado final ---
    return competicion, posicion, tipo_lesion, (fecha_inicio, fecha_fin), records_filtrados

def preview_record(record: dict) -> None:
    #st.subheader("Previsualización")
    # Header with key fields
    #jug = record.get("nombre", "-")
    fecha = record.get("fecha_hora", "-")
    posicion = record.get("posicion", "-")
    tipo = record.get("tipo_lesion", "-")
    #st.markdown(f"**Jugadora:** {jug}  |  **Fecha:** {fecha}  |  **Posicion:** {posicion}  |  **Tipo Lesión:** {tipo}")
    with st.expander(t("Ver registro JSON"), expanded=False):
        st.code(json.dumps(record, ensure_ascii=False, indent=2), language="json")

def main_metrics(records, modo="overview"):
    """
    Muestra métricas principales de lesiones según el modo:
    - 'overview': agrupa por periodo (semana/mes), muestra filtros y help en métricas.
    - 'reporte': usa todo el DataFrame sin agrupar ni filtros.
    """

    # --- Validación inicial ---
    if records.empty:    
        st.warning(t("No hay datos de lesiones disponibles."))
        st.stop()  

    # Convertir fecha y limpiar
    records["fecha_lesion"] = pd.to_datetime(records["fecha_lesion"], errors="coerce")

    ultimos = records.copy()
    articulo, periodo = "", ""

    default_period = "Semana"
    OPCIONES_PERIODO = {
       # "Hoy": t("Hoy"),
       # "Último día": t("Último día"),
        "Semana": t("Semana"),
        "Mes": t("Mes")
    }

    # --- MODO OVERVIEW ---
    if modo == "overview":

        periodo_traducido = st.radio(t("Periodo:"),
        list(OPCIONES_PERIODO.values()),horizontal=True,
        index=list(OPCIONES_PERIODO.keys()).index(default_period))

        periodo = next(k for k, v in OPCIONES_PERIODO.items() if v == periodo_traducido)

        #periodo = st.radio(t("Periodo:"), ["Semana", "Mes"], horizontal=True)
        articulo = "la última" if periodo == "Semana" else "el último"

        if periodo == "Semana":
            records["periodo"] = records["fecha_lesion"].dt.isocalendar().week
            ultimos = records[
                records["fecha_lesion"]
                >= (records["fecha_lesion"].max() - pd.Timedelta(days=7))
            ]
        else:
            records["periodo"] = records["fecha_lesion"].dt.month
            ultimos = records[
                records["fecha_lesion"]
                >= (records["fecha_lesion"].max() - pd.Timedelta(days=30))
            ]

        #st.dataframe(ultimos)
    # --- MODO REPORTE ---
    elif modo == "reporte":
        # No agrupar por periodo; se muestran métricas globales
        records["periodo"] = 1  # valor fijo para mantener compatibilidad con cálculos
        articulo = "todo el periodo registrado"

    # === Métricas base ===
    total_lesiones = len(records)
    activas = records[records["estado_lesion"] == "ACTIVO"].shape[0]
    porcentaje_activas = round((activas / total_lesiones) * 100, 1) if total_lesiones else 0
    promedio_dias_baja = round(records["dias_baja_estimado"].mean(), 1) if not records["dias_baja_estimado"].empty else 0

    zona_top = records["zona_cuerpo"].mode()[0] if not records["zona_cuerpo"].empty else "-"
    zona_count = records["zona_cuerpo"].value_counts().iloc[0] if not records["zona_cuerpo"].empty else 0
    zona_pct = round((zona_count / total_lesiones) * 100, 1) if total_lesiones else 0

    # === Series por periodo ===
    trend_total = records.groupby("periodo").size().reset_index(name="cantidad")
    trend_activas = (
        records[records["estado_lesion"] == "ACTIVO"]
        .groupby("periodo")
        .size()
        .reset_index(name="count")
    )
    trend_dias = (
        records.groupby("periodo")["dias_baja_estimado"]
        .mean()
        .reset_index(name="avg_days")
        .round(2)
    )
    trend_zonas = (
        records[records["zona_cuerpo"] == zona_top]
        .groupby("periodo")
        .size()
        .reset_index(name="count")
    )

    chart_total = trend_total["cantidad"].tolist()
    chart_activas = trend_activas["count"].tolist()
    chart_dias = trend_dias["avg_days"].tolist()
    chart_zonas = trend_zonas["count"].tolist()

    # === Calcular deltas ===
    def calc_delta(values):
        if len(values) < 2 or values[-2] == 0:
            return 0
        return round(((values[-1] - values[-2]) / values[-2]) * 100, 1)

    delta_total = calc_delta(chart_total)
    delta_activas = calc_delta(chart_activas)
    delta_dias = calc_delta(chart_dias)
    delta_zona = calc_delta(chart_zonas)

    # === Visualización de métricas ===
    col1, col2, col3, col4 = st.columns(4)

    help_texts = (modo == "overview")  # solo mostrar help en modo overview

    with col1:
        st.metric(
            t("Total de lesiones registradas"),
            total_lesiones,
            f"{delta_total:+.1f}%",
            chart_data=chart_total,
            chart_type="area",
            border=True,
            delta_color="normal",
            help=f"{t('Variación del número total de lesiones comparado con')} {articulo} {periodo.lower()}."
            if help_texts else None,
        )
    with col2:
        st.metric(
            t("Lesiones activas"),
            activas,
            f"{delta_activas:+.1f}%",
            chart_data=chart_activas,
            chart_type="line",
            border=True,
            delta_color="inverse",
            help=f"{t('Variación en las lesiones activas respecto a')} {articulo} {periodo.lower()}."
            if help_texts else None,
        )
    with col3:
        st.metric(
            t("Días de recuperación promedio"),
            promedio_dias_baja,
            f"{delta_dias:+.1f}%",
            chart_data=chart_dias,
            chart_type="area",
            border=True,
            delta_color="normal",
            help=f"{t('Variación del tiempo promedio de recuperación por {periodo.lower()}.')}"
            if help_texts else None,
        )
    with col4:
        st.metric(
            f"{t('Zona más afectada:')} {zona_top}",
            f"{zona_count} casos",
            f"{delta_zona:+.1f}%",
            chart_data=chart_zonas,
            chart_type="bar",
            border=True,
            delta_color="inverse",
            help=f"{t('Frecuencia de lesiones en')} {zona_top} comparado con {articulo} {periodo.lower()}."
            if help_texts else None,
        )

    return ultimos
