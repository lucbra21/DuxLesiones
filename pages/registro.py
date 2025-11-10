import time
import streamlit as st
import src.config as config
config.init_config()

from src.auth_system.auth_core import init_app_state, validate_login
from src.auth_system.auth_ui import login_view, menu

init_app_state()
validate_login()

from src.ui_components import data_filters
from src.records_ui import view_registro_lesion
from src.db_records import save_lesion

# Authentication gate
if not st.session_state["auth"]["is_logged_in"]:
    login_view()
    st.stop()

st.header("Registro de :red[lesiones]", divider=True)

menu()

jugadora_seleccionada, posicion = data_filters()

st.divider()

if jugadora_seleccionada and isinstance(jugadora_seleccionada, dict):
    nombre_completo = (jugadora_seleccionada["nombre"] + " " + jugadora_seleccionada["apellido"]).upper()
    id_jugadora = jugadora_seleccionada["identificacion"]
    posicion = jugadora_seleccionada["posicion"]

    jugadora_info = {
    "id_jugadora": jugadora_seleccionada.get("identificacion"),
    "nombre_completo": f"{jugadora_seleccionada.get('nombre', '')} {jugadora_seleccionada.get('apellido', '')}".upper().strip(),
    "posicion": jugadora_seleccionada.get("posicion"),
    "id_lesion": None}

else:
    st.info("Selecciona una jugadora para continuar.")
    st.stop()

record, error, disabled_evolution = view_registro_lesion(jugadora_info=jugadora_info)

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
        with st.spinner("Guardando registro..."):
            success = save_lesion(record, "nuevo")

            if success:
                # Si el guardado fue exitoso
                
                st.session_state["flash"] = f":material/done_all: Lesión guardada correctamente."
                st.success(st.session_state["flash"])
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
    #st.success(st.session_state["flash"])
    st.session_state["flash"] = None
    st.session_state.form_submitted = False

if success:
    st.session_state["target_page"] = "registro"
    st.switch_page("pages/switch.py")