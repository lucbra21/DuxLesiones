import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime

# --- CONFIGURACIÓN DE LA APLICACIÓN ---
st.set_page_config(
    page_title="Registro de Lesiones | Fútbol Femenino",
    page_icon="⚽",
    layout="wide"
)

# --- CONFIGURACIÓN DE GOOGLE SHEETS ---
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
CREDS_FILE = 'registro-de-lesiones-b8d69c2d5b34.json'
SHEET_NAME = 'Propuesta tablas'
WORKSHEET_NAME = 'Tabla I invent jugadores' # Asegúrate de que este nombre sea exacto

# --- VARIABLES DE ESTADO/SESIÓN ---
# Define los perfiles que se usarán en la aplicación
PERFILES = ["Médico/Reporte", "Administrador"]

# --- FUNCIONES ---

@st.cache_data(ttl=600)  # Cacha los datos por 10 minutos para evitar llamadas repetidas
def get_data_from_gsheets():
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        client = gspread.authorize(creds)
        spreadsheet = client.open(SHEET_NAME)
        # Usamos el nombre de la hoja de cálculo de los registros
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME) 
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        # Añadir una columna de índice para ayudar con la edición
        df.insert(0, 'ID', df.index + 2) # +2 porque la fila 1 es el encabezado, y el índice empieza en 0
        return df
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return pd.DataFrame() 

def registrar_lesion(data):
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        client = gspread.authorize(creds)
        spreadsheet = client.open(SHEET_NAME)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        
        # Añade la nueva fila a la hoja de cálculo
        worksheet.append_row(data)
        
        st.success("¡Lesión registrada con éxito! Los datos han sido guardados.")
        st.balloons() 
        # Limpiar el caché de datos para que el dashboard se actualice
        st.cache_data.clear()
        st.rerun() # Volver a ejecutar para mostrar el dashboard actualizado
        
    except Exception as e:
        st.error(f"Error al guardar los datos: {e}")

def editar_registro(df_original, row_id, new_data):
    """Función simulada para editar una fila. En GSheets, se debe hacer por índice."""
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        client = gspread.authorize(creds)
        spreadsheet = client.open(SHEET_NAME)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        
        # row_id es el índice de la fila en GSheets (ID + 2)
        row_to_update = row_id 
        
        # Actualiza la fila con los nuevos datos (new_data debe ser una lista)
        worksheet.update(f'A{row_to_update}:{chr(65 + len(new_data) - 1)}{row_to_update}', [new_data])
        
        st.success(f"Registro ID {row_id} actualizado con éxito.")
        st.cache_data.clear()
        st.rerun()
        
    except Exception as e:
        st.error(f"Error al editar el registro: {e}")
        st.info("Asegúrate de que la hoja de Google Sheets no esté protegida o que las credenciales sean correctas.")


# --- VISTA DEL FORMULARIO DE REGISTRO ---

def view_registro_lesion():
    st.subheader("Registrar Nueva Lesión ✍️")
    
    # Lista de jugadoras predefinidas (DEBES REEMPLAZAR CON TU LISTA REAL)
    jugadoras_ejemplo = ['Seleccionar Jugadora', 'Catalina Pérez', 'Linda Caicedo', 'Mayra Ramírez', 'Manuela Vanegas', 'Daniela Montoya']

    with st.form("lesion_form"):
        # La nueva columna para el nombre de la jugadora
        jugadora_seleccionada = st.selectbox("Nombre de la Jugadora", jugadoras_ejemplo)

        # Organiza el formulario en dos columnas
        col1, col2 = st.columns(2)
        with col1:
            posicion = st.selectbox("Posición", ["Portera", "Defensa", "Medio centro", "Delantera"])
            fecha_lesion = st.date_input("Fecha de la lesión", datetime.date.today())
            estado_lesion = st.selectbox("Estado de la lesión", ["Activo", "Inactivo"])
            tipo_lesion = st.selectbox("Tipo de lesión", ["Muscular", "Ósea", "Tendinosa", "Articular", "Ligamentosa", "Contusión"])
            zona_cuerpo = st.selectbox("Zona del cuerpo", ["Cabeza", "Cuello", "Tronco", "Hombro", "Codo", "Muñeca", "Mano", "Cadera", "Ingle", "Rodilla", "Tobillo", "Pie", "Muslo", "Pierna"])
            
        with col2:
            lateralidad = st.selectbox("Lateralidad", ["Derecha", "Izquierda", "Bilateral"])
            gravedad = st.selectbox("Gravedad", ["Leve", "Moderada", "Grave"])
            dias_baja_estimado = st.number_input("Días de baja estimados", min_value=0, value=0)
            mecanismo_lesion = st.selectbox("Mecanismo de lesión", ["Entrenamiento", "Partido", "Gimnasio", "Otro"])
            tipo_tratamiento = st.multiselect("Tipo(s) de tratamiento", ["Fisioterapia", "Medicación", "Gimnasio", "Cirugía", "Reposo", "Readaptación"])
            personal_reporta = st.text_input("Personal médico que reporta")
            fecha_alta_diagnostico = st.date_input("Fecha estimada de alta (diagnóstico)", datetime.date.today())
            fecha_alta_lesion = st.date_input("Fecha de alta real de la lesión", datetime.date.today())
            descripcion = st.text_area("Descripción (texto libre)")

        submitted = st.form_submit_button("Registrar Lesión")
        if submitted:
            if jugadora_seleccionada == 'Seleccionar Jugadora':
                st.error("Por favor, selecciona una jugadora.")
                return

            tratamientos_str = ", ".join(tipo_tratamiento) if tipo_tratamiento else ""

            # Asegúrate de que este orden coincida EXACTAMENTE con los encabezados de tu hoja de Google Sheets
            new_row = [
                jugadora_seleccionada, # Campo de jugadora
                posicion,
                fecha_lesion.strftime("%d/%m/%Y"),
                estado_lesion,
                tipo_lesion,
                zona_cuerpo,
                lateralidad,
                gravedad,
                dias_baja_estimado,
                mecanismo_lesion,
                tratamientos_str, 
                personal_reporta,
                fecha_alta_diagnostico.strftime("%d/%m/%Y"),
                fecha_alta_lesion.strftime("%d/%m/%Y"),
                descripcion
            ]
            registrar_lesion(new_row)

# --- VISTA DEL FORMULARIO DE EDICIÓN (Solo para Administrador) ---

def view_editar_registro(df_lesiones):
    st.subheader("Editar Registro de Lesión ✏️")

    # Selección de registro
    registro_ids = df_lesiones['ID'].tolist()
    registro_seleccionado_id = st.selectbox(
        "Selecciona el ID de la lesión a editar:", 
        registro_ids,
        format_func=lambda x: f"ID: {x} - {df_lesiones.loc[df_lesiones['ID'] == x].iloc[0]['Jugadora']} - {df_lesiones.loc[df_lesiones['ID'] == x].iloc[0]['Fecha Lesion']}"
    )

    if registro_seleccionado_id:
        # Obtener los datos actuales de la fila seleccionada
        fila_actual = df_lesiones.loc[df_lesiones['ID'] == registro_seleccionado_id].iloc[0]
        st.write("---")
        st.markdown(f"**Editando registro ID {registro_seleccionado_id} de {fila_actual['Jugadora']}**")

        # El índice real en Google Sheets es el ID
        gsheets_row_index = int(registro_seleccionado_id)
        
        # --- Formulario de edición (similar al de registro, pero con valores prellenados) ---
        with st.form(key="edit_form"):
            col1, col2 = st.columns(2)
            
            # Recrear los campos con valores por defecto
            with col1:
                # Nombre de la jugadora (No editable en esta simulación, pero se muestra el valor)
                st.text_input("Jugadora", value=fila_actual.get('Jugadora', 'N/A'), disabled=True) 
                
                new_posicion = st.selectbox("Posición", ["Portera", "Defensa", "Medio centro", "Delantera"], index=["Portera", "Defensa", "Medio centro", "Delantera"].index(fila_actual.get('Posicion', 'Defensa')))
                new_fecha_lesion = st.date_input("Fecha de la lesión", pd.to_datetime(fila_actual.get('Fecha Lesion', datetime.date.today()), format='%d/%m/%Y', errors='coerce'), key='edit_fecha_lesion')
                new_estado_lesion = st.selectbox("Estado de la lesión", ["Activo", "Inactivo"], index=["Activo", "Inactivo"].index(fila_actual.get('Estado Lesion', 'Activo')))
                new_tipo_lesion = st.selectbox("Tipo de lesión", ["Muscular", "Ósea", "Tendinosa", "Articular", "Ligamentosa", "Contusión"], index=["Muscular", "Ósea", "Tendinosa", "Articular", "Ligamentosa", "Contusión"].index(fila_actual.get('Tipo Lesion', 'Muscular')))
                new_zona_cuerpo = st.selectbox("Zona del cuerpo", ["Cabeza", "Cuello", "Tronco", "Hombro", "Codo", "Muñeca", "Mano", "Cadera", "Ingle", "Rodilla", "Tobillo", "Pie", "Muslo", "Pierna"], index=["Cabeza", "Cuello", "Tronco", "Hombro", "Codo", "Muñeca", "Mano", "Cadera", "Ingle", "Rodilla", "Tobillo", "Pie", "Muslo", "Pierna"].index(fila_actual.get('Zona Cuerpo', 'Rodilla')))

            with col2:
                new_lateralidad = st.selectbox("Lateralidad", ["Derecha", "Izquierda", "Bilateral"], index=["Derecha", "Izquierda", "Bilateral"].index(fila_actual.get('Lateralidad', 'Derecha')))
                new_gravedad = st.selectbox("Gravedad", ["Leve", "Moderada", "Grave"], index=["Leve", "Moderada", "Grave"].index(fila_actual.get('Gravedad', 'Leve')))
                new_dias_baja_estimado = st.number_input("Días de baja estimados", min_value=0, value=int(fila_actual.get('Dias Baja Estimado', 0)))
                new_mecanismo_lesion = st.selectbox("Mecanismo de lesión", ["Entrenamiento", "Partido", "Gimnasio", "Otro"], index=["Entrenamiento", "Partido", "Gimnasio", "Otro"].index(fila_actual.get('Mecanismo Lesion', 'Entrenamiento')))
                
                # Para multiselect: convertir la cadena guardada en lista
                current_tratamientos = fila_actual.get('Tipo Tratamiento', '').split(', ')
                new_tipo_tratamiento = st.multiselect("Tipo(s) de tratamiento", ["Fisioterapia", "Medicación", "Gimnasio", "Cirugía", "Reposo", "Readaptación"], default=current_tratamientos)
                
                new_personal_reporta = st.text_input("Personal médico que reporta", value=fila_actual.get('Personal Reporta', ''))
                
                # Manejo de fechas para prellenado
                try:
                    fecha_alta_diag_default = pd.to_datetime(fila_actual.get('Fecha Alta Diagnostico', datetime.date.today()), format='%d/%m/%Y', errors='coerce').date()
                    fecha_alta_real_default = pd.to_datetime(fila_actual.get('Fecha Alta Lesion', datetime.date.today()), format='%d/%m/%Y', errors='coerce').date()
                except:
                    fecha_alta_diag_default = datetime.date.today()
                    fecha_alta_real_default = datetime.date.today()

                new_fecha_alta_diagnostico = st.date_input("Fecha estimada de alta (diagnóstico)", fecha_alta_diag_default, key='edit_fecha_alta_diag')
                new_fecha_alta_lesion = st.date_input("Fecha de alta real de la lesión", fecha_alta_real_default, key='edit_fecha_alta_real')
                
                new_descripcion = st.text_area("Descripción (texto libre)", value=fila_actual.get('Descripcion', ''))

            edit_submitted = st.form_submit_button("Actualizar Registro")
            if edit_submitted:
                # 1. Preparar la nueva fila de datos en el mismo orden de la hoja de cálculo
                tratamientos_str = ", ".join(new_tipo_tratamiento) if new_tipo_tratamiento else ""
                
                updated_row_data = [
                    fila_actual.get('Jugadora', 'N/A'), # Usamos la jugadora original
                    new_posicion,
                    new_fecha_lesion.strftime("%d/%m/%Y"),
                    new_estado_lesion,
                    new_tipo_lesion,
                    new_zona_cuerpo,
                    new_lateralidad,
                    new_gravedad,
                    new_dias_baja_estimado,
                    new_mecanismo_lesion,
                    tratamientos_str, 
                    new_personal_reporta,
                    new_fecha_alta_diagnostico.strftime("%d/%m/%Y"),
                    new_fecha_alta_lesion.strftime("%d/%m/%Y"),
                    new_descripcion
                ]
                
                # 2. Llamar a la función de edición
                editar_registro(df_lesiones, gsheets_row_index, updated_row_data)


# --- LÓGICA DE NAVEGACIÓN PRINCIPAL ---

st.title("⚽️ Registro de Lesiones - Club de Fútbol Femenino")

# 1. Menú de Perfiles de Usuario
perfil_seleccionado = st.sidebar.selectbox(
    "Seleccionar Perfil de Ingreso",
    PERFILES
)

st.sidebar.markdown("---")

# 2. Cargar datos para el Dashboard y Edición
df_lesiones = get_data_from_gsheets()

if not df_lesiones.empty:
    st.markdown(f"### Dashboard ({perfil_seleccionado})")
    
    # 3. Mostrar el Dashboard de Lesiones (Visible para todos)
    st.dataframe(df_lesiones.drop(columns=['ID']), use_container_width=True)
else:
    st.warning("No se pudo cargar la información de lesiones. Revisa la conexión/permisos.")


st.markdown("---")


# 4. Control de Vistas por Perfil

if perfil_seleccionado == "Médico/Reporte":
    view_registro_lesion() # Solo ve el formulario de registro

elif perfil_seleccionado == "Administrador":
    # El administrador puede ver el formulario de registro y la opción de editar
    st.subheader("Opciones de Administrador")
    
    opcion_admin = st.radio(
        "Seleccionar Tarea:", 
        ("Registrar Nueva Lesión", "Editar/Actualizar Registro"),
        key="admin_task"
    )
    
    if opcion_admin == "Registrar Nueva Lesión":
        view_registro_lesion()
    
    elif opcion_admin == "Editar/Actualizar Registro":
        view_editar_registro(df_lesiones)