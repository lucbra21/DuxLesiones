import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime # Importa datetime para manejar fechas

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

# Función para la conexión y carga de datos
@st.cache_data(ttl=600)  # Cacha los datos por 10 minutos para evitar llamadas repetidas
def get_data_from_gsheets():
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        client = gspread.authorize(creds)
        spreadsheet = client.open(SHEET_NAME)
        worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        # Convertir algunas columnas a tipo de fecha si es necesario para análisis futuros
        # df['Fecha Lesion'] = pd.to_datetime(df['Fecha Lesion'], format='%d/%m/%Y', errors='coerce')
        return df
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return pd.DataFrame() # Retorna un DataFrame vacío en caso de error

# --- VISUALIZACIÓN DE LA APLICACIÓN ---
st.title("⚽️ Registro de Lesiones - Club de Fútbol Femenino")
st.markdown("---")
st.subheader("Dashboard de Lesiones Actuales")

# Cargar los datos
df_lesiones = get_data_from_gsheets()

if not df_lesiones.empty:
    st.dataframe(df_lesiones, use_container_width=True)
else:
    st.warning("No se pudo cargar la información de lesiones. Por favor, revisa la conexión y los permisos.")

# --- FORMULARIO PARA REGISTRAR NUEVA LESIÓN ---
st.markdown("---")
st.subheader("Registrar Nueva Lesión ✍️")

with st.form("lesion_form"):
    # Organiza el formulario en dos columnas
    col1, col2 = st.columns(2)
    with col1:
        # Nota: 'jugadora' se quitará, pero necesitamos un placeholder para la relación en DB.
        # Por ahora, podemos poner un campo oculto o un valor predeterminado.
        # Para mantener el flujo y no romper el GSheets, lo dejaremos como un input simple
        # que no se usará activamente, o pondremos un valor por defecto si lo prefieres.
        # De momento, lo quitamos como "entrada manual".
        
        # Asumiendo que la jugadora se seleccionará de una lista precargada en el futuro:
        # Por ahora, para que el formulario funcione sin un campo de jugadora "manual",
        # puedes usar un valor por defecto o un placeholder que se reemplazará.
        # Por ejemplo, una selección de jugadoras predefinidas si tuvieras esa lista,
        # o simplemente no incluirlo por ahora si vas a manejarlo desde la DB.
        
        # *** Importante: En tu hoja de Google Sheets, la columna 'Jugadora' debe seguir existiendo,
        # *** de lo contrario, al insertar la fila, se desalinearán los datos.
        # *** Podemos enviar un valor por defecto o un placeholder por ahora.
        # *** Para el ejemplo, usaremos un placeholder 'ID_JUGADORA_PENDIENTE'.
        
        # No se pide jugadora directamente en el formulario
        # jugadora = st.text_input("ID de Jugadora (se cargará de la DB)", "ID_PENDIENTE") # Placeholder temporal
        
        posicion = st.selectbox("Posición", ["Portera", "Defensa", "Medio centro", "Delantera"]) # Corregí 'Porcera' a 'Portera'
        # fecha_nacimiento eliminada
        fecha_lesion = st.date_input("Fecha de la lesión", datetime.date.today())
        
        # Campo estado_lesion modificado
        estado_lesion = st.selectbox("Estado de la lesión", ["Activo", "Inactivo"])
        
        tipo_lesion = st.selectbox("Tipo de lesión", ["Muscular", "Ósea", "Tendinosa", "Articular", "Ligamentosa", "Contusión"])
        zona_cuerpo = st.selectbox("Zona del cuerpo", ["Cabeza", "Cuello", "Tronco", "Hombro", "Codo", "Muñeca", "Mano", "Cadera", "Ingle", "Rodilla", "Tobillo", "Pie", "Muslo", "Pierna"])
        
    with col2:
        lateralidad = st.selectbox("Lateralidad", ["Derecha", "Izquierda", "Bilateral"])
        
        # Campo gravedad modificado y añadimos 'dias_baja_estimado'
        gravedad = st.selectbox("Gravedad", ["Leve", "Moderada", "Grave"])
        dias_baja_estimado = st.number_input("Días de baja estimados (según diagnóstico)", min_value=0, value=0)
        
        mecanismo_lesion = st.selectbox("Mecanismo de lesión", ["Entrenamiento", "Partido", "Gimnasio", "Otro"])
        # fecha_tratamiento eliminada
        
        # Campo tipo_tratamiento para selección múltiple
        tipo_tratamiento = st.multiselect("Tipo(s) de tratamiento", ["Fisioterapia", "Medicación", "Gimnasio", "Cirugía", "Reposo", "Readaptación"])
        
        personal_reporta = st.text_input("Personal médico que reporta")
        
        # Nuevos campos de fecha de alta
        fecha_alta_diagnostico = st.date_input("Fecha estimada de alta (diagnóstico)", datetime.date.today())
        fecha_alta_lesion = st.date_input("Fecha de alta real de la lesión", datetime.date.today()) # Podría ser un campo opcional o llenarse después

        descripcion = st.text_area("Descripción (texto libre)")

    submitted = st.form_submit_button("Registrar Lesión")
    if submitted:
        # Preparamos los tipos de tratamiento para guardar como una cadena separada por comas
        tratamientos_str = ", ".join(tipo_tratamiento) if tipo_tratamiento else ""

        # --- ORDEN DE COLUMNAS PARA GOOGLE SHEETS (MUY IMPORTANTE) ---
        # Asegúrate de que este orden coincida EXACTAMENTE con los encabezados de tu hoja de Google Sheets.
        # Si las columnas en tu hoja de Google Sheets no se llaman igual o están en un orden diferente,
        # esto causará errores o desalineación de datos.
        # Necesitarás crear las nuevas columnas en Google Sheets si no existen.
        # Por ahora, asumo que las columnas en GSheets son:
        # [Jugadora, Posicion, Fecha Lesion, Estado Lesion, Tipo Lesion, Zona Cuerpo, Lateralidad,
        # Gravedad, Dias Baja Estimado, Mecanismo Lesion, Tipo Tratamiento, Personal Reporta,
        # Fecha Alta Diagnostico, Fecha Alta Lesion, Descripcion]
        
        new_row = [
            "ID_JUGADORA_PENDIENTE", # Placeholder para 'jugadora'
            posicion,
            fecha_lesion.strftime("%d/%m/%Y"),
            estado_lesion,
            tipo_lesion,
            zona_cuerpo,
            lateralidad,
            gravedad,
            dias_baja_estimado, # Nuevo campo
            mecanismo_lesion,
            tratamientos_str, # Tipo de tratamiento como cadena
            personal_reporta,
            fecha_alta_diagnostico.strftime("%d/%m/%Y"), # Nuevo campo
            fecha_alta_lesion.strftime("%d/%m/%Y"), # Nuevo campo
            descripcion
        ]

        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
            client = gspread.authorize(creds)
            spreadsheet = client.open(SHEET_NAME)
            worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
            
            # Añade la nueva fila a la hoja de cálculo
            worksheet.append_row(new_row)
            
            st.success("¡Lesión registrada con éxito! Los datos han sido guardados.")
            st.balloons() # Animación de confeti
            
            # Limpiar el caché de datos para que el dashboard se actualice
            st.cache_data.clear()
            
        except Exception as e:
            st.error(f"Error al guardar los datos: {e}")