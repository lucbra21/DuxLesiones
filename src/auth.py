import streamlit as st

import jwt
import time
from st_cookies_manager import EncryptedCookieManager

# 🛑 IMPORTACIONES DE PÁGINAS ELIMINADAS: Dejaremos que el archivo principal (app.py) maneje la ejecución de las páginas para evitar errores de ruta.

# # --- CONFIG JWT ---
JWT_SECRET = st.secrets.auth.jwt_secret
JWT_ALGORITHM = st.secrets.auth.algorithm
JWT_EXP_DELTA_SECONDS = st.secrets.auth.time

# # --- CONFIG COOKIES ---
cookies = EncryptedCookieManager(prefix="dux-lesiones", password=JWT_SECRET)

if not cookies.ready():
    st.stop()

def init_app_state():
    ensure_session_defaults()
    if "flash" not in st.session_state:
        st.session_state["flash"] = None
        
    # Inicializa la página actual para el enrutamiento manual
    if 'current_page' not in st.session_state:
        st.session_state['current_page'] = "Inicio"

def ensure_session_defaults() -> None:
    """Initialize session state defaults for authentication and UI."""
    if "auth" not in st.session_state:
        st.session_state["auth"] = {
            "is_logged_in": False,
            "username": "",
            "rol": "",
            "token": ""
        }

def _get_credentials() -> tuple[str, str, str]:
    """Load credentials from environment or fallback to hardcoded defaults."""
    user = st.secrets.db.username
    pwd = st.secrets.db.password
    rol = st.secrets.db.rol
    return user, pwd, rol

def login_view() -> None:
    """Render the login form and handle authentication."""
    
    expected_user, expected_pass, rol = _get_credentials()
    
    _, col2, _ = st.columns([2, 1.5, 2])

    with col2:
        st.markdown("""
            <style>
                [data-testid="stSidebar"] {
                    display: none;
                    visibility: hidden;
                },
                [data-testid="st-emotion-cache-169dgwr edtmxes15"] {
                    display: none;
                    visibility: hidden;
                }
                [data-testid="stBaseButton-headerNoPadding"] {
                    display: none;
                    visibility: hidden;
                }
            </style>
        """, unsafe_allow_html=True)

        st.image("assets/images/banner.png")
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Usuario", value="")
            password = st.text_input("Contraseña", type="password", value="")
            submitted = st.form_submit_button("Iniciar sesión", type="primary")

        if submitted:
            if username == expected_user and password == expected_pass:

                token = create_jwt_token(username, rol)
                cookies["auth_token"] = token
                cookies.save()
                
                st.session_state["auth"]["is_logged_in"] = True
                st.session_state["auth"]["username"] = username
                st.session_state["auth"]["rol"] = rol
                st.session_state["auth"]["token"] = token

                st.success("Autenticado correctamente")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")

        st.caption("Usa usuario/contraseña proporcionados o variables de entorno TRAINER_USER/TRAINER_PASS")

def create_jwt_token(username: str, rol: str) -> str:
    """Crea un token JWT firmado con expiración."""
    payload = {
        "user": username,
        "rol": rol,
        "exp": time.time() + JWT_EXP_DELTA_SECONDS,
        "iat": time.time()
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token

def get_current_user():
    """Valida token de cookie o session_state y devuelve usuario si es válido."""
    token = st.session_state['auth']['token'] or cookies.get("auth_token")

    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        st.session_state["auth"]["is_logged_in"] = True
        st.session_state["auth"]["username"] = payload["user"]
        st.session_state["auth"]["rol"] = payload["rol"]
        st.session_state["auth"]["token"] = token
        
        return payload["user"]
    except jwt.ExpiredSignatureError:
        logout()
        return None
    except jwt.InvalidTokenError:
        logout()
        return None

def validate_login():
    username = get_current_user()
    if not username:
        return False
    return username

def menu():
    # Esta función ahora SOLO crea el menú y guarda la selección.
    with st.sidebar:
        st.logo("assets/images/banner.png", size="large")
        st.subheader("Entrenador :material/admin_panel_settings:")
        
        st.write(f"Hola **:blue-background[{st.session_state['auth']['username'].capitalize()}]** ")
        
        # 🛑 AQUÍ ESTÁ EL MENÚ CON ENRUTAMIENTO MANUAL
        page_options = ["Inicio", "Registrar Lesion", "Epidemiología", "Historico", "Reporte individual"]
        
        # Encuentra el índice de la página actual
        try:
            default_index = page_options.index(st.session_state.current_page)
        except ValueError:
            default_index = 0

        st.markdown("---")
        st.subheader("Modo :material/dashboard:")
        
        page = st.sidebar.radio(
            "Navegación",
            page_options,
            index=default_index,
            key='menu_selection'
        )

        st.session_state.current_page = page # Guarda la selección
        st.markdown("---")
        
        if st.session_state["auth"]["rol"] == "developer":
            st.page_link("pages/admin.py", label="Admin", icon=":material/app_registration:")
        
        btnSalir = st.button("Cerrar Sesión", type="tertiary", icon=":material/logout:")

        if btnSalir:
            logout()
    
    # IMPORTANTE: Ya no hay bloque IF/ELIF aquí. El router se moverá a app.py.


def logout():
    """Elimina sesión y cookie."""
    st.session_state["auth"] = {"is_logged_in": False, "username": "", "token": "", "rol": ""}
    cookies["auth_token"] = ""
    cookies.save()

    st.rerun()
