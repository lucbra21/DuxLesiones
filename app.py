import streamlit as st
import pandas as pd
import datetime

import src.config as config
config.init_config()

from src.auth import init_app_state, login_view, menu, validate_login
from src.io_files import get_records_df
init_app_state()

validate_login()

# Authentication gate
if not st.session_state["auth"]["is_logged_in"]:
    #st.text("🔐 Por favor, inicie sesión para acceder a esta página.")
    login_view()
    st.stop()

st.header("Resumen de :red[Lesiones]", divider=True)

menu()

#SHEET_NAME = 'Propuesta tablas'
WORKSHEET_NAME = 'Tabla I invent jugadores' # Asegúrate de que este nombre sea exacto

records = get_records_df()  # Carga y cachea los datos

if records.empty:    
    st.warning("No hay datos de lesiones disponibles.")
    st.stop()   

# === Filtros ===
periodo = st.radio("Agrupar por:", ["Semana", "Mes"], horizontal=True)

articulo = "el último"

records["fecha_alta_diagnostico"] = pd.to_datetime(records["fecha_alta_diagnostico"], errors="coerce")
if periodo == "Semana":
    articulo = "la última"
    records["periodo"] = records["fecha_alta_diagnostico"].dt.isocalendar().week
    ultimos = records[records["fecha_alta_diagnostico"] >= (records["fecha_alta_diagnostico"].max() - pd.Timedelta(days=7))]
else:
    records["periodo"] = records["fecha_alta_diagnostico"].dt.month
    ultimos = records[records["fecha_alta_diagnostico"] >= (records["fecha_alta_diagnostico"].max() - pd.Timedelta(days=30))]

# === Métricas base ===
total_lesiones = len(records)
activas = records[records["estado_lesion"] == "ACTIVO"].shape[0]
porcentaje_activas = round((activas / total_lesiones) * 100, 1)
promedio_dias_baja = round(records["dias_baja_estimado"].mean(), 1)
zona_top = records["zona_cuerpo"].mode()[0]
zona_count = records["zona_cuerpo"].value_counts().iloc[0]
zona_pct = round((zona_count / total_lesiones) * 100, 1)

# === Series por periodo ===

# Total de lesiones por periodo (para el gráfico principal)
trend_total = records.groupby("periodo").size().reset_index(name="cantidad")

trend_activas = (
    records[records["estado_lesion"] == "ACTIVO"]
    .groupby("periodo")
    .size()
    .reset_index(name="count")
)
chart_activas = trend_activas["count"].tolist()

trend_dias = (
    records.groupby("periodo")["dias_baja_estimado"]
    .mean()
    .reset_index(name="avg_days")
)

# Redondeamos a 2 decimales
trend_dias["avg_days"] = trend_dias["avg_days"].round(2)
chart_dias = trend_dias["avg_days"].tolist()

trend_zonas = (
    records[records["zona_cuerpo"] == zona_top]
    .groupby("periodo")
    .size()
    .reset_index(name="count")
)
chart_zonas = trend_zonas["count"].tolist()

# === Calcular deltas ===
def calc_delta(values):
    if len(values) < 2:
        return 0
    return round(((values[-1] - values[-2]) / values[-2]) * 100, 1) if values[-2] != 0 else 0

delta_activas = calc_delta(chart_activas)
delta_dias = calc_delta(chart_dias)
delta_zona = calc_delta(chart_zonas)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        "Lesiones activas",
        activas,
        f"{delta_activas:+.1f}%",
        chart_data=chart_activas,
        chart_type="line",
        border=True,
        delta_color="inverse",  # 🔴 if increased, 🟢 if decreased
        help=f"Variación en las lesiones activas en comparación con {articulo} {periodo.lower()}."
    )
with col2:
    st.metric(
        "Días de recuperación promedio",
        promedio_dias_baja,
        f"{delta_dias:+.1f}%",
        chart_data=chart_dias,
        chart_type="area",
        border=True,
        delta_color="normal",  # 🟢 increase = longer recovery
        help=f"Variación del tiempo promedio de recuperación por {periodo.lower()}."
    )
with col3:
    st.metric(
        f"Zona más afectada: {zona_top}",
        f"{zona_count} cases",
        f"{delta_zona:+.1f}%",
        chart_data=chart_zonas,
        chart_type="bar",
        border=True,
        delta_color="inverse",  # 🔴 more injuries in this zone = bad
        help=f"Frecuencia de lesiones en {zona_top} comparado con {articulo} {periodo.lower()}."
    )

#     st.metric(
#         f"Most Affected Zone",
#         zona_top,
#         f"{zona_pct}%",
#         help="Zone with highest injury frequency"
#     )

#st.divider()

# # Agrupar por fecha y contar lesiones
# trend_fecha = (
#     ultimos.groupby(ultimos["fecha_alta_diagnostico"].dt.date)
#     .size()
#     .reset_index(name="count")
#     .sort_values("fecha_alta_diagnostico")
# )

# # 🔹 Gráfico en barras
# st.line_chart(
#     trend_fecha,
#     x="fecha_alta_diagnostico",
#     y="count"
# )

def editar_registro(df_original, row_id, new_data):
    """Función simulada para editar una fila. En GSheets, se debe hacer por índice."""
    try:
        #creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, SCOPE)
        #client = gspread.authorize(creds)
        #spreadsheet = client.open(SHEET_NAME)
        #worksheet = spreadsheet.worksheet(WORKSHEET_NAME)
        
        # row_id es el índice de la fila en GSheets (ID + 2)
        row_to_update = row_id 
        
        # Actualiza la fila con los nuevos datos (new_data debe ser una lista)
        #worksheet.update(f'A{row_to_update}:{chr(65 + len(new_data) - 1)}{row_to_update}', [new_data])
        
        st.success(f"Registro ID {row_id} actualizado con éxito.")
        st.cache_data.clear()
        st.rerun()
        
    except Exception as e:
        st.error(f"Error al editar el registro: {e}")
        st.info("Asegúrate de que la hoja de Google Sheets no esté protegida o que las credenciales sean correctas.")

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
                new_estado_lesion = st.selectbox("Estado de la lesión", ["ACTIVO", "INACTIVO"], index=["ACTIVO", "INACTIVO"].index(fila_actual.get('Estado Lesion', 'ACTIVO')))
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
