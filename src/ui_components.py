import streamlit as st
import datetime
from src.io_files import load_jugadoras, upsert_jsonl, load_competiciones

def view_registro_lesion():

    # Lista de jugadoras predefinidas
    jug_df, jug_error = load_jugadoras()
    comp_df, comp_error = load_competiciones()
    
    #st.dataframe(comp_df)
    
    #jugadoras_options = jug_df.to_dict("records")
    
    #with st.form("lesion_form", border=False):
        
    # Organiza el formulario en dos columnas
    col1, col2, col3 = st.columns([2,1,1])

    with col1:
        competiciones_options = comp_df.to_dict("records")
        competicion = st.selectbox(
            "Competición",
            options=competiciones_options,
            format_func=lambda x: f'{x["nombre"]} ({x["codigo"]})',
            placeholder="Seleccione una Competición",
            #index=None
        )
        
    with col2:
        posicion = st.selectbox("Posición", ["PORTERA", "DEFENSA", "CENTRO", "DELANTERA"],
        placeholder="Seleccione una Posición",
        #index=None
        )
        
    with col3:
        if competicion:
            codigo_competicion = competicion["codigo"]
            jug_df_filtrado = jug_df[jug_df["competicion"] == codigo_competicion]

            # Convertir el DataFrame filtrado a lista de opciones
            jugadoras_filtradas = jug_df_filtrado.to_dict("records")
        else:
            jugadoras_filtradas = jug_df.to_dict("records")

        # La nueva columna para el nombre de la jugadora
        jugadora_seleccionada = st.selectbox(
            "Jugadora",
            options=jugadoras_filtradas,
            format_func=lambda x: f'{jugadoras_filtradas.index(x) + 1} - {x["nombre"]} {x["apellido"]}',
            placeholder="Seleccione una Jugadora",
            #index=None
        )
        


    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    # Diccionario principal → subcategorías
    zonas_anatomicas = {
        "MUSLO": ["ISQUIOTIBIALES", "CUÁDRICEPS", "ADUCTORES"],
        "PIERNA": ["GEMELOS", "SÓLEO", "TIBIAL ANTERIOR"],
        "RODILLA": [],
        "TOBILLO": [],
        "PIE": [],
        "CADERA / PELVIS": [],
        "COLUMNA LUMBAR": [],
        "HOMBRO / BRAZO / MUÑECA": [],
        "CABEZA / CUELLO": []
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

    with col1:
        fecha_lesion = st.date_input("Fecha de la lesión", datetime.date.today())
        zona_cuerpo = st.selectbox("Zona del cuerpo", list(zonas_anatomicas.keys()))
        #tipo_tratamiento = st.multiselect("Tipo(s) de tratamiento", tratamientos, placeholder="Selecciona uno o más")
        #fecha_alta_lesion = st.date_input("Fecha de alta real de la lesión", datetime.date.today()) 
    with col2:
        lugar = st.selectbox("Lugar", ["ENTRENAMIENTO", "PARTIDO", "GIMNASIO", "OTRO"])

        subregiones = zonas_anatomicas[zona_cuerpo]
        if subregiones:
            zona_especifica = st.selectbox("Región anatómica específica:", subregiones, key="subregion", disabled=False)
        else:
            zona_especifica = st.selectbox(
                "Región anatómica específica:",
                ["NO APLICA"],
                key="subregion",
                disabled=True
            )

        #dias_baja_estimado = st.number_input("Días de baja estimados", min_value=0, value=0)
        #estado_lesion = st.selectbox("Estado de la lesión", ["Activo", "Inactivo"])

    with col3:
        mecanismo_lesion = st.selectbox("Mecanismo de lesión", ["SIN CONTACTO", "CON CONTACTO", "SOBRECARGA O MICROTRAUMA REPETITIVO", "TORSIÓN O DESEQUILIBRIO", "GOLPE DIRECTO"])
        lateralidad = st.selectbox("Lateralidad", ["DERECHA", "IZQUIERDA", "BILATERAL"])
        #fecha_alta_diagnostico = st.date_input("Fecha estimada de alta (diagnóstico)", datetime.date.today())  
         
    with col4:
        tipo_lesion = st.selectbox("Tipo de lesión", ["CONTUSIÓN", "DISTENSIÓN MUSCULAR", "ESGUINCE", "FRACTURA", "LACERACIÓN", "LESIÓN ARTICULAR", "LESIÓN LIGAMENTARIA", "LUXACIÓN / SUBLUXACIÓN", "ROTURA FIBRILAR", "TENDINOPATÍA", "OTRA"])
        gravedad = st.selectbox("Gravedad", ["LEVE (GRADO I)", "MODERADA (GRADO II)", "GRAVE (GRADO III)", "MUY GRAVE"])
        #personal_reporta = st.text_input("Personal médico que reporta")
        
    diagnostico = st.text_area("Diagnóstico Medico")

    col1, col2, col3, col4 = st.columns([2,1,1,1.5])    

    with col1:
        tipo_tratamiento = st.multiselect("Tipo(s) de tratamiento", tratamientos, placeholder="Selecciona uno o más")
    with col2:
        dias_baja_estimado = st.number_input("Días de baja (estimado)", min_value=0, value=0)
    with col3:
        fecha_alta_diagnostico = st.date_input("Fecha de alta (estimada)", datetime.date.today())  
    with col4:
        personal_reporta = st.text_input("Personal médico que reporta")

    #st.divider()

    st.divider()
    descripcion = st.text_area("Observaciones / Descripción de la lesión")
        
    tratamientos_str = tipo_tratamiento if isinstance(tipo_tratamiento, list) else []

    # Asegúrate de que este orden coincida EXACTAMENTE con los encabezados de tu hoja de Google Sheets
    # Construimos el diccionario de la lesión
    record = {
        "id_jugadora": jugadora_seleccionada["identificacion"],
        "nombre": jugadora_seleccionada["nombre"],
        "fecha_hora": datetime.datetime.now().isoformat(),
        "posicion": posicion,
        "fecha_lesion": fecha_lesion.strftime("%Y-%m-%d"),
        "lugar": lugar,
        "zona_cuerpo": zona_cuerpo,
        "zona_especifica": zona_especifica,
        "lateralidad": lateralidad,
        "tipo_lesion": tipo_lesion,
        "gravedad": gravedad,
        "dias_baja_estimado": dias_baja_estimado,
        "mecanismo_lesion": mecanismo_lesion,
        "tipo_tratamiento": tratamientos_str,
        "personal_reporta": personal_reporta,
        "fecha_alta_diagnostico": fecha_alta_diagnostico.strftime("%Y-%m-%d"),
        "fecha_alta_lesion": None,
        #"fecha_alta_lesion": fecha_alta_lesion.strftime("%Y-%m-%d"),
        "diagnostico": diagnostico,
        "descripcion": descripcion,
    }

    # Preview and save
    #st.divider()

    if st.checkbox("Previsualización"):
        preview_record(record)
        #st.caption(f"Datos almacenados en: {DATA_DIR}/registros.jsonl")

    submitted = st.button("Guardar")
    if submitted:
        if jugadora_seleccionada == 'Seleccionar Jugadora':
            st.error("Por favor, selecciona una jugadora.")
            return
        upsert_jsonl(record)

        # Set flash message to show after rerun
        st.session_state["flash"] = "Registro guardado/actualizado correctamente en data/registros.jsonl"
        # Clear form state by reloading
        st.rerun()

    # Show flash message if present (e.g., after saving)
    if st.session_state.get("flash"):
        st.success(st.session_state["flash"])
        st.session_state["flash"] = None

def preview_record(record: dict) -> None:
    #st.subheader("Previsualización")
    # Header with key fields
    jug = record.get("nombre", "-")
    fecha = record.get("fecha_hora", "-")
    posicion = record.get("posicion", "-")
    tipo = record.get("tipo_lesion", "-")
    st.markdown(f"**Jugadora:** {jug}  |  **Fecha:** {fecha}  |  **Posicion:** {posicion}  |  **Tipo Lesion:** {tipo}")
    with st.expander("Ver registro JSON", expanded=False):
        import json

        st.code(json.dumps(record, ensure_ascii=False, indent=2), language="json")
