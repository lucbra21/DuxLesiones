import streamlit as st

import jwt
import time
from st_cookies_manager import EncryptedCookieManager

# IMPORTACIONES NECESARIAS PARA LAS PAGINAS
# Importamos la página de Epidemiología. Necesitas una línea similar para Registro, Historico y Reporte
# Asumo que tienes un archivo de apoyo que maneja estos imports, pero aquí las listamos:
from pages import epidemiologia # Tu dashboard

# Si tus páginas Registro, Historico y Reporte se llaman con st.page_link, no es necesario importarlas aquí.
# Pero si usan funciones, necesitarás importarlas (ej: from pages import registro)

# --- CONFIG JWT / COOKIES (Resto del código idéntico) ---
JWT_SECRET = st.secrets.auth.jwt_secret
# ... (todo el código de JWT y login_view es idéntico) ...
JWT_ALGORITHM = st.secrets.auth.algorithm
JWT_EXP_DELTA_SECONDS = st.secrets.auth.time
cookies = EncryptedCookieManager(prefix="dux-lesiones", password=JWT_SECRET)
if not cookies.ready():
    st.stop()

def init_app_state():
    ensure_session_defaults()
    if "flash" not in st.session_state:
        st.session_state["flash"] = None
        
    # INICIALIZA LA PÁGINA ACTUAL
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = "Inicio" # Página por defecto

def ensure_session_defaults() -> None:
    # ... (código idéntico) ...
    if "auth" not in st.session_state:
        st.session_state["auth"] = {
            "is_logged_in": False,
            "username": "",
            "rol": "",
            "token": ""
        }
    
def _get_credentials() -> tuple[str, str, str]:
    # ... (código idéntico) ...
    user = st.secrets.db.username
    pwd = st.secrets.db.password
    rol = st.secrets.db.rol
    return user, pwd, rol

# ... (todo el código de login_view, create_jwt_token, get_current_user, validate_login es idéntico) ...

def menu():
    # El menú ya no usa st.page_link sino un st.sidebar.radio para control manual.
    
    with st.sidebar:
        st.logo("assets/images/banner.png", size="large")
        st.subheader("Entrenador :material/admin_panel_settings:")
        
        st.write(f"Hola **:blue-background[{st.session_state['auth']['username'].capitalize()}]** ")

        # Menú de navegación manual con radio
        page = st.sidebar.radio(
            "Modo",
            ["Inicio", "Registrar Lesion", "Epidemiología", "Historico", "Reporte individual"],
            index=["Inicio", "Registrar Lesion", "Epidemiología", "Historico", "Reporte individual"].index(st.session_state.current_page),
            key='menu_selection'
        )

        st.session_state.current_page = page # Guarda la selección
        
        # --- OPCIONES ADICIONALES ---
        if st.session_state["auth"]["rol"] == "developer":
            st.markdown("---")
            st.page_link("pages/admin.py", label="Admin", icon=":material/app_registration:")
        
        #st.page_link("pages/rpe.py", label="RPE", icon=":material/lab_profile:")

        btnSalir = st.button("Cerrar Sesión", type="tertiary", icon=":material/logout:")

        if btnSalir:
            logout()
    
    # 🛑 ESTE BLOQUE DEBE ESTAR FUERA DEL st.sidebar para renderizar la página
    # Usamos el st.session_state.current_page para decidir qué mostrar.

    if st.session_state.current_page == "Inicio":
        # Ejecuta el código de la página principal (app.py)
        st.title("Inicio de DUX Lesiones")
        st.markdown("Selecciona una opción del menú lateral para continuar.")
    
    elif st.session_state.current_page == "Registrar Lesion":
        # Necesitas importar el módulo de registro si usas este sistema:
        import pages.registro
    
    elif st.session_state.current_page == "Epidemiología":
        # 🛑 AQUÍ FORZAMOS LA EJECUCIÓN DEL CÓDIGO 🛑
        import pages.epidemiologia
        
    elif st.session_state.current_page == "Historico":
        # Necesitas importar el módulo de Historico:
        import pages.historico
        
    elif st.session_state.current_page == "Reporte individual":
        # Necesitas importar el módulo de Reporte:
        import pages.reporte
    
    # Si tienes otras páginas, sigue la misma estructura 'elif'.


def logout():
    """Elimina sesión y cookie."""
    st.session_state["auth"] = {"is_logged_in": False, "username": "", "token": "", "rol": ""}
    cookies["auth_token"] = ""
    cookies.save()

    st.rerun()
