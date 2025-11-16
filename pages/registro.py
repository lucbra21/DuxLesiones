import time
import streamlit as st
from src.i18n.i18n import t
import src.config as config
config.init_config()

from src.auth_system.auth_core import init_app_state, validate_login
from src.auth_system.auth_ui import login_view, menu

init_app_state()
validate_login()

from src.ui_components import selection_header
from src.records_ui import view_registro_lesion
from src.db_records import save_lesion

# Authentication gate
if not st.session_state["auth"]["is_logged_in"]:
    login_view()
    st.stop()
menu()

st.header(t("Registro de :red[lesiones]"), divider=True)

jugadora_seleccionada, posicion = selection_header()

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
    st.info(t("Selecciona una jugadora para continuar."))
    st.stop()

record, error, disabled_evolution = view_registro_lesion(jugadora_info=jugadora_info)

######################## GUARDADO Y REINICIO ########################
# Inicializar control de estado del botón
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False

# Determinar si el botón debe estar deshabilitado
disabled_guardar = disabled_evolution or error

submitted = st.button(t("Guardar"),disabled=disabled_guardar, type="primary")
success = False

if submitted:
    # Evitar dobles clics
    st.session_state.form_submitted = True
    st.session_state["form_version"] += 1

    try:
        with st.spinner(t("Guardando registro...")):
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
                st.warning(t(":material/warning: No se pudo guardar la lesión. Revisa los datos e inténtalo nuevamente."))
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