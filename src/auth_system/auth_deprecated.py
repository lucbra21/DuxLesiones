import streamlit as st

import jwt
import time
from st_cookies_manager import EncryptedCookieManager
from src.db_login import load_user_from_db
import bcrypt

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

def ensure_session_defaults() -> None:
    """Initialize session state defaults for authentication and UI."""
    if "auth" not in st.session_state:
        st.session_state["auth"] = {
            "is_logged_in": False,
            "username": "",
            "rol": "",
            "token": ""
        }

# def _get_credentials() -> tuple[str, str, str]:
#     """Load credentials from environment or fallback to hardcoded defaults.

#     Environment variables (optional): TRAINER_USER, TRAINER_PASS
#     Defaults: admin / admin
#     """
#     user = st.secrets.db.username
#     pwd = st.secrets.db.password
#     rol = st.secrets.db.rol
#     return user, pwd, rol

def login_view() -> None:
    """Render the login form and handle authentication."""
    
    #password = "duxlogrono."

    # # Generar hash (bytes)
    #hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    # # Mostrar (solo para pruebas; en prod NO mostrar hashes)
    #st.text(hashed.decode("utf-8"))

    # # Verificar: primer arg = contraseña en texto plano (bytes), segundo arg = hash (bytes)
    # is_ok = bcrypt.checkpw(password.encode("utf-8"), hashed)
    # st.text(f"¿Contraseña válida? {is_ok}")  # True

    #users = load_users()
    #expected_user, expected_pass, rol = _get_credentials()
    
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

        #st.header('Login :red[Entrenador]')
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
            
            #user_data = next((u for u in users if u["username"] == username and u["password"] == password), None)
            #if username == expected_user and password == expected_pass:
            if user_data:
                validate_password(password, user_data)
                
                #rol = user_data["rol"]
                #token = create_jwt_token(username, rol)
                # cookies["auth_token"] = token
                # cookies.save()
                
                # st.session_state["auth"]["is_logged_in"] = True
                # st.session_state["auth"]["username"] = username
                # st.session_state["auth"]["rol"] = rol
                # st.session_state["auth"]["token"] = token

                # st.success("Autenticado correctamente")
                # st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")

        #st.caption("Usa usuario/contraseña proporcionados o variables de entorno TRAINER_USER/TRAINER_PASS")

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

def validate_password(password, user):
    # Verificar contraseña
    if bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        token = create_jwt_token(user["email"], user["role_name"])
        st.session_state["auth"] = {
            "is_logged_in": True,
            "username": user["email"],
            "rol": user["role_name"].lower(),
            "nombre": f"{user['name']} {user['lastname']}".strip(),
            "token": token
        }
        cookies["auth_token"] = token
        cookies.save()
        st.success(":material/check: Autenticado correctamente.")
        st.rerun()
    else:
        st.error("Usuario o contraseña incorrectos")

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

def logout():
    """Elimina sesión y cookie."""
    st.session_state["auth"] = {"is_logged_in": False, "username": "", "token": "", "rol": ""}
    cookies["auth_token"] = ""
    cookies.save()

    st.rerun()