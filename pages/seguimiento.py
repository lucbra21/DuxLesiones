import time
import streamlit as st

import src.config as config
config.init_config()

from src.records_ui import view_registro_lesion
from src.db_records import save_lesion
from src.ui_components import data_filters
from src.auth import init_app_state, login_view, menu, validate_login
from src.util import clean_df, sanitize_lesion_data

init_app_state()
validate_login()

# Authentication gate
if not st.session_state["auth"]["is_logged_in"]:
    login_view()
    st.stop()

st.header("Seguimiento de :red[lesiones]", divider="red")

menu()

jugadora_seleccionada, posicion, records = data_filters(modo=2)
st.divider()

#st.dataframe(records)

if records.empty:    
    st.warning("No hay datos de lesiones disponibles.")
    st.stop()   
    
if not jugadora_seleccionada:
    st.info("Selecciona una jugadora para continuar.")
    st.stop()

if jugadora_seleccionada and isinstance(jugadora_seleccionada, dict):
    nombre_completo = (jugadora_seleccionada["nombre"] + " " + jugadora_seleccionada["apellido"]).upper()
    id_jugadora = jugadora_seleccionada["identificacion"]
    posicion = jugadora_seleccionada["posicion"]

    jugadora_info = {
        "id_jugadora": jugadora_seleccionada.get("identificacion"),
        "nombre_completo": f"{jugadora_seleccionada.get('nombre', '')} {jugadora_seleccionada.get('apellido', '')}".upper().strip(),
        "posicion": jugadora_seleccionada.get("posicion"),
        "id_lesion": None
    }

    records = records[records["id_jugadora"] == jugadora_seleccionada["identificacion"]]

estado_filtro = st.radio(
    "Filtrar por estatus:",
    ["Todas", "Activas", "En Observación", "Inactivas"],horizontal=True, index=0)

if estado_filtro == "Activas":
    records = records[records["estado_lesion"].str.lower() == "activo"]
elif estado_filtro == "En Observación":
    records = records[records["estado_lesion"].str.lower() == "observacion"]
elif estado_filtro == "Inactivas":
    records = records[records["estado_lesion"].str.lower() == "inactivo"]

# --- Mensaje dinámico según cantidad ---
num_lesiones = len(records)
if num_lesiones == 0:
    st.info(f"No se encontraron lesiones {estado_filtro.lower()}")
    st.stop()
elif num_lesiones == 1:
    st.markdown(f"**Se encontró 1 lesión {estado_filtro.lower()[:-1] if estado_filtro != 'Todas' else ''} registrada.**")
else:
    st.markdown(f"**Se encontraron {num_lesiones} lesiones {estado_filtro.lower()[:] if estado_filtro != 'Todas' else ''} registradas.**")

# === Mostrar resultado ===
df_filtrado = clean_df(records)
st.dataframe(df_filtrado)

#st.divider()
st.subheader(":red[Buscar] lesión", divider="red")
col1, col2 = st.columns([1,2])

with col1:
    input_id = st.text_input("Introduce el ID de la lesión:", placeholder="Ejemplo: AJB20251013-4")

# Si se introduce un ID y se presiona Enter
if input_id:
    # Intentamos convertir a número si aplica
    try:
        id_buscar = int(input_id)
    except ValueError:
        id_buscar = input_id  # por si los ID son strings

    # Buscar el registro
    lesion = records.loc[records["id_lesion"] == id_buscar]

    if not lesion.empty:
        lesion_data = lesion.iloc[0].to_dict()
        lesion_data = sanitize_lesion_data(lesion_data)
        #with st.expander(f"Registro médico de la lesión",expanded=True):
        record, error, disabled_evolution = view_registro_lesion(modo="editar", jugadora_info=jugadora_info, lesion_data=lesion_data)
    else:
        st.error("No se encontró ninguna lesion con ese ID.")
        st.stop()

######################## GUARDADO Y REINICIO ########################
#st.session_state.form_submitted = False
# Inicializar control de estado del botón
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False

# Determinar si el botón debe estar deshabilitado
disabled_guardar = disabled_evolution or error

submitted = st.button("Guardar",disabled=disabled_guardar, type="primary")
success = False

if submitted:
    # Evitar dobles clics
    st.session_state.form_submitted = True
    st.session_state["form_version"] += 1

    try:
        with st.spinner("Actualizando lesión..."):
            success = save_lesion(record, "editar")

            if success:
                # Si el guardado fue exitoso
                
                st.session_state["flash"] = f":material/done_all: Lesión guardada correctamente."
                #{record['id_lesion']}
                #st.rerun()
                time.sleep(4)
                #st.switch_page("pages/switch.py")
                #st.markdown("""<script>window.scrollTo({top: 0, behavior: 'smooth'});</script>""", unsafe_allow_html=True)
                
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

if success:
    st.rerun()
    # st.session_state["target_page"] = "seguimiento"
    # st.switch_page("pages/switch.py")