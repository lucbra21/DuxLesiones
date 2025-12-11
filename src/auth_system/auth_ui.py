import streamlit as st
from src.db.db_login import load_user_from_db
from src.auth_system.auth_core import logout, validate_access
from src.util.util import right_caption, set_background_image_local
from src.i18n.i18n import t, language_selector

def login_view() -> None:
    """Renderiza el formulario de inicio de sesión."""

    # Ruta local o URL de la imagen
    #background_image_url = "https://images.unsplash.com/photo-1503264116251-35a269479413"
    set_background_image_local("assets/images/fondo.jpg")
   
    _, col2, _ = st.columns([2, 1.5, 2])
    with col2:
        st.markdown("""
            <style>
                [data-testid="stSidebar"], 
                [data-testid="stBaseButton-headerNoPadding"] { display: none !important; }
            </style>
        """, unsafe_allow_html=True)
        
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.image("assets/images/banner.png")

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Usuario", value="")
            password = st.text_input("Contraseña", type="password", value="")
            submitted = st.form_submit_button("Iniciar sesión", type="primary")

        right_caption("Control de Lesiones")

        if submitted:
            user_data = load_user_from_db(username)
            if not user_data:
                st.error("Usuario no encontrado o inactivo.")
                st.stop()
            validate_access(password, user_data)

def menu():
    with st.sidebar:
        st.logo("assets/images/banner.png", size="large")
        language_selector()
        st.subheader(f'Rol: {st.session_state["auth"]["rol"].capitalize()} :material/admin_panel_settings:')
        
        #st.write(f"Usuario: {st.session_state['auth']['username']}")
        st.write(f"{t('Hola')} **:blue-background[{st.session_state['auth']['name'].capitalize()}]** ")

        st.page_link("app.py", label=t("Inicio"), icon=":material/home:")
        st.subheader(t("Modo :material/dashboard:"))
        st.page_link("pages/registro.py", label=t("Registrar Lesión"), icon=":material/article_person:")
        st.page_link("pages/seguimiento.py", label=t("Seguimiento"), icon=":material/fact_check:")

        st.subheader(t("Análisis y Estadísticas :material/query_stats:"))
        st.page_link("pages/individual.py", label=t("Individual"), icon=":material/personal_injury:")
        st.page_link("pages/grupal.py", label=t("Grupal"), icon=":material/groups:")

        if st.session_state["auth"]["rol"].lower() == "admin" or st.session_state["auth"]["rol"].lower() == "developer":
            st.subheader(t("Administración :material/settings:"))
            st.page_link("pages/admin.py", label=t("Registros"), icon=":material/docs:")
        
        if st.session_state["auth"]["rol"].lower() == "developer":
            #st.page_link("pages/ficha_medica.py", label=t("Ficha Médica"), icon=":material/lab_profile:")
            st.page_link("pages/developer.py", label=t("Developer Area"), icon=":material/code_blocks:")

        btnSalir = st.button(t("Cerrar Sesión"), type="tertiary", icon=":material/logout:")

        if btnSalir:
            logout()


