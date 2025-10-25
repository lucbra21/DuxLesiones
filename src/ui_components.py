import time
import streamlit as st
import datetime
from src.io_files import load_jugadoras, upsert_jsonl, load_competiciones, get_records_df, load_catalog_list
import pandas as pd

import math
import pandas as pd
import numpy as np
import json

from src.util import get_photo, get_drive_direct_url, debe_deshabilitar_subtipo

def is_valid(value):
    """Devuelve True si el valor no es None, vacío ni NaN."""
    if value is None:
        return False
    if isinstance(value, str) and value.strip() == "":
        return False
    if isinstance(value, (float, np.floating)) and math.isnan(value):
        return False
    if pd.isna(value):  # cubre np.nan, pd.NaT y similares
        return False
    return True

def data_filters(modo: int = 1):
    jug_df, jug_error = load_jugadoras()

    if jug_df is None or "plantel" not in jug_df.columns:
        st.error("❌ No se pudo cargar la lista de jugadoras o falta la columna 'plantel'.")
        st.stop()
    
    comp_df, comp_error = load_competiciones()
    
    if modo == 1:
        col1, col2, col3 = st.columns([2,1,2])
    else:
        records = get_records_df() 
        if records.empty:    
            st.warning("No hay datos de lesiones disponibles.")
            st.stop()   
        col1, col2, col3, col4 = st.columns([2,1,2,1])

    with col1:
        competiciones_options = comp_df.to_dict("records")
        competicion = st.selectbox(
            "Plantel",
            options=competiciones_options,
            format_func=lambda x: f'{x["nombre"]} ({x["codigo"]})',
            placeholder="Seleccione un plantel",
            index=3,
        )
        
    with col2:
        posicion = st.selectbox(
            "Posición",
            ["PORTERA", "DEFENSA", "CENTRO", "DELANTERA"],
            placeholder="Seleccione una Posición",
            index=None
        )
        
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
            "Jugadora",
            options=jugadoras_filtradas,
            format_func=lambda x: f'{jugadoras_filtradas.index(x) + 1} - {x["nombre"]} {x["apellido"]}',
            placeholder="Seleccione una Jugadora",
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
                "Tipo de lesión",
                ["NO APLICA"],
                disabled=True)
            else:
                # Mostrar filtro activo si hay registros
                tipos = sorted(records["tipo_lesion"].dropna().unique())
                selected_tipo = st.selectbox(
                    "Tipo de lesión",
                    ["Todas"] + tipos,
                    disabled=False
                )

                if selected_tipo and selected_tipo != "Todas":
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
    # --- Cargar datos ---
    jug_df, jug_error = load_jugadoras()

    if jug_df is None or "plantel" not in jug_df.columns:
        st.error("❌ No se pudo cargar la lista de jugadoras o falta la columna 'plantel'.")
        st.stop()
    
    comp_df, comp_error = load_competiciones()
    records = get_records_df()

    if records.empty:    
        st.warning("No hay datos de lesiones disponibles.")
        st.stop()   


    # --- Validación básica ---
    if jug_df is None or jug_df.empty or records is None or records.empty:
        st.warning("No hay datos disponibles para aplicar filtros.")
        return None, None, None, (None, None)

    col1, col2, col3, col4 = st.columns([3, 1, 1.5, 2])

    # --- FILTRO 1: Plantel / Competición ---
    with col1:
        competiciones_options = comp_df.to_dict("records") if comp_df is not None else []
        competicion = st.selectbox(
            "Plantel",
            options=competiciones_options,
            format_func=lambda x: f'{x["nombre"]} ({x["codigo"]})',
            placeholder="Seleccione un plantel",
            index=3
        )

    # --- FILTRO 2: Posición ---
    with col2:
        posicion = st.selectbox(
            "Posición",
            ["Todas", "PORTERA", "DEFENSA", "CENTRO", "DELANTERA"],
            placeholder="Seleccione una Posición",
            index=0
        )

    # --- FILTRO 3: Tipo de lesión (dependiente de jugadoras filtradas) ---
    with col3:
        # Filtrar jugadoras por competición y posición
        jugadoras_filtradas = jug_df.copy()

        if competicion:
            codigo_competicion = competicion["codigo"]
            jugadoras_filtradas = jugadoras_filtradas[
                jugadoras_filtradas["plantel"] == codigo_competicion
            ]

        if posicion and posicion != "Todas":
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
        tipo_lesion = st.selectbox("Tipo de lesión", ["Todas"] + tipos)

        # Aplicar el filtro de tipo de lesión
        if tipo_lesion != "Todas":
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
            "Seleccionar rango",
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

def view_registro_lesion(modo: str = "nuevo", jugadora_seleccionada: str = None, posicion: str = None, lesion_data = None) -> None:

    segmentos_corporales_df = load_catalog_list("segmentos_corporales", as_df=True)
    map_segmentos_nombre_a_id = dict(zip(segmentos_corporales_df["nombre"], segmentos_corporales_df["id"]))
    segmentos_corporales_list = segmentos_corporales_df["nombre"].tolist()

    zonas_segmento_df = load_catalog_list("zonas_por_segmento", key="zonas_segmento", as_df=True)
    map_zonas_segmento_nombre_a_id = dict(zip(zonas_segmento_df["nombre"], zonas_segmento_df["id"]))

    zonas_anatomicas_df = load_catalog_list("zonas_anatomicas", as_df=True)
    #map_zonas_anatomicas_nombre_a_id = dict(zip(zonas_anatomicas_df["nombre"], zonas_anatomicas_df["id"]))

    #tipos_lesion = load_catalog_list("tipos_lesion") 
    mecanismos_df = load_catalog_list("mecanismos", as_df=True)
    mecanismo_list = mecanismos_df["nombre"].tolist()

    tipos_lesion_df = load_catalog_list("tipo_lesion", as_df=True)
    map_tipo_nombre_a_id = dict(zip(tipos_lesion_df["nombre"], tipos_lesion_df["id"]))
    #map_tipo_id_a_nombre = dict(zip(tipos_lesion_df["id"], tipos_lesion_df["nombre"]))
    subtipos_df = load_catalog_list("tipo_especifico_lesion", as_df=True)
    relacion_df = load_catalog_list("mecanismo_tipo_lesion", as_df=True)

    lateralidades = load_catalog_list("lateralidades")
    tratamientos = load_catalog_list("tratamientos")
    tipos_recidiva = load_catalog_list("tipos_recidiva")

    lugares = load_catalog_list("lugares")
    #mecanismos = load_catalog_list("mecanismos")

    df_gravedad = load_catalog_list("gravedad", as_df=True)
    gravedad_dias = (df_gravedad.set_index("nombre")[["dias_min", "dias_max"]].apply(tuple, axis=1).to_dict())
    
    if "form_version" not in st.session_state:
        st.session_state["form_version"] = 0

    error = False
    if jugadora_seleccionada and isinstance(jugadora_seleccionada, dict):
        nombre_completo = (jugadora_seleccionada["nombre"] + " " + jugadora_seleccionada["apellido"]).upper()
        id_jugadora = jugadora_seleccionada["identificacion"]
        posicion = jugadora_seleccionada["posicion"]
        records = get_records_df() 
        if modo == "nuevo":
            nuevo_id = generar_id_lesion(nombre_completo, id_jugadora, records)
            #st.text(f"Nuevo ID generado: {nuevo_id}")
    else:
        st.info("Selecciona una jugadora para continuar.")
        st.stop()
    
    disabled_edit = False
    if modo == "editar":
        disabled_edit = True

    disabled_evolution = False
    
    if lesion_data and lesion_data["estado_lesion"] == "INACTIVO":
        fecha_alta_medica = lesion_data.get("fecha_alta_medica", None)
        fecha_alta_deportiva = lesion_data.get("fecha_alta_deportiva", None)
        
        disabled_evolution = True
        st.warning(f"La lesi´n esta **'Inactiva'**, **fecha de alta médica:** {fecha_alta_medica}, **fecha de alta deportiva:** {fecha_alta_deportiva}. No se pueden editar los datos")

    lesion_help ="Lesiones agrupadas según el tejido afectado y mecanismo (criterios FIFA/UEFA)."
    
    if modo == "editar":
        fecha_lesion_date = datetime.date.fromisoformat(lesion_data["fecha_lesion"])
        fecha_alta_diagnostico_date = datetime.date.fromisoformat(lesion_data["fecha_alta_diagnostico"])
        
        diagnostico_text = lesion_data.get("diagnostico", "")
        descripcion_text = lesion_data.get("descripcion", "")
        personal_reporte_text = lesion_data.get("personal_reporta", "")
        dias_baja_estimado = int(lesion_data.get("dias_baja_estimado", 0))
        
        fecha_alta_medica = lesion_data.get("fecha_alta_medica", None)
        fecha_alta_deportiva = lesion_data.get("fecha_alta_deportiva", None)
        
        if is_valid(fecha_alta_medica):
            alta_medica_value = True  
        else:
            fecha_alta_medica = None
            alta_medica_value = False
            
        if is_valid(fecha_alta_deportiva):
            alta_deportiva_value = True
        else:
            fecha_alta_deportiva = None
            alta_deportiva_value = False

        tratamientos_selected = lesion_data.get("tipo_tratamiento", [])

        for m in tratamientos_selected:
            if m not in tratamientos:
                tratamientos.append(m)

        tratamientos_default=[p for p in tratamientos_selected if p in tratamientos]

        es_recidiva_value = lesion_data.get("es_recidiva")

        try:
            idx_segmento = None
            if is_valid(lesion_data.get("segmento")):
                idx_segmento = segmentos_corporales_list.index(lesion_data["segmento"])
        except ValueError:
            lugares.append(lesion_data["segmento"])
            idx_segmento = segmentos_corporales_list.index(lesion_data["segmento"])

        try:
            idx_lugar = None
            if is_valid(lesion_data.get("lugar")):
                idx_lugar = lugares.index(lesion_data["lugar"])
        except ValueError:
            lugares.append(lesion_data["lugar"])
            idx_lugar = lugares.index(lesion_data["lugar"])

        try:
            idx_mecanismo = None
            if is_valid(lesion_data.get("mecanismo_lesion")):
                idx_mecanismo = mecanismo_list.index(lesion_data["mecanismo_lesion"])
        except ValueError:
            mecanismo_list.append(lesion_data["mecanismo_lesion"])
            idx_mecanismo = mecanismo_list.index(lesion_data["mecanismo_lesion"])

        try:
            idx_lateralidad = None
            if is_valid(lesion_data.get("lateralidad")):
                idx_lateralidad = lateralidades.index(lesion_data["lateralidad"])
        except ValueError:
            lateralidades.append(lesion_data["lateralidad"])
            idx_lateralidad = lateralidades.index(lesion_data["lateralidad"])

        # try:
        #     idx_tipos_lesion = None
        #     if is_valid(lesion_data.get("tipo_lesion")):
        #         idx_tipos_lesion = tipos_lesion.index(lesion_data["tipo_lesion"])
        # except ValueError:
        #     tipos_lesion.append(lesion_data["tipo_lesion"])
        #     idx_tipos_lesion = tipos_lesion.index(lesion_data["tipo_lesion"])

        try:
            idx_tipo_recidiva = None
            if is_valid(lesion_data.get("tipo_recidiva")):
                idx_tipo_recidiva = tipos_recidiva.index(lesion_data["tipo_recidiva"])
        except ValueError:
            lugares.append(lesion_data["tipo_recidiva"])
            idx_tipo_recidiva = tipos_recidiva.index(lesion_data["tipo_recidiva"])


    else:
        fecha_lesion_date = datetime.date.today()
        fecha_alta_diagnostico_date = datetime.date.today() + datetime.timedelta(days=1)
        idx_zonas = None
        idx_lugar = None
        idx_mecanismo = None
        idx_lateralidad = None
        idx_tipos_lesion = None
        es_recidiva_value = None
        idx_zona_espec = None
        idx_tipo_recidiva = None    
        diagnostico_text = ""
        descripcion_text = ""
        personal_reporte_text = ""
        dias_baja_estimado = "0"
        tratamientos_default = []
        idx_tipo_especifico = None
        idx_segmento = None
        gravedad = None

    #st.selectbox("Gravedad clínica", ["Leve", "Moderada", "Grave", "Muy grave", "Recidiva"])
    placeholder="Selecciona una opción"
    default_list=["NO APLICA"]

    #with st.form("form_registro_lesion", clear_on_submit=True, border=False):
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        fecha_lesion = st.date_input("Fecha de la lesión", fecha_lesion_date, 
                                     disabled=disabled_edit, max_value=datetime.date.today(),  
                                     key=f"fecha_lesion_{st.session_state['form_version']}")
        fecha_str = fecha_lesion.strftime("%Y-%m-%d")

        segmento = st.selectbox("Región anatómica", segmentos_corporales_list, 
                                index=idx_segmento, disabled=disabled_edit, placeholder=placeholder, 
                                key=f"segmento_{st.session_state['form_version']}")
    with col2:
        lugar = st.selectbox("Lugar", lugares, index=idx_lugar, disabled=disabled_edit, placeholder=placeholder, 
                             key=f"lugar_{st.session_state['form_version']}")
        
        idx_zonas = 0
        if segmento:
            segmento_id = map_segmentos_nombre_a_id.get(segmento)
            zonas_segmento_filtrados = zonas_segmento_df[zonas_segmento_df["segmento_id"] == segmento_id]
            zonas_segmento_list = zonas_segmento_filtrados["nombre"].tolist()
        else:
            zonas_segmento_list = []

        # Si hay subtipos, usarlos; si no, usar el valor por defecto
        opciones_tipo_zona = zonas_segmento_list if zonas_segmento_list else default_list
        is_disabled = disabled_edit or not zonas_segmento_list
    
        if modo == "editar":
            try:
                idx_zonas = zonas_segmento_list.index(lesion_data["zona_cuerpo"])
            except ValueError:
                idx_zonas = 0

        zona_cuerpo = st.selectbox("Zona anatómica", opciones_tipo_zona, index=idx_zonas, disabled=is_disabled, 
                                   placeholder=placeholder, key=f"zona_cuerpo_{st.session_state['form_version']}")
    with col3:
        mecanismo_lesion = st.selectbox("Mecanismo de lesión", mecanismo_list, index=idx_mecanismo, disabled=disabled_edit, 
                                        placeholder=placeholder, key=f"mecanismo_lesion_{st.session_state['form_version']}")
        
        idx_zona_espec = 0
        if zona_cuerpo:
            zonas_segmento_id = map_zonas_segmento_nombre_a_id.get(zona_cuerpo)
            zonas_anatomicas_filtrados = zonas_anatomicas_df[zonas_anatomicas_df["zona_id"] == zonas_segmento_id]
            zonas_anatomicas_list = zonas_anatomicas_filtrados["nombre"].tolist()
        else:
            zonas_anatomicas_list = []

        # Si hay subtipos, usarlos; si no, usar el valor por defecto
        opciones_tipo_zona_especifica = zonas_anatomicas_list if zonas_anatomicas_list else default_list
        is_disabled = disabled_edit or not zonas_anatomicas_list
    
        if modo == "editar":
            try:
                idx_zona_espec = zonas_anatomicas_list.index(lesion_data["zona_especifica"])
            except ValueError:
                idx_zona_espec = 0
                
        zona_especifica = st.selectbox("Estructura anatómica", opciones_tipo_zona_especifica, index=idx_zona_espec, 
                                       key=f"subregion_{st.session_state['form_version']}", disabled=is_disabled,
                                       placeholder=placeholder)

    with col4:
        
        idx_tipos_lesion = 0
        if mecanismo_lesion:
            # Filtrar tipos compatibles
            mecanismo_id = mecanismos_df.loc[mecanismos_df["nombre"] == mecanismo_lesion, "id"].iloc[0]
            
            tipos_filtrados = tipos_lesion_df.merge(
                relacion_df[relacion_df["mecanismo_id"] == mecanismo_id],
                left_on="id",
                right_on="tipo_lesion_id",
                how="inner"
            )

            tipos_lesion_list = tipos_filtrados["nombre"].tolist()
        else:
            tipos_lesion_list = []

        # Si hay subtipos, usarlos; si no, usar el valor por defecto
        opciones_tipo_lesion = tipos_lesion_list if tipos_lesion_list else default_list
        is_disabled = disabled_edit or not tipos_lesion_list
    
        if modo == "editar":
            try:
                idx_tipos_lesion = tipos_lesion_list.index(lesion_data.get("tipo_lesion", ""))
            except ValueError:
                idx_tipos_lesion = 0

        tipo_lesion = st.selectbox("Tipo de lesión", opciones_tipo_lesion, index=idx_tipos_lesion, 
                                   disabled=is_disabled, help=lesion_help, placeholder=placeholder, 
                                   key=f"tipo_lesion_{st.session_state['form_version']}")
        
        lateralidad = st.selectbox("Lateralidad", lateralidades, index=idx_lateralidad, disabled=disabled_edit, placeholder=placeholder, key=f"lateralidad_{st.session_state['form_version']}")
    with col5:
        idx_tipo_especifico = 0

        if debe_deshabilitar_subtipo(mecanismo_lesion, tipo_lesion):
            opciones_tipo = default_list
            is_disabled = True
        else: 
            # Obtener lista de subtipos válidos según la selección
            if tipo_lesion:
                tipo_lesion_id = map_tipo_nombre_a_id.get(tipo_lesion)
                subtipos_filtrados = subtipos_df[subtipos_df["tipo_lesion_id"] == tipo_lesion_id]
                subtipos_list = subtipos_filtrados["nombre"].tolist()
            else:
                subtipos_list = []

            # Si hay subtipos, usarlos; si no, usar el valor por defecto
            opciones_tipo = subtipos_list if subtipos_list else default_list
            is_disabled = disabled_edit or not subtipos_list
        
            # Establecer índice en modo edición
            if modo == "editar" and subtipos_list:
                try:
                    idx_tipo_especifico = subtipos_list.index(lesion_data.get("tipo_especifico", ""))
                except ValueError:
                    idx_tipo_especifico = 0

        tipo_especifico = st.selectbox("Tipo específico", opciones_tipo, index=idx_tipo_especifico, disabled=is_disabled, help=lesion_help, placeholder=placeholder, key=f"tipo_especifico_{st.session_state['form_version']}")

        ############################################

    diagnostico = st.text_area("Diagnóstico Médico", disabled=disabled_edit, value=diagnostico_text, key=f"diagnostico_{st.session_state['form_version']}")

    col1, col2, col3 = st.columns([1,2,2])    

    with col1:
        es_recidiva = st.checkbox("Es Recidiva", value=es_recidiva_value, disabled=disabled_edit, 
                                  key=f"es_recidiva_{st.session_state['form_version']}")
    with col2:
        tipo_recidiva = st.selectbox(
                "Tipo de recidiva (según tiempo desde el alta anterior)",
                options=tipos_recidiva if es_recidiva else ["NO APLICA"],
                index=idx_tipo_recidiva,
                disabled=True if not es_recidiva or disabled_edit else False,
                help="Clasificación basada en la fisiología de la reparación tisular y en la evidencia epidemiológica de la UEFA y el IOC.",
                placeholder=placeholder, key=f"tipo_recidiva_{st.session_state['form_version']}"
        )
    
    with col3:
        fecha_alta_diagnostico = st.date_input("Alta Deportiva (estimada)", fecha_alta_diagnostico_date, disabled=disabled_edit, key=f"fecha_alta_diagnostico_{st.session_state['form_version']}")  

    if (fecha_alta_diagnostico - fecha_lesion).days < 0:
        error = True
        st.warning(":material/warning: La fecha de alta no puede ser anterior a la fecha de registro.")
    else:
        # --- Cálculo automático de los días de baja ---
        dias_baja_estimado = max(0, (fecha_alta_diagnostico - fecha_lesion).days)

    #if modo == "editar":
        st.info(f":material/calendar_clock: Días estimados de baja: {dias_baja_estimado} día(s)")

        # --- Determinar gravedad automáticamente ---
        
        for nivel, (min_dias, max_dias) in gravedad_dias.items():
            if max_dias is None:
                if dias_baja_estimado >= min_dias:
                    gravedad = nivel
                    rango = (min_dias, max_dias)
                    break
            elif min_dias <= dias_baja_estimado <= max_dias:
                gravedad = nivel
                rango = (min_dias, max_dias)
                break

        if gravedad:
            #rango = gravedad_dias[gravedad]
            texto_rango = f":material/personal_injury: Severidad o Impacto de la lesión según los días de baja: **{gravedad}**"

            # if rango[1] is not None:
            #     texto_rango = texto_rango + f" entre {rango[0]} y {rango[1]} días."
            #     #dias_baja_estimado = f"{rango[0]}-{rango[1]}"
            # else:
            #     texto_rango = texto_rango + f" más de {rango[0]} días."
            #     #dias_baja_estimado = f">{rango[0]}"

            #if modo != "editar":    
            st.warning(f"{texto_rango}")

    #------------------------------      
    col1, col2 = st.columns([2,1])   
    with col1:
        tipo_tratamiento = st.multiselect("Tipo(s) de tratamiento", options=tratamientos, default=tratamientos_default, 
                                          placeholder="Selecciona uno o más", max_selections=5, disabled=disabled_edit, 
                                          key=f"tipo_tratamiento_{st.session_state['form_version']}")
    
    with col2:
        personal_reporta = st.text_input("Personal médico que reporta", value=personal_reporte_text, disabled=disabled_edit, 
                                         key=f"personal_reporta_{st.session_state['form_version']}")

    descripcion = st.text_area("Observaciones / Descripción de la lesión", value=descripcion_text, disabled=disabled_edit, 
                               key=f"descripcion_{st.session_state['form_version']}")
    
    ############## FIN LOGICA ##############

    if modo == "editar":
        st.divider()

        st.subheader("Evolución de :red[la lesión]")
        
        seguimiento = st.checkbox("Añadir seguimiento", disabled=disabled_evolution)

        if seguimiento and not disabled_evolution:
            disabled_evolution = False
        else:
            disabled_evolution = True

        col1, col2, col3 = st.columns([1,2,1])    
        
        with col1:
            fecha_control = st.date_input("Fecha de control", datetime.date.today(), disabled=disabled_evolution)
        with col2:
            tratamiento_aplicado = st.multiselect("Tratamiento Aplicado", tratamientos, placeholder="Selecciona uno o más", max_selections=5, disabled=disabled_evolution)
        with col3:
            personal_seguimiento = st.text_input("Personal médico", disabled=disabled_evolution)

        descripcion = st.text_area("Observaciones o incidencias", disabled=disabled_evolution)

        col1, col2, col3 = st.columns([1,1,2])    
        
        with col1:
            
            alta_medica = st.checkbox("Alta Médica", value=alta_medica_value, disabled=alta_medica_value or disabled_evolution)

            #fecha_alta = None
            if alta_medica:
                if not fecha_alta_medica:
                    fecha_alta_medica = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
                
                fecha_alta_medica = st.date_input("Fecha alta médica", value=fecha_alta_medica, disabled=alta_medica_value)

        with col2: 
            if alta_medica_value:
                alta_deportiva = st.checkbox("Alta Deportiva", value=alta_deportiva_value, disabled=disabled_evolution)

                if alta_deportiva:
                    if not fecha_alta_deportiva:
                        fecha_alta_deportiva = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
                
                    fecha_alta_deportiva = st.date_input("Fecha alta deportiva", value=fecha_alta_deportiva, disabled=disabled_evolution)

        if is_valid(fecha_alta_medica):
            #st.text(fecha_alta_medica)
            if (fecha_alta_medica - fecha_lesion).days < 0:
                error = True
                st.warning("⚠️ La fecha de alta médica no puede ser anterior a la fecha de registro.")
            else:
                dias_baja_reales = max(0, (fecha_alta_medica - fecha_lesion).days)
                st.info(f":material/calendar_clock: Días reales de baja médica: {dias_baja_reales} día(s)")
                descripcion = descripcion + "\n Alta Médica"
            
        if is_valid(fecha_alta_deportiva):
            if (fecha_alta_deportiva - fecha_alta_medica).days < 0:
                error = True
                st.warning("⚠️ La fecha de alta deportiva no puede ser anterior a la fecha de alta médica.")
            else:
                dias_baja_reales = max(0, (fecha_alta_deportiva - fecha_lesion).days)
                st.info(f":material/calendar_clock: Días reales de baja deportiva: {dias_baja_reales} día(s)")
                descripcion = descripcion + "\n Alta Deportiva"
            

        ####################################################################################
        if ("evolucion" in lesion_data and isinstance(lesion_data["evolucion"], list) and len(lesion_data["evolucion"]) > 0):
            st.divider()
            st.markdown("**Historial de sesiones**")
            st.dataframe(lesion_data["evolucion"])
            
        tratamiento_aplicado_str = ([t.upper() for t in tratamiento_aplicado] if isinstance(tratamiento_aplicado, list) else [])
        record_evolucion = {
            "fecha_control": fecha_control.strftime("%Y-%m-%d"),
            "tratamiento_aplicado": tratamiento_aplicado_str,
            "personal_seguimiento": personal_seguimiento,
            "observaciones": descripcion,
            "fecha_hora_registro": datetime.datetime.now().isoformat(),
            "usuario": st.session_state['auth']['username']
        }

    ############# PROCESAMIENTO Y GUARDADO #############  
    tratamientos_str = ([t.upper() for t in tipo_tratamiento] if isinstance(tipo_tratamiento, list) else [])

    if not lugar or not segmento or not zona_cuerpo or not tipo_lesion or not mecanismo_lesion:
        error = True

    # Construimos el diccionario de la lesión
    if modo == "nuevo":
        record = {
            "id_lesion": nuevo_id,
            "id_jugadora": id_jugadora,
            #"nombre": nombre_completo,
            "posicion": posicion,
            "fecha_lesion": fecha_str,
            "lugar": lugar.upper() if lugar else lugar,
            "segmento": segmento.upper() if segmento else segmento,
            "zona_cuerpo": zona_cuerpo.upper() if zona_cuerpo else zona_cuerpo,
            "zona_especifica": zona_especifica,
            "lateralidad": lateralidad,
            "tipo_lesion": tipo_lesion.upper() if tipo_lesion else tipo_lesion,
            "tipo_especifico": tipo_especifico.upper() if tipo_especifico else tipo_especifico,
            #"gravedad_clinica": gravedad_clinica,
            "es_recidiva": es_recidiva,
            "tipo_recidiva": tipo_recidiva,
            "dias_baja_estimado": dias_baja_estimado,
            "impacto_dias_baja_estimado": gravedad,
            "mecanismo_lesion": mecanismo_lesion.upper() if mecanismo_lesion else mecanismo_lesion,
            "tipo_tratamiento": tratamientos_str,
            "personal_reporta": personal_reporta,
            "fecha_alta_diagnostico": fecha_alta_diagnostico.strftime("%Y-%m-%d"),
            "fecha_alta_medica": None,
            "fecha_alta_deportiva": None,
            #"fecha_alta_lesion": fecha_alta_lesion.strftime("%Y-%m-%d"),
            "estado_lesion": "ACTIVO",
            "diagnostico": diagnostico,
            "descripcion": descripcion,
            "evolucion": [],
            "fecha_hora_registro": datetime.datetime.now().isoformat(),
            "usuario": st.session_state['auth']['username']
        }
    else:  # modo editar
        if "evolucion" not in lesion_data or not isinstance(lesion_data["evolucion"], list):
            lesion_data["evolucion"] = []
        
        lesion_data["evolucion"].append(record_evolucion)

        if alta_medica and fecha_alta_medica:
            lesion_data["fecha_alta_medica"] = fecha_alta_medica.strftime("%Y-%m-%d")
            lesion_data["fecha_alta_deportiva"] = None
        
        if lesion_data.get("fecha_alta_deportiva") is None and alta_medica_value:
            if alta_deportiva and fecha_alta_deportiva:
                lesion_data["fecha_alta_deportiva"] = fecha_alta_deportiva.strftime("%Y-%m-%d")
                lesion_data["estado_lesion"] = "INACTIVO"

        record = lesion_data

    if st.session_state["auth"]["rol"] == "developer":
        st.divider()
        #st.text(record)
        if st.checkbox("Previsualización"):
            preview_record(record)
            #st.caption(f"Datos almacenados en: {DATA_DIR}/registros.jsonl")

    if error:
        st.error("Existen campos obligatorios que debe seleccionar")

    ######################## GUARDADO Y REINICIO ########################

    # Inicializar control de estado del botón
    if "form_submitted" not in st.session_state:
        st.session_state.form_submitted = False

    # Determinar si el botón debe estar deshabilitado
    disabled_guardar = disabled_evolution or error or st.session_state.form_submitted

    submitted = st.button(
        "Guardar",
        disabled=disabled_guardar,
        type="primary"
    )

    if submitted:
        # Evitar dobles clics
        st.session_state.form_submitted = True
        st.session_state["form_version"] += 1

        # Guardado visual con spinner
        with st.spinner("Guardando registro..."):
            upsert_jsonl(record)
            time.sleep(0.8)
        # Obtener ID según el modo
        id_lesion = nuevo_id if modo == "nuevo" else lesion_data.get("id_lesion", "N/A")

        # Mensaje de confirmación (se muestra tras rerun)
        st.session_state["flash"] = f"✅ Registro {id_lesion} guardado correctamente en data/registros.jsonl"

        # Refrescar la interfaz
        st.rerun()

    # --- Mostrar mensaje flash tras guardar ---
    if st.session_state.get("flash"):
        st.success(st.session_state["flash"])
        st.session_state["flash"] = None
        st.session_state.form_submitted = False

        

def preview_record(record: dict) -> None:
    #st.subheader("Previsualización")
    # Header with key fields
    #jug = record.get("nombre", "-")
    fecha = record.get("fecha_hora", "-")
    posicion = record.get("posicion", "-")
    tipo = record.get("tipo_lesion", "-")
    #st.markdown(f"**Jugadora:** {jug}  |  **Fecha:** {fecha}  |  **Posicion:** {posicion}  |  **Tipo Lesión:** {tipo}")
    with st.expander("Ver registro JSON", expanded=False):
        st.code(json.dumps(record, ensure_ascii=False, indent=2), language="json")


def generar_id_lesion(nombre: str, id_jugadora: int, df: pd.DataFrame, fecha: str | None = None) -> str:
    """
    Genera un identificador único de lesión para una jugadora.
    Formato: <INICIALES><YYYYMMDD>-<INCREMENTAL>
    
    - nombre: Nombre completo de la jugadora
    - id_jugadora: ID numérico único de la jugadora
    - df: DataFrame con registros previos de lesiones
    - fecha: Fecha opcional (formato 'YYYYMMDD'). Si no se pasa, usa la actual.
    """
    # --- Obtener iniciales (todas las palabras) ---
    partes = nombre.strip().split()
    iniciales = "".join(p[0].upper() for p in partes if p)  # toma todas las iniciales

    # --- Fecha ---
    if fecha is None:
        fecha = datetime.datetime.now().strftime("%Y%m%d")

    #st.dataframe(df)
    #st.text(id_jugadora)
    if "id_jugadora" in df.columns:
        previas = df[df["id_jugadora"] == id_jugadora]
        numero = len(previas) + 1
    else:
        # Si no existe la columna, asumir que no hay lesiones previas
        numero = 1

    # --- Construir identificador ---
    return f"{iniciales}{fecha}-{numero}"

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
        st.metric("Total de Lesiones", total_lesiones)
    with col2:
        st.metric("Lesiones Activas", activas, f"{porcentaje_activas}%")
    with col3:
        st.metric("Días de Baja Promedio", f"{tiempo_promedio:.1f} días")
    with col4:
        st.metric("Recaídas", recidivas, f"{pct_recidivas}%")

def player_block_dux(jugadora_seleccionada: dict, unavailable="N/A"):
    """Muestra el bloque visual con la información principal de la jugadora."""

    # Validar jugadora seleccionada
    if not jugadora_seleccionada or not isinstance(jugadora_seleccionada, dict):
        st.info("Selecciona una jugadora para continuar.")
        st.stop()

    # Extraer información básica
    nombre = jugadora_seleccionada.get("nombre", unavailable).strip().upper()
    apellido = jugadora_seleccionada.get("apellido", "").strip().upper()
    nombre_completo = f"{nombre.capitalize()} {apellido.capitalize()}"
    id_jugadora = jugadora_seleccionada.get("identificacion", unavailable)
    posicion = jugadora_seleccionada.get("posicion", unavailable)
    pais = jugadora_seleccionada.get("pais", unavailable)
    fecha_nac = jugadora_seleccionada.get("fecha_nacimiento", unavailable)
    sexo = jugadora_seleccionada.get("sexo", "")
    competicion = jugadora_seleccionada.get("plantel", "")
    url_drive = jugadora_seleccionada.get("url", "")

    # Calcular edad
    try:
        fnac = datetime.datetime.strptime(fecha_nac, "%Y-%m-%d").date()
        hoy = datetime.date.today()
        edad = hoy.year - fnac.year - ((hoy.month, hoy.day) < (fnac.month, fnac.day))
    except Exception:
        edad = unavailable

    # Color temático
    #color = "violet" if sexo.upper() == "F" else "blue"

    # Icono de género
    if sexo.upper() == "F":
        genero_icono = ":material/girl:"
        profile_image = "female"
    elif sexo.upper() == "H":
        genero_icono = ":material/boy:"
        profile_image = "male"
    else:
        genero_icono = ""
        profile_image = "profile"

    # Bloque visual
    st.markdown(f"### {nombre_completo.title()} {genero_icono}")
    #st.markdown(f"##### **_:red[Identificación:]_** _{id_jugadora}_ | **_:red[País:]_** _{pais.upper()}_")

    col1, col2, col3 = st.columns([1.6, 2, 2])

    with col1:
        if pd.notna(url_drive) and url_drive and url_drive != "No Disponible":
            direct_url = get_drive_direct_url(url_drive)
            response = get_photo(direct_url)
            if response and response.status_code == 200 and 'image' in response.headers.get("Content-Type", ""):
                st.image(response.content, width=300)
            else:
                st.image(f"assets/images/{profile_image}.png", width=300)
        else:
            st.image(f"assets/images/{profile_image}.png", width=300)

    with col2:
        #st.markdown(f"**:material/sports_soccer: Competición:** {competicion}")
        #st.markdown(f"**:material/cake: Fecha Nac.:** {fecha_nac}")

        st.metric(label=f":red[:material/id_card: Identificación]", value=f"{id_jugadora}", border=True)
        st.metric(label=f":red[:material/sports_soccer: Plantel]", value=f"{competicion}", border=True)
        st.metric(label=f":red[:material/cake: F. Nacimiento]", value=f"{fecha_nac}", border=True)
                    
    with col3:
        #st.markdown(f"**:material/person: Posición:** {posicion.capitalize()}")
        #st.markdown(f"**:material/favorite: Edad:** {edad if edad != unavailable else 'N/A'} años")

        st.metric(label=f":red[:material/globe: País]", value=f"{pais.capitalize()}", border=True)
        st.metric(label=f":red[:material/person: Posición]", value=f"{posicion.capitalize()}", border=True)
        st.metric(label=f":red[:material/favorite: Edad]", value=f"{edad if edad != unavailable else 'N/A'} años", border=True)
          
    st.divider()

def main_metrics(records, modo="overview"):
    """
    Muestra métricas principales de lesiones según el modo:
    - 'overview': agrupa por periodo (semana/mes), muestra filtros y help en métricas.
    - 'reporte': usa todo el DataFrame sin agrupar ni filtros.
    """

    # --- Validación inicial ---
    if records.empty:    
        st.warning("No hay datos de lesiones disponibles.")
        st.stop()  

    # Convertir fecha y limpiar
    records["fecha_alta_diagnostico"] = pd.to_datetime(records["fecha_alta_diagnostico"], errors="coerce")

    ultimos = records.copy()
    articulo, periodo = "", ""

    # --- MODO OVERVIEW ---
    if modo == "overview":
        periodo = st.radio("Agrupar por:", ["Semana", "Mes"], horizontal=True)
        articulo = "la última" if periodo == "Semana" else "el último"

        if periodo == "Semana":
            records["periodo"] = records["fecha_alta_diagnostico"].dt.isocalendar().week
            ultimos = records[
                records["fecha_alta_diagnostico"]
                >= (records["fecha_alta_diagnostico"].max() - pd.Timedelta(days=7))
            ]
        else:
            records["periodo"] = records["fecha_alta_diagnostico"].dt.month
            ultimos = records[
                records["fecha_alta_diagnostico"]
                >= (records["fecha_alta_diagnostico"].max() - pd.Timedelta(days=30))
            ]

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
            "Total de lesiones registradas",
            total_lesiones,
            f"{delta_total:+.1f}%",
            chart_data=chart_total,
            chart_type="area",
            border=True,
            delta_color="normal",
            help=f"Variación del número total de lesiones comparado con {articulo} {periodo.lower()}."
            if help_texts else None,
        )
    with col2:
        st.metric(
            "Lesiones activas",
            activas,
            f"{delta_activas:+.1f}%",
            chart_data=chart_activas,
            chart_type="line",
            border=True,
            delta_color="inverse",
            help=f"Variación en las lesiones activas respecto a {articulo} {periodo.lower()}."
            if help_texts else None,
        )
    with col3:
        st.metric(
            "Días de recuperación promedio",
            promedio_dias_baja,
            f"{delta_dias:+.1f}%",
            chart_data=chart_dias,
            chart_type="area",
            border=True,
            delta_color="normal",
            help=f"Variación del tiempo promedio de recuperación por {periodo.lower()}."
            if help_texts else None,
        )
    with col4:
        st.metric(
            f"Zona más afectada: {zona_top}",
            f"{zona_count} casos",
            f"{delta_zona:+.1f}%",
            chart_data=chart_zonas,
            chart_type="bar",
            border=True,
            delta_color="inverse",
            help=f"Frecuencia de lesiones en {zona_top} comparado con {articulo} {periodo.lower()}."
            if help_texts else None,
        )

    return ultimos
