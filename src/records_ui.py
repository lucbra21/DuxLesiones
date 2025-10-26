import time
import streamlit as st
import datetime
from src.io_files import load_catalog_list
import pandas as pd

import pandas as pd
import numpy as np
import json

from src.util import (debe_deshabilitar_subtipo, is_valid, parse_fecha, get_gravedad_por_dias, get_normalized_treatment)

from src.db_catalogs import load_catalog_list_db
from src.db_records import save_lesion
from src.ui_components import preview_record

def view_registro_lesion(modo: str = "nuevo", jugadora_info: str = None, lesion_data = None) -> None:

    #st.dataframe(lesion_data)
    error = False
    #st.text(f"Error: {error}")

    placeholder="Selecciona una opción"
    default_list=["NO APLICA"]

    if "form_version" not in st.session_state:
        st.session_state["form_version"] = 0

    disabled_edit = False
    if modo == "editar":
        disabled_edit = True

    disabled_evolution = False
    
    if lesion_data and lesion_data["estado_lesion"] == "INACTIVO":
        fecha_alta_medica = lesion_data.get("fecha_alta_medica", None)
        fecha_alta_deportiva = lesion_data.get("fecha_alta_deportiva", None)
        
        disabled_evolution = True
        st.warning(f"La lesión esta **'Inactiva'**, **fecha de alta médica:** {fecha_alta_medica}, **fecha de alta deportiva:** {fecha_alta_deportiva}. No se pueden editar los datos")

    lesion_help ="Lesiones agrupadas según el tejido afectado y mecanismo (criterios FIFA/UEFA)."
    
    ############## BD DATA ##############
    segmentos_corporales_df = load_catalog_list_db("segmentos_corporales", as_df=True)
    map_segmentos_nombre_a_id = dict(zip(segmentos_corporales_df["nombre"], segmentos_corporales_df["id"]))
    segmentos_corporales_list = segmentos_corporales_df["nombre"].tolist()

    zonas_segmento_df = load_catalog_list_db("zonas_segmento", as_df=True)
    map_zonas_segmento_nombre_a_id = dict(zip(zonas_segmento_df["nombre"], zonas_segmento_df["id"]))

    zonas_anatomicas_df = load_catalog_list_db("zonas_anatomicas", as_df=True)
    map_zonas_anatomicas_nombre_a_id = dict(zip(zonas_anatomicas_df["nombre"], zonas_anatomicas_df["id"]))

    mecanismos_df = load_catalog_list_db("mecanismos", as_df=True)
    map_mecanismos_nombre_a_id = dict(zip(mecanismos_df["nombre"], mecanismos_df["id"]))
    mecanismo_list = mecanismos_df["nombre"].tolist()

    tipos_lesion_df = load_catalog_list_db("tipo_lesion", as_df=True)
    map_tipos_lesion_nombre_a_id = dict(zip(tipos_lesion_df["nombre"], tipos_lesion_df["id"]))
    map_tipo_nombre_a_id = dict(zip(tipos_lesion_df["nombre"], tipos_lesion_df["id"]))

    subtipos_df = load_catalog_list_db("tipo_especifico_lesion", as_df=True)
    map_subtipos_nombre_a_id = dict(zip(subtipos_df["nombre"], subtipos_df["id"]))

    relacion_df = load_catalog_list_db("mecanismo_tipo_lesion", as_df=True)
    #map_relacion_df_nombre_a_id = dict(zip(tipos_lesion_df["nombre"], tipos_lesion_df["id"]))

    tratamientos = load_catalog_list_db("tratamientos", as_df=True)
    tratamientos_list = tratamientos["nombre"].tolist()

    lugares_df = load_catalog_list_db("lugares", as_df=True)
    map_lugares_nombre_a_id = dict(zip(lugares_df["nombre"], lugares_df["id"]))
    lugares_list = lugares_df["nombre"].tolist()

    lateralidades = load_catalog_list("lateralidades")
    tipos_recidiva = load_catalog_list("tipos_recidiva")

    df_gravedad = load_catalog_list("gravedad", as_df=True)
    gravedad_dias = (df_gravedad.set_index("nombre")[["dias_min", "dias_max"]].apply(tuple, axis=1).to_dict())
    ############## BD DATA ##############

    if modo == "editar":

        fecha_lesion_date = parse_fecha(lesion_data["fecha_lesion"])
        fecha_alta_diagnostico_date = parse_fecha(lesion_data["fecha_alta_diagnostico"])

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

        diagnostico_text = lesion_data.get("diagnostico", "")
        descripcion_text = lesion_data.get("descripcion", "")
        personal_reporte_text = lesion_data.get("personal_reporta", "")
        dias_baja_estimado = int(lesion_data.get("dias_baja_estimado", 0))
        tratamientos_default = get_normalized_treatment(lesion_data)
        es_recidiva_value = lesion_data.get("es_recidiva")

        try:
            idx_segmento = None
            if is_valid(lesion_data.get("segmento")):
                idx_segmento = segmentos_corporales_list.index(lesion_data["segmento"])
        except ValueError:
            segmentos_corporales_list.append(lesion_data["segmento"])
            idx_segmento = segmentos_corporales_list.index(lesion_data["segmento"])

        try:
            idx_lugar = None
            if is_valid(lesion_data.get("lugar")):
                idx_lugar = lugares_list.index(lesion_data["lugar"])
        except ValueError:
            lugares_list.append(lesion_data["lugar"])
            idx_lugar = lugares_list.index(lesion_data["lugar"])

        try:
            idx_mecanismo = None
            if is_valid(lesion_data.get("mecanismo")):
                idx_mecanismo = mecanismo_list.index(lesion_data["mecanismo"])
        except ValueError:
            mecanismo_list.append(lesion_data["mecanismo"])
            idx_mecanismo = mecanismo_list.index(lesion_data["mecanismo"])

        try:
            idx_lateralidad = None
            if is_valid(lesion_data.get("lateralidad")):
                idx_lateralidad = lateralidades.index(lesion_data["lateralidad"])
        except ValueError:
            lateralidades.append(lesion_data["lateralidad"])
            idx_lateralidad = lateralidades.index(lesion_data["lateralidad"])

        try:
            idx_tipo_recidiva = None
            
            if is_valid(lesion_data.get("tipo_recidiva")):
                idx_tipo_recidiva = tipos_recidiva.index(lesion_data["tipo_recidiva"])
                #st.text(lesion_data.get("tipo_recidiva"))
                #st.text(f"idx_tipo_recidiva: {idx_tipo_recidiva}")
        except ValueError:
            tipos_recidiva.append(lesion_data["tipo_recidiva"])
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
        lugar = st.selectbox("Lugar", lugares_list, index=idx_lugar, disabled=disabled_edit, placeholder=placeholder, 
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
                #st.text(f'tipo_lesion: {lesion_data.get("tipo_lesion", "")}')
                #st.dataframe(tipos_lesion_list)
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
        fecha_alta_diagnostico = st.date_input("Alta Deportiva (estimada)", fecha_alta_diagnostico_date, disabled=disabled_edit, 
                                               key=f"fecha_alta_diagnostico_{st.session_state['form_version']}")  

    if (fecha_alta_diagnostico - fecha_lesion).days < 0:
        error = True
        #st.text(f"Error fecha_alta_diagnostico - fecha_lesion: {error}")
        st.warning(":material/warning: La fecha de alta no puede ser anterior a la fecha de registro.")
    else:
        # --- Cálculo automático de los días de baja ---
        dias_baja_estimado = max(0, (fecha_alta_diagnostico - fecha_lesion).days)

    #if modo == "editar":
        st.info(f":material/calendar_clock: Días estimados de baja: {dias_baja_estimado} día(s)")

        # --- Determinar gravedad automáticamente ---
        gravedad, rango = get_gravedad_por_dias(dias_baja_estimado, gravedad_dias)

        if gravedad:
            texto_rango = f":material/personal_injury: Severidad o Impacto de la lesión según los días de baja: **{gravedad}**" 
            st.warning(f"{texto_rango}")

    #------------------------------      
    col1, col2 = st.columns([2,1])   
    with col1:
        tipo_tratamiento = st.multiselect("Tipo(s) de tratamiento", options=tratamientos_list, default=tratamientos_default, 
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
        
        seguimiento = st.checkbox("Añadir seguimiento", disabled=disabled_evolution, 
                                  key=f"seguimiento_{st.session_state['form_version']}")

        if seguimiento and not disabled_evolution:
            disabled_evolution = False
        else:
            disabled_evolution = True

        col1, col2, col3 = st.columns([1,2,1])    
        
        with col1:
            fecha_control = st.date_input("Fecha de control", datetime.date.today(), disabled=disabled_evolution)
        with col2:
            tratamiento_aplicado = st.multiselect("Tratamiento Aplicado", tratamientos_list, placeholder="Selecciona uno o más", 
                                                  max_selections=15, disabled=disabled_evolution,
                                                  key=f"tratamiento_aplicado_{st.session_state['form_version']}")
        with col3:
            personal_seguimiento = st.text_input("Personal médico", disabled=disabled_evolution,
                                                 key=f"personal_seguimiento_{st.session_state['form_version']}")

        incidencias = st.text_area("Observaciones o incidencias", disabled=disabled_evolution,
                                   key=f"incidencias_{st.session_state['form_version']}")

        col1, col2, col3 = st.columns([1,1,2])    
        
        with col1:            
            alta_medica = st.checkbox("Alta Médica", value=alta_medica_value, disabled=alta_medica_value or disabled_evolution)

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
                #st.text(f"Error fecha_alta_medica - fecha_lesion): {error}")
                st.warning(":material/warning: La fecha de alta médica no puede ser anterior a la fecha de registro.")
            else:
                dias_baja_reales = max(0, (fecha_alta_medica - fecha_lesion).days)
                st.info(f":material/calendar_clock: Días reales de baja médica: {dias_baja_reales} día(s)")
                #incidencias = incidencias + "\n Alta Médica"
            
        if is_valid(fecha_alta_deportiva):
            if (fecha_alta_deportiva - fecha_alta_medica).days < 0:
                error = True
                #st.text(f"Error fecha_alta_deportiva - fecha_alta_medica: {error}")
                st.warning(":material/warning: La fecha de alta deportiva no puede ser anterior a la fecha de alta médica.")
            else:
                dias_baja_reales = max(0, (fecha_alta_deportiva - fecha_lesion).days)
                st.info(f":material/calendar_clock: Días reales de baja deportiva: {dias_baja_reales} día(s)")
                #incidencias = incidencias + "\n Alta Deportiva"
            

        ####################################################################################
        show_evolucion_historial(lesion_data)

        if seguimiento and (not personal_seguimiento or not personal_seguimiento.strip()):
            error = True

        tratamiento_aplicado_str = ([t.upper() for t in tratamiento_aplicado] if isinstance(tratamiento_aplicado, list) else [])
        
        record_evolucion = {
            "fecha_control": fecha_control.strftime("%Y-%m-%d"),
            "tratamiento_aplicado": tratamiento_aplicado_str,
            "personal_seguimiento": personal_seguimiento,
            "observaciones": incidencias,
            "fecha_hora_registro": datetime.datetime.now().isoformat(),
            "usuario": st.session_state['auth']['username']
        }

    ############# PROCESAMIENTO Y GUARDADO #############  
    tratamientos_str = ([t.upper() for t in tipo_tratamiento] if isinstance(tipo_tratamiento, list) else [])

    if not lugar or not segmento or not zona_cuerpo or not tipo_lesion or not mecanismo_lesion:
        error = True
        #st.text(f"Error not lugar or not segmento or not zona_cuerpo or not tipo_lesion or not mecanismo_lesion: {error}")

    #st.text(modo)
    # Construimos el diccionario de la lesión
    if modo == "nuevo":

        lugar_id = map_lugares_nombre_a_id.get(lugar)
        segmento_id = map_segmentos_nombre_a_id.get(segmento)
        zona_cuerpo_id = map_zonas_segmento_nombre_a_id.get(zona_cuerpo)
        zona_especifica_id = map_zonas_anatomicas_nombre_a_id.get(zona_especifica)

        tipo_lesion_id = map_tipo_nombre_a_id.get(tipo_lesion)
        tipo_especifico_id = map_subtipos_nombre_a_id.get(tipo_especifico)
        mecanismo_id = map_mecanismos_nombre_a_id.get(mecanismo_lesion)

        record = {
            "id_lesion": None,
            "id_jugadora": jugadora_info["id_jugadora"],
            "nombre": jugadora_info["nombre_completo"],
            "posicion": jugadora_info["posicion"].upper(),
            "fecha_lesion": fecha_str,
            "lugar_id": lugar_id,
            "segmento_id": segmento_id,
            "zona_cuerpo_id": zona_cuerpo_id,
            "zona_especifica_id": zona_especifica_id,
            "lateralidad": lateralidad,
            "tipo_lesion_id": tipo_lesion_id,
            "tipo_especifico_id": tipo_especifico_id,
            #"gravedad_clinica": gravedad_clinica,
            "es_recidiva": es_recidiva,
            "tipo_recidiva": tipo_recidiva,
            "dias_baja_estimado": dias_baja_estimado,
            "impacto_dias_baja_estimado": gravedad,
            "mecanismo_id": mecanismo_id,
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
    else:  
        # modo editar
        if "evolucion" not in lesion_data or not isinstance(lesion_data["evolucion"], list):
            lesion_data["evolucion"] = []
        
        tiene_datos = any([
            record_evolucion["tratamiento_aplicado"],  # lista con elementos
            record_evolucion["personal_seguimiento"],
            record_evolucion["observaciones"]
        ])

        if tiene_datos:
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

    #st.text(st.session_state.form_submitted)
    #st.text(f"Error: {error}")
    ######################## GUARDADO Y REINICIO ########################
    #st.session_state.form_submitted = False
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

        try:
            with st.spinner("Guardando registro..."):
                success = save_lesion(record, modo)

                if success:
                    # Si el guardado fue exitoso
                    
                    st.session_state["flash"] = f":material/done_all: Lesión {record['id_lesion']} guardada correctamente."
                    time.sleep(5)
                    st.rerun()
                else:
                    # Si hubo error en save_lesion, desbloquear botón
                    st.warning(":material/warning: No se pudo guardar la lesión. Revisa los datos e inténtalo nuevamente.")
                    st.session_state.form_submitted = False

        except Exception as e:
            # Captura cualquier error inesperado
            st.error(f":material/warning: Error inesperado al guardar la lesión: {e}")
            st.session_state.form_submitted = False

# --- Mostrar mensaje flash tras guardar ---
if st.session_state.get("flash"):
    st.success(st.session_state["flash"])
    st.session_state["flash"] = None
    st.session_state.form_submitted = False

def show_evolucion_historial(lesion_data: dict):
    """
    Muestra el historial de evolución de una lesión a partir del campo JSON 'evolucion' almacenado en la base de datos.
    
    Args:
        lesion_data (dict): Diccionario con la información de la lesión. 
                            Debe incluir el campo 'evolucion' (LONGTEXT JSON válido o lista).
    """

    evol_raw = lesion_data.get("evolucion")
    
    # 1. Decodificar según el tipo recibido
    if not evol_raw:
        evolucion_list = []
    elif isinstance(evol_raw, str):
        try:
            evolucion_list = json.loads(evol_raw)
        except json.JSONDecodeError:
            st.warning(":material/warning: Error al decodificar el campo 'evolucion'.")
            evolucion_list = []
    elif isinstance(evol_raw, list):
        evolucion_list = evol_raw
    else:
        st.warning(":material/warning: Formato desconocido en el campo 'evolucion'.")
        evolucion_list = []

    # 2. Validar que sea una lista con registros
    if not isinstance(evolucion_list, list) or len(evolucion_list) == 0:
        st.info("Sin registros de evolución disponibles.")
        return

    # 3. Convertir a DataFrame para mostrarlo en tabla
    df_evol = pd.DataFrame(evolucion_list)
    
    # 4. Formatear columnas si existen
    if "fecha_control" in df_evol.columns:
        df_evol["fecha_control"] = pd.to_datetime(df_evol["fecha_control"], errors="coerce")
        df_evol = df_evol.sort_values("fecha_control", ascending=False)

    if "tratamiento_aplicado" in df_evol.columns:
        df_evol["tratamiento_aplicado"] = df_evol["tratamiento_aplicado"].apply(
            lambda x: ", ".join(x) if isinstance(x, list) else x
        )

    # 5. Reordenar columnas para mejor lectura
    columnas_orden = [
        c for c in ["fecha_control", "tratamiento_aplicado", "personal_seguimiento", "observaciones", "usuario", "fecha_hora_registro"]
        if c in df_evol.columns
    ]
    #st.dataframe(df_evol)
    df_evol = df_evol[columnas_orden]

    # 6. Mostrar el historial
    st.divider()
    st.markdown("**Historial de sesiones**")
    st.dataframe(df_evol)
