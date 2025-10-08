import streamlit as st
import datetime
from src.io_files import load_jugadoras, upsert_jsonl

def view_registro_lesion():

    # Lista de jugadoras predefinidas
    jug_df, jug_error = load_jugadoras()

    jugadoras_ejemplo = sorted(
        jug_df.to_dict(orient="records"),
        key=lambda x: x["nombre_jugadora"]
    )

    #with st.form("lesion_form", border=False):
        
    # Organiza el formulario en dos columnas
    col1, col2, col3 = st.columns(3)

    with col1:
        # La nueva columna para el nombre de la jugadora
        jugadora_seleccionada = st.selectbox(
            "Jugadora",
            options=jugadoras_ejemplo,
            format_func=lambda x: f'{x["nombre_jugadora"]} ({x["id_jugadora"]})'
        )

    with col2:
        posicion = st.selectbox("Posición", ["Portera", "Defensa", "Medio centro", "Delantera"])
        
    with col3:
        fecha_lesion = st.date_input("Fecha de la lesión", datetime.date.today())


    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    with col1:            
        estado_lesion = st.selectbox("Estado de la lesión", ["Activo", "Inactivo"])
        zona_cuerpo = st.selectbox("Zona del cuerpo", ["Cabeza", "Cuello", "Tronco", "Hombro", "Codo", "Muñeca", "Mano", "Cadera", "Ingle", "Rodilla", "Tobillo", "Pie", "Muslo", "Pierna"])
        fecha_alta_diagnostico = st.date_input("Fecha estimada de alta (diagnóstico)", datetime.date.today())  
        
    with col2:
        gravedad = st.selectbox("Gravedad", ["Leve", "Moderada", "Grave"])
        dias_baja_estimado = st.number_input("Días de baja estimados", min_value=0, value=0)
        fecha_alta_lesion = st.date_input("Fecha de alta real de la lesión", datetime.date.today())
        
    with col3:
        tipo_lesion = st.selectbox("Tipo de lesión", ["Muscular", "Ósea", "Tendinosa", "Articular", "Ligamentosa", "Contusión"])
        mecanismo_lesion = st.selectbox("Mecanismo de lesión", ["Entrenamiento", "Partido", "Gimnasio", "Otro"])
        personal_reporta = st.text_input("Personal médico que reporta")

    with col4:
        lateralidad = st.selectbox("Lateralidad", ["Derecha", "Izquierda", "Bilateral"])
        tipo_tratamiento = st.multiselect("Tipo(s) de tratamiento", ["Fisioterapia", "Medicación", "Gimnasio", "Cirugía", "Reposo", "Readaptación"], placeholder="Selecciona uno o más")
        
    descripcion = st.text_area("Descripción")
        
    tratamientos_str = tipo_tratamiento if isinstance(tipo_tratamiento, list) else []

    # Asegúrate de que este orden coincida EXACTAMENTE con los encabezados de tu hoja de Google Sheets
    # Construimos el diccionario de la lesión
    record = {
        "id_jugadora": jugadora_seleccionada["id_jugadora"],
        "nombre_jugadora": jugadora_seleccionada["nombre_jugadora"],
        "fecha_hora": datetime.datetime.now().isoformat(),
        "posicion": posicion,
        "fecha_lesion": fecha_lesion.strftime("%Y-%m-%d"),
        "estado_lesion": estado_lesion,
        "zona_cuerpo": zona_cuerpo,
        "lateralidad": lateralidad,
        "tipo_lesion": tipo_lesion,
        "gravedad": gravedad,
        "dias_baja_estimado": dias_baja_estimado,
        "mecanismo_lesion": mecanismo_lesion,
        "tipo_tratamiento": tratamientos_str,
        "personal_reporta": personal_reporta,
        "fecha_alta_diagnostico": fecha_alta_diagnostico.strftime("%Y-%m-%d"),
        "fecha_alta_lesion": fecha_alta_lesion.strftime("%Y-%m-%d"),
        "descripcion": descripcion,
    }

    # Preview and save
    st.divider()

    if st.checkbox("Previsualización"):
        preview_record(record)
        #st.caption(f"Datos almacenados en: {DATA_DIR}/registros.jsonl")

    submitted = st.button("Registrar Lesión")
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
    jug = record.get("nombre_jugadora", "-")
    fecha = record.get("fecha_hora", "-")
    posicion = record.get("posicion", "-")
    tipo = record.get("tipo_lesion", "-")
    st.markdown(f"**Jugadora:** {jug}  |  **Fecha:** {fecha}  |  **Posicion:** {posicion}  |  **Tipo Lesion:** {tipo}")
    with st.expander("Ver registro JSON", expanded=False):
        import json

        st.code(json.dumps(record, ensure_ascii=False, indent=2), language="json")
