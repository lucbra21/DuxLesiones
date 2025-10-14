import streamlit as st
import datetime
from src.io_files import load_jugadoras, upsert_jsonl, load_competiciones, get_records_df
import pandas as pd


def data_filters():
    # Lista de jugadoras predefinidas
    jug_df, jug_error = load_jugadoras()
    comp_df, comp_error = load_competiciones()
    
    # Organiza el formulario en columnas
    col1, col2, col3 = st.columns([2,1,2])

    with col1:
        competiciones_options = comp_df.to_dict("records")
        competicion = st.selectbox(
            "Competición",
            options=competiciones_options,
            format_func=lambda x: f'{x["nombre"]} ({x["codigo"]})',
            placeholder="Seleccione una Competición",
            index=3
        )
        
    with col2:
        posicion = st.selectbox("Posición", ["PORTERA", "DEFENSA", "CENTRO", "DELANTERA"],
        placeholder="Seleccione una Posición",
        index=None
        )
        
    with col3:
        if competicion:
            codigo_competicion = competicion["codigo"]
            jug_df_filtrado = jug_df[jug_df["competicion"] == codigo_competicion]

            # Convertir el DataFrame filtrado a lista de opciones
            jugadoras_filtradas = jug_df_filtrado
        else:
            jugadoras_filtradas = jug_df

        if posicion:
            jugadoras_filtradas = jugadoras_filtradas[jugadoras_filtradas["posicion"] == posicion]

        # Convertir el DataFrame filtrado a lista de opciones
        jugadoras_filtradas = jugadoras_filtradas.to_dict("records")

        # La nueva columna para el nombre de la jugadora
        jugadora_seleccionada = st.selectbox(
            "Jugadora",
            options=jugadoras_filtradas,
            format_func=lambda x: f'{jugadoras_filtradas.index(x) + 1} - {x["nombre"]} {x["apellido"]}',
            placeholder="Seleccione una Jugadora",
            index=None
        )
    return jugadora_seleccionada, posicion

def view_registro_lesion(modo: str = "nuevo", jugadora_seleccionada: str = None, posicion: str = None, lesion_data = None) -> None:

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
        disabled_evolution = True
        st.warning("La lesión está inactiva. No se pueden editar los datos")

    lesion_help ="Lesiones agrupadas según el tejido afectado y mecanismo (criterios FIFA/UEFA)."
    # Diccionario principal → subcategorías
    zonas_anatomicas = {
        "MUSLO": ["ISQUIOTIBIALES", "CUÁDRICEPS", "ADUCTORES"],
        "PIERNA": ["GEMELOS", "SÓLEO", "TIBIAL ANTERIOR"],
        "RODILLA": [],
        "TOBILLO": [],
        "PIE": [],
        "CADERA": [],
        "PELVIS": [],
        "COLUMNA LUMBAR": [],
        "HOMBRO": [],
        "BRAZO": [],
        "CODO": [],
        "ANTEBRAZO": [],
        "MUÑECA": [],
        "MANO": [],
        "CABEZA": [],
        "CUELLO": [],
        "OTRO": []
    }

    tratamientos = [
        "CRIOTERAPIA",
        "TERMOTERAPIA",
        "ELECTROTERAPIA",
        "MASOTERAPIA / DRENAJE",
        "PUNCIÓN SECA",
        "EJERCICIOS DE MOVILIDAD",
        "EJERCICIOS DE FUERZA",
        "TRABAJO PROPIOCEPTIVO",
        "TRABAJO DE CAMPO",
        "REEDUCACIÓN TÉCNICA / RETORNO PROGRESIVO"
    ]

    lugares = ["ENTRENAMIENTO", "PARTIDO", "GIMNASIO", "OTRO"]
    mecanismos = ["SIN CONTACTO", "CON CONTACTO", "SOBRECARGA O MICROTRAUMA REPETITIVO", "TORSIÓN O DESEQUILIBRIO", "GOLPE DIRECTO"]
    lateralidades = ["DERECHA", "IZQUIERDA", "BILATERAL"]
    #tipos_lesion = ["CONTUSIÓN", "DISTENSIÓN MUSCULAR", "ESGUINCE", "FRACTURA", "LACERACIÓN", "LESIÓN ARTICULAR", "LESIÓN LIGAMENTARIA", "LUXACIÓN / SUBLUXACIÓN", "ROTURA FIBRILAR", "TENDINOPATÍA", "OTRA"]

    tipos_lesion = {
        "MUSCULAR": ["CONTUSIÓN MUSCULAR", "DISTENSIÓN", "ROTURA FIBRILAR"],
        "TENDINOSA": ["TENDINOPATÍA", "ROTURA TENDINOSA"],
        "LIGAMENTARIA / ARTICULAR": ["ESGUINCE", "LESIÓN LIGAMENTARIA", "LUXACIÓN / SUBLUXACIÓN", "LESIÓN ARTICULAR"],
        "ÓSEA": ["FRACTURA"],
        "TRAUMÁTICA / SUPERFICIAL": ["LACERACIÓN", "CONTUSIÓN SUPERFICIAL"],
        "OTRAS": ["OTRA"]
    }

    gravedad_dias = {
        "LEVE (GRADO I)": (1, 3),
        "MODERADA (GRADO II)": (4, 7),
        "GRAVE (GRADO III)": (8, 28),
        "MUY GRAVE": (29, None)
    }
    
    if modo == "editar":
        fecha_alta_medica = None
        fecha_lesion_date = datetime.date.fromisoformat(lesion_data["fecha_lesion"])
        fecha_alta_diagnostico_date = datetime.date.fromisoformat(lesion_data["fecha_alta_diagnostico"])
        diagnostico_text = lesion_data.get("diagnostico", "")
        descripcion_text = lesion_data.get("descripcion", "")
        personal_reporte_text = lesion_data.get("personal_reporta", "")
        dias_baja = int(lesion_data.get("dias_baja_estimado", 0))
        fecha_alta_lesion = lesion_data.get("fecha_alta_lesion", None)
        tratamientos_selected = lesion_data.get("tipo_tratamiento", [])

        for m in tratamientos_selected:
            if m not in tratamientos:
                tratamientos.append(m)

        tratamientos_default=[p for p in tratamientos_selected if p in tratamientos]

        try:
            idx_gravedad = list(gravedad_dias.keys()).index(lesion_data["gravedad"])
        except ValueError:
            idx_gravedad = 0 

        if fecha_alta_lesion:
            alta_medica_value = True
        else:
            fecha_alta_lesion = datetime.datetime.now().strftime("%Y-%m-%d")
            alta_medica_value = False

        try:
            #st.text(lesion_data["zona_cuerpo"])
            idx_zonas = list(zonas_anatomicas.keys()).index(lesion_data["zona_cuerpo"])
        except ValueError:
            zonas_anatomicas.setdefault(lesion_data["zona_cuerpo"], [])
            idx_zonas = list(zonas_anatomicas.keys()).index(lesion_data["zona_cuerpo"]) 

        try:
            idx_lugar = lugares.index(lesion_data["lugar"])
        except ValueError:
            lugares.append(lesion_data["lugar"])
            idx_lugar = lugares.index(lesion_data["lugar"])

        try:
            idx_mecanismo = mecanismos.index(lesion_data["mecanismo_lesion"])
        except ValueError:
            mecanismos.append(lesion_data["mecanismo_lesion"])
            idx_mecanismo = mecanismos.index(lesion_data["mecanismo_lesion"])

        try:
            idx_lateralidad = lateralidades.index(lesion_data["lateralidad"])
        except ValueError:
            lateralidades.append(lesion_data["lateralidad"])
            idx_lateralidad = lateralidades.index(lesion_data["lateralidad"])

        try:
            idx_tipos_lesion = list(tipos_lesion.keys()).index(lesion_data["tipo_lesion"])
        except ValueError:
            tipos_lesion.setdefault(lesion_data["tipo_lesion"], [])
            idx_tipos_lesion = list(tipos_lesion.keys()).index(lesion_data["tipo_lesion"])

        try:
            idx_gravedad = list(gravedad_dias.keys()).index(lesion_data["gravedad"])
        except ValueError:
            idx_gravedad = 0 

            # Añadir dinámicamente los que no existan
            for m in lesion_data["mecanismo_lesion"]:
                if m not in mecanismos:
                    mecanismos.append(m)

            st.text(mecanismos)

    else:
        fecha_lesion_date = datetime.date.today()
        fecha_alta_diagnostico_date = datetime.date.today()
        idx_zonas = 0 
        idx_lugar = 0 
        idx_mecanismo = 0 
        idx_lateralidad = 0 
        idx_tipos_lesion = 0 
        idx_gravedad = 0 
        idx_zona_espec = 0 
        diagnostico_text = ""
        descripcion_text = ""
        personal_reporte_text = ""
        dias_baja = 0
        tratamientos_default = []
        idx_tipo_especifico = 0
        
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        fecha_lesion = st.date_input("Fecha de la lesión", fecha_lesion_date, disabled=disabled_edit)
        fecha_str = fecha_lesion.strftime("%Y-%m-%d")
        zona_cuerpo = st.selectbox("Zona del cuerpo", list(zonas_anatomicas.keys()), index=idx_zonas, disabled=disabled_edit, accept_new_options=True)
    with col2:
        lugar = st.selectbox("Lugar", lugares, index=idx_lugar, disabled=disabled_edit, accept_new_options=True)

        subregiones = zonas_anatomicas.get(zona_cuerpo, [])
        if subregiones:
            idx_zona_espec = 0 
            if modo == "editar":
                try:
                    idx_zona_espec = subregiones.index(lesion_data["zona_especifica"])
                except ValueError:
                    idx_zona_espec = 0
                
            zona_especifica = st.selectbox("Región anatómica específica:", subregiones, index=idx_zona_espec, key="subregion", disabled=disabled_edit)
        else:
            zona_especifica = st.selectbox(
                "Región anatómica específica:",
                ["NO APLICA"],
                key="subregion",
                disabled=True
            )
    with col3:
        mecanismo_lesion = st.selectbox("Mecanismo de lesión", mecanismos, index=idx_mecanismo, disabled=disabled_edit, accept_new_options=True)
        lateralidad = st.selectbox("Lateralidad", lateralidades, index=idx_lateralidad, disabled=disabled_edit)
    with col4:
        tipo_lesion = st.selectbox("Tipo de lesión", list(tipos_lesion.keys()), index=idx_tipos_lesion, disabled=disabled_edit, accept_new_options=True, help=lesion_help)
        
        gravedad = st.selectbox(
            "Gravedad",
            list(gravedad_dias.keys()),
            help="Clasificación basada en el estándar UEFA (Fuller et al., 2006)",
            index=idx_gravedad,
            disabled=disabled_edit
        )  
    with col5:
        subtipos = tipos_lesion.get(tipo_lesion, [])

        if modo == "editar":
            try:
                idx_tipo_especifico = subtipos.index(lesion_data["tipo_especifico"])
            except ValueError:
                idx_tipo_especifico = 0
        tipo_especifico = st.selectbox("Tipo específico", subtipos, index=idx_tipo_especifico, disabled=disabled_edit, help=lesion_help)


    rango = gravedad_dias[gravedad]
    texto_rango = ":material/calendar_clock: **Duración estimada de baja:**"

    if rango[1] is not None:
        texto_rango = texto_rango + f" entre {rango[0]} y {rango[1]} días."
    else:
        texto_rango = f":material/calendar_clock: **Duración estimada de baja:** más de {rango[0]} días."
        
    if modo != "editar":
        st.info(f"{texto_rango}")

    diagnostico = st.text_area("Diagnóstico Médico",value=diagnostico_text, disabled=disabled_edit)

    col1, col2, col3, col4 = st.columns([2,1,1,1.5])    

    with col1:
        tipo_tratamiento = st.multiselect("Tipo(s) de tratamiento", options=tratamientos, default=tratamientos_default, placeholder="Selecciona uno o más", max_selections=5, disabled=disabled_edit, accept_new_options=True)
    with col2:
        dias_baja_estimado = st.number_input("Días de baja (estimado)", min_value=0, value=dias_baja, disabled=disabled_edit)
    with col3:
        fecha_alta_diagnostico = st.date_input("Fecha de alta (estimada)", fecha_alta_diagnostico_date, disabled=disabled_edit)  
    with col4:
        personal_reporta = st.text_input("Personal médico que reporta", value=personal_reporte_text, disabled=disabled_edit)

    descripcion = st.text_area("Observaciones / Descripción de la lesión", value=descripcion_text, disabled=disabled_edit)
    
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

        col1, col2, col3 = st.columns([1,2,2])    
        
        with col1:
            alta_medica = st.checkbox("Alta Médica", value=alta_medica_value, disabled=disabled_evolution)

            #fecha_alta = None
            if alta_medica:

                fecha_alta_medica = st.date_input("Fecha alta", fecha_alta_lesion, disabled=disabled_evolution)

                #if fecha_alta_lesion:
                #    st.markdown(f":green[**Fecha de Alta Médica: {fecha_alta_lesion}**]")
                #else:
                #    fecha_alta_lesion = datetime.datetime.now().strftime("%Y-%m-%d")
                #    st.markdown(f":green[**Fecha de Alta Médica: {fecha_alta_lesion}**]")

        if ("evolucion" in lesion_data and isinstance(lesion_data["evolucion"], list) and len(lesion_data["evolucion"]) > 0):
            st.divider()
            st.markdown("**Historial de sesiones**")
            st.dataframe(lesion_data["evolucion"])
            
        tratamiento_aplicado_str = ([t.upper() for t in tratamiento_aplicado] if isinstance(tratamiento_aplicado, list) else [])
        record_evolucion = {
            "fecha_control": fecha_control.strftime("%Y-%m-%d"),
            "tratamiento_aplicado": tratamiento_aplicado_str,
            "personal_seguimiento": personal_seguimiento,
            "descripcion": descripcion,
            "fecha_hora_registro": datetime.datetime.now().isoformat()
        }

    ############# PROCESAMIENTO Y GUARDADO #############  
    tratamientos_str = ([t.upper() for t in tipo_tratamiento] if isinstance(tipo_tratamiento, list) else [])

    # Construimos el diccionario de la lesión
    if modo == "nuevo":
        record = {
            "id_lesion": nuevo_id,
            "id_jugadora": id_jugadora,
            #"nombre": nombre_completo,
            "posicion": posicion,
            "fecha_lesion": fecha_str,
            "lugar": lugar.upper(),
            "zona_cuerpo": zona_cuerpo.upper(),
            "zona_especifica": zona_especifica,
            "lateralidad": lateralidad.upper(),
            "tipo_lesion": tipo_lesion.upper(),
            "tipo_especifico": tipo_especifico.upper(),
            "gravedad": gravedad,
            "dias_baja_estimado": dias_baja_estimado,
            "mecanismo_lesion": mecanismo_lesion.upper(),
            "tipo_tratamiento": tratamientos_str,
            "personal_reporta": personal_reporta,
            "fecha_alta_diagnostico": fecha_alta_diagnostico.strftime("%Y-%m-%d"),
            "fecha_alta_lesion": None,
            #"fecha_alta_lesion": fecha_alta_lesion.strftime("%Y-%m-%d"),
            "estado_lesion": "ACTIVO",
            "diagnostico": diagnostico,
            "descripcion": descripcion,
            "evolucion": [],
            "fecha_hora_registro": datetime.datetime.now().isoformat()
        }
    else:  # modo editar
        if "evolucion" not in lesion_data or not isinstance(lesion_data["evolucion"], list):
            lesion_data["evolucion"] = []
        
        lesion_data["evolucion"].append(record_evolucion)
        
        if lesion_data.get("fecha_alta") is None and alta_medica and fecha_alta_medica:
            lesion_data["fecha_alta_lesion"] = fecha_alta_medica.strftime("%Y-%m-%d")
            lesion_data["estado_lesion"] = "INACTIVO"

        record = lesion_data

    if not disabled_evolution:
        st.divider()
        #st.text(record)
        if st.checkbox("Previsualización"):
            preview_record(record)
            #st.caption(f"Datos almacenados en: {DATA_DIR}/registros.jsonl")

    submitted = st.button("Guardar", disabled=disabled_evolution)
    if submitted:
        if jugadora_seleccionada == 'Seleccionar Jugadora':
            st.error("Por favor, selecciona una jugadora.")
            return
        
        upsert_jsonl(record)

        if modo == "nuevo":
            id_lesion = nuevo_id
        else:
            id_lesion = lesion_data.get("id_lesion", "N/A")
        # Set flash message to show after rerun
        st.session_state["flash"] = f"Registro {id_lesion} guardado/actualizado correctamente en data/registros.jsonl"
        # Clear form state by reloading
        st.rerun()

    # Show flash message if present (e.g., after saving)
    if st.session_state.get("flash"):
        st.success(st.session_state["flash"])
        st.session_state["flash"] = None

def preview_record(record: dict) -> None:
    #st.subheader("Previsualización")
    # Header with key fields
    #jug = record.get("nombre", "-")
    fecha = record.get("fecha_hora", "-")
    posicion = record.get("posicion", "-")
    tipo = record.get("tipo_lesion", "-")
    #st.markdown(f"**Jugadora:** {jug}  |  **Fecha:** {fecha}  |  **Posicion:** {posicion}  |  **Tipo Lesión:** {tipo}")
    with st.expander("Ver registro JSON", expanded=False):
        import json

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

