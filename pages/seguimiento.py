import time
import streamlit as st
from src.i18n.i18n import t
import src.config as config
config.init_config()

from src.records_ui import view_registro_lesion
from src.db_records import save_lesion
from src.ui_components import selection_header
from src.util import clean_df, sanitize_lesion_data

from src.auth_system.auth_core import init_app_state, validate_login
from src.auth_system.auth_ui import login_view, menu

init_app_state()
validate_login()

# Authentication gate
if not st.session_state["auth"]["is_logged_in"]:
    login_view()
    st.stop()
menu()

st.header(t("Seguimiento de :red[lesiones]"), divider="red")

jugadora_seleccionada, posicion, records = selection_header(modo=2)
st.divider()

#st.dataframe(records)

if records.empty:    
    st.warning(t("No hay datos de lesiones disponibles."))
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

OPCIONES_ESTATUS = {
    "Todas": t("Todas"),
    "Activas": t("Activas"),
    "En Observación": t("En Observación"),
    "Inactivas": t("Inactivas")
}

estado_filtro_traducido = st.radio(
    t("Filtrar por estatus:"),
    list(OPCIONES_ESTATUS.values()),
    horizontal=True,
    index=list(OPCIONES_ESTATUS.keys()).index("Todas")
)

# 🔥 Mapeo invertido: valor traducido → clave original
estado_filtro = next(k for k, v in OPCIONES_ESTATUS.items() if v == estado_filtro_traducido)

#estado_filtro = st.radio(t("Filtrar por estatus:"),["Todas", "Activas", "En Observación", "Inactivas"],horizontal=True, index=0)

if estado_filtro == "Activas":
    records = records[records["estado_lesion"].str.lower() == "activo"]
elif estado_filtro == "En Observación":
    records = records[records["estado_lesion"].str.lower() == "observacion"]
elif estado_filtro == "Inactivas":
    records = records[records["estado_lesion"].str.lower() == "inactivo"]

# --- Mensaje dinámico según cantidad ---
num_lesiones = len(records)
if num_lesiones == 0:
    st.info(f"{t('No se encontraron lesiones')} {estado_filtro.lower()}")
    st.stop()
elif num_lesiones == 1:
    st.markdown(f"**{t('Se encontró 1 lesión')} {estado_filtro.lower()[:-1] if estado_filtro != 'Todas' else ''} {t('registrada')}**")
else:
    st.markdown(f"**{t('Se encontraron')} {num_lesiones} {t('lesiones')} {estado_filtro.lower()[:] if estado_filtro != 'Todas' else ''} {t('registradas')}**")

# === Mostrar resultado ===
df_filtrado = clean_df(records)
st.dataframe(df_filtrado)


#st.divider()
st.subheader(t(":red[Buscar] lesión"), divider="red")
col1, col2 = st.columns([1,2])

with col1:
    input_id = st.text_input(t("Introduce el ID de la lesión:"), placeholder=t("Ejemplo: AJB20251013-4"))

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
        st.error(t("No se encontró ninguna lesion con ese ID."))
        st.stop()

    ######################## GUARDADO Y REINICIO ########################
    #st.session_state.form_submitted = False
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
            with st.spinner(t("Actualizando lesión...")):
                success = save_lesion(record, "editar")

                if success:
                    # Si el guardado fue exitoso
                    
                    st.session_state["flash"] = t(":material/done_all: Lesión guardada correctamente.")
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
            st.error(f"{t(':material/warning: Error inesperado al guardar la lesión:')} {e}")
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