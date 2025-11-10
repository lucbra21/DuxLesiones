import streamlit as st
from src.db_login import load_user_from_db
from src.auth_system.auth_core import logout, validate_password

def login_view() -> None:
    """Renderiza el formulario de inicio de sesión."""
    _, col2, _ = st.columns([2, 1.5, 2])
    with col2:
        st.markdown("""
            <style>
                [data-testid="stSidebar"], 
                [data-testid="stBaseButton-headerNoPadding"] { display: none !important; }
            </style>
        """, unsafe_allow_html=True)

        st.image("assets/images/banner.png")

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Usuario", value="")
            password = st.text_input("Contraseña", type="password", value="")
            submitted = st.form_submit_button("Iniciar sesión", type="primary")

        if submitted:
            user_data = load_user_from_db(username)
            if not user_data:
                st.error("Usuario no encontrado o inactivo.")
                st.stop()
            validate_password(password, user_data)

def menu():
    with st.sidebar:
        st.logo("assets/images/banner.png", size="large")
        st.subheader(f'Rol: {st.session_state["auth"]["rol"].capitalize()} :material/admin_panel_settings:')
        
        #st.write(f"Usuario: {st.session_state['auth']['username']}")
        st.write(f"Hola **:blue-background[{st.session_state['auth']['username'].capitalize()}]** ")

        st.page_link("app.py", label="Inicio", icon=":material/home:")
        st.subheader("Gestión de Lesiones  :material/dashboard:")
        st.page_link("pages/registro.py", label="Registrar Lesión", icon=":material/article_person:")
        st.page_link("pages/seguimiento.py", label="Seguimiento", icon=":material/fact_check:")

        st.subheader("Análisis y Estadísticas  :material/query_stats:")
        st.page_link("pages/reporte.py", label="Individual", icon=":material/personal_injury:")

        st.page_link("pages/epidemiologia.py", label="Grupal", icon=":material/groups:")

        if st.session_state["auth"]["rol"].lower() == "admin" or st.session_state["auth"]["rol"].lower() == "developer":
            st.subheader("Administración :material/settings:")
            st.page_link("pages/files.py", label="Registros", icon=":material/docs:")
        
        if st.session_state["auth"]["rol"].lower() == "developer":
            st.page_link("pages/ficha_medica.py", label="Ficha Médica", icon=":material/lab_profile:")
            st.page_link("pages/admin.py", label="Developer Area", icon=":material/code_blocks:")

        btnSalir = st.button("Cerrar Sesión", type="tertiary", icon=":material/logout:")

        if btnSalir:
            logout()


