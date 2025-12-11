import streamlit as st

import math
import re
import numpy as np
import requests
import pandas as pd
import json

import datetime
from pathlib import Path
from urllib.parse import urlparse, urlunparse
import base64
import re
import unicodedata
import datetime
from dateutil.relativedelta import relativedelta  # pip install python-dateutil

def normalize_text(s):
    """Limpia texto eliminando tildes, espacios invisibles y normalizando Unicode."""
    if not isinstance(s, str):
        return ""
    s = s.strip().upper()
    s = unicodedata.normalize("NFKC", s)  # Normaliza forma Unicode
    return s

def get_normalized_treatment(lesion_data):
    """
    Normaliza el campo tipo_tratamiento, admitiendo tanto JSON string como lista.
    """
    tipo_tratamiento_raw = lesion_data.get("tipo_tratamiento", "[]")

    # --- Detectar tipo de dato recibido ---
    if isinstance(tipo_tratamiento_raw, list):
        tratamientos_default = tipo_tratamiento_raw
    elif isinstance(tipo_tratamiento_raw, str):
        try:
            tratamientos_default = json.loads(tipo_tratamiento_raw)
        except json.JSONDecodeError:
            # Si no es JSON válido, lo tratamos como texto plano
            tratamientos_default = [tipo_tratamiento_raw.strip()]
    else:
        tratamientos_default = []

    #st.text(f"tratamientos_default raw: {tipo_tratamiento_raw}")
    #st.text(f"tratamientos_default parsed: {tratamientos_default}")

    # --- Normalizar texto final ---
    tratamientos_default = [
        str(t).strip().upper() for t in tratamientos_default if t
    ]

    return tratamientos_default

def get_photo(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Verifica si hubo un error (por ejemplo, 404 o 500)
    except requests.exceptions.RequestException:
        response = None  # Si hay un error, no asignamos nada a response

    return response

def centered_text(text : str):
        st.markdown(f"<h3 style='text-align: center;'>{text}</span></h3>",unsafe_allow_html=True)

def right_caption(text: str):
    st.markdown(
        f"""
        <p style='text-align: right; font-size: 0.85rem; color: #666;'>
            {text}
        </p>
        """,
        unsafe_allow_html=True
    )

def clean_df(records):
    columnas_excluir = [
        "id_registro",
        "id_jugadora",
        "fecha_hora",
        #"posicion",
        #"tipo_tratamiento",
        "diagnostico",
        "descripcion",
        "fecha",
        "fecha_dia",
        "evolucion",
        "mecanismo",
        "mecanismo_id",
        "dias_baja_estimado",
        "fecha_alta_lesion",
        "fecha_alta_diagnostico",
        "fecha_hora_registro",
        "periodo",
        "es_recidiva",
        "tipo_recidiva",
        "evolucion",
        "periodo",
        "lugar_id",
        "segmento_id",
        "zona_cuerpo_id",
        "zona_especifica_id",
        "id",
        "impacto_dias_baja_estimado",
        "nombre",
        "apellido"
        #"usuario"
    ]
    # --- eliminar columnas si existen ---
    df_filtrado = records.drop(columns=[col for col in columnas_excluir if col in records.columns])

    orden = ["fecha_lesion", "nombre_jugadora", "posicion", "plantel" ,"id_lesion", "lugar", "segmento", "zona_cuerpo", "zona_especifica", "lateralidad", "tipo_lesion", "tipo_especifico", "gravedad", "tipo_tratamiento", "personal_reporta", "estado_lesion", "sesiones"]
    
    # Solo mantener columnas que realmente existen
    orden_existentes = [c for c in orden if c in df_filtrado.columns]

    df_filtrado = df_filtrado[orden_existentes + [c for c in df_filtrado.columns if c not in orden_existentes]]
        
    #df_filtrado = df_filtrado[orden + [c for c in df_filtrado.columns if c not in orden]]

    df_filtrado = df_filtrado.sort_values("fecha_lesion", ascending=False)
    df_filtrado.reset_index(drop=True, inplace=True)
    df_filtrado.index = df_filtrado.index + 1
    return df_filtrado

def calcular_edad(fecha_nac):
    try:
        # Si viene como string -> convertir
        if isinstance(fecha_nac, str):
            fnac = datetime.datetime.strptime(fecha_nac, "%Y-%m-%d").date()
        elif isinstance(fecha_nac, datetime.date):
            fnac = fecha_nac
        else:
            return "N/A", None

        hoy = datetime.date.today()
        diff = relativedelta(hoy, fnac)

        edad_anos = diff.years
        edad_meses = diff.months

        edad_texto = f"{edad_anos} años y {edad_meses} meses"
        return edad_texto, fnac

    except Exception as e:
        return f"Error: {e}", None

def clean_image_url(url: str) -> str:
    """
    Limpia y normaliza URLs de imágenes:
    - Si es de Google Drive, la convierte a formato directo de descarga/visualización.
    - Si tiene parámetros (como '?size=...' o '&lossy=1'), los elimina.
    - Si ya es una URL limpia, la devuelve igual.
    """

    if not url or not isinstance(url, str):
        return ""

    # --- 1️⃣ Caso Google Drive ---
    if "drive.google.com" in url:
        # Caso A: /file/d/<ID>/view?usp=sharing
        match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
        if match:
            file_id = match.group(1)
            return f"https://drive.google.com/uc?id={file_id}"

        # Caso B: open?id=<ID>
        match = re.search(r"id=([a-zA-Z0-9_-]+)", url)
        if match:
            file_id = match.group(1)
            return f"https://drive.google.com/uc?id={file_id}"

        # Si no encuentra ID, devuelve sin cambios
        return url

    # --- 2️⃣ Caso URLs con parámetros (ej. cdn.resfu.com) ---
    parsed = urlparse(url)
    # Elimina los parámetros de consulta (?size=...&lossy=...)
    clean_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))

    return clean_url

def get_drive_direct_url(url: str) -> str:
    """
    Convierte un enlace de Google Drive en un enlace directo para visualizar o descargar la imagen.

    Args:
        url (str): Enlace de Google Drive (por ejemplo, 'https://drive.google.com/file/d/.../view?usp=sharing')

    Returns:
        str: Enlace directo usable en st.image o <img src="...">
    """
    if not url:
        return ""

    # Detectar si contiene el patrón de ID
    if "drive.google.com" not in url:
        raise ValueError("La URL no parece ser de Google Drive")

    # Buscar el ID del archivo
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    if not match:
        raise ValueError("No se pudo extraer el ID del archivo de la URL")

    file_id = match.group(1)
    return f"https://drive.google.com/uc?export=view&id={file_id}"

def load_lesiones_jsonl(path: str | Path) -> tuple[pd.DataFrame | None, str | None]:
    """
    Carga un archivo JSONL de lesiones y lo convierte en un DataFrame.

    Parámetros
    ----------
    path : str | Path
        Ruta del archivo 'lesiones.jsonl' que contiene los registros de lesiones.

    Retorna
    -------
    tuple[pd.DataFrame | None, str | None]
        - DataFrame con las lesiones si la carga es exitosa.
        - Mensaje de error si ocurre algún problema.
    """
    try:
        path = Path(path)
        if not path.exists():
            return None, f"Archivo no encontrado: {path}"

        data = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue

        if not data:
            return None, "El archivo no contiene registros válidos."

        df = pd.DataFrame(data)

        # Asegurar tipos de datos y ordenar por fecha de diagnóstico
        if "fecha_alta_diagnostico" in df.columns:
            df["fecha_alta_diagnostico"] = pd.to_datetime(df["fecha_alta_diagnostico"], errors="coerce")
            df = df.sort_values("fecha_alta_diagnostico", ascending=False)

        return df.reset_index(drop=True), None

    except Exception as e:
        return None, f"Error al cargar el archivo de lesiones: {e}"

def parse_fecha(value):
    """
    Convierte un valor en objeto datetime.date de forma segura.

    Acepta:
        - str en formato ISO ('YYYY-MM-DD' o 'YYYY-MM-DDTHH:MM:SS')
        - datetime.date
        - datetime.datetime
        - None o vacío

    Devuelve:
        datetime.date | None
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return None

    if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
        # Ya es un objeto date
        return value

    if isinstance(value, datetime.datetime):
        # Extraer solo la parte de fecha
        return value.date()

    if isinstance(value, str):
        try:
            # Intentar formato ISO estándar
            return datetime.date.fromisoformat(value.split("T")[0])
        except Exception:
            try:
                # Intentar otros formatos comunes (por compatibilidad)
                return datetime.datetime.strptime(value, "%Y-%m-%d").date()
            except Exception:
                return None

    # Si no es ningún tipo compatible
    return None

def get_gravedad_por_dias(dias_baja_estimado: float, gravedad_dias: dict) -> tuple[str | None, tuple[float | None, float | None]]:
    """
    Determina el nivel de gravedad según los días estimados de baja.

    Args:
        dias_baja_estimado (float): Días de baja estimados (puede venir de RPE o diagnóstico).
        gravedad_dias (dict): Diccionario con niveles de gravedad y sus rangos de días.
                              Ejemplo: {"Leve": (1, 3), "Moderada": (4, 7), "Grave": (8, None)}

    Returns:
        tuple:
            - gravedad (str | None): Nivel de gravedad encontrado o None si no coincide.
            - rango (tuple): Rango de días correspondiente al nivel encontrado.
    """

    if dias_baja_estimado is None or pd.isna(dias_baja_estimado):
        return None, (None, None)

    for nivel, (min_dias, max_dias) in gravedad_dias.items():
        # Saltar rangos completamente vacíos
        if pd.isna(min_dias) and pd.isna(max_dias):
            continue

        # Caso: sin límite superior (max_dias vacío o NaN)
        if pd.isna(max_dias) or max_dias is None:
            if not pd.isna(min_dias) and dias_baja_estimado >= min_dias:
                return nivel, (min_dias, max_dias)

        # Caso: rango cerrado válido
        elif not pd.isna(min_dias) and min_dias <= dias_baja_estimado <= max_dias:
            return nivel, (min_dias, max_dias)

    # Si no entra en ningún rango
    return None, (None, None)

def is_valid(value):
    """Devuelve True si el valor no es None, vacío ni NaN."""
    if value is None:
        return False
    if isinstance(value, str) and value.strip() == "":
        return False
    if isinstance(value, (float, np.floating)) and math.isnan(value):
        return False
    if pd.isna(value):  # cubre np.nan, pd.NaT y similares
        return False
    return True

def to_date(value):
    """Convierte una cadena o datetime a date (YYYY-MM-DD)."""
    if isinstance(value, datetime.date):
        return value
    try:
        return pd.to_datetime(value, errors="coerce").date()
    except Exception:
        return None
    
def date_to_str(fecha):
    if isinstance(fecha, (datetime.date, datetime.datetime)):
        return fecha.strftime("%Y-%m-%d")
    elif isinstance(fecha, str):
        return fecha  
    else:
        return None

def generar_id_lesion(nombre: str, id_jugadora: str, ultima_lesion_id: str | None = None, fecha: str | None = None) -> str:
    """
    Genera un identificador único de lesión para una jugadora.
    Formato: <INICIALES><YYYYMMDD>-<INCREMENTAL>
    
    - nombre: Nombre completo de la jugadora (en mayúsculas o minúsculas)
    - id_jugadora: Identificador único de la jugadora
    - ultima_lesion_id: ID de la última lesión registrada (si existe)
    - fecha: Fecha opcional (formato 'YYYYMMDD'). Si no se pasa, usa la actual.
    """

    # --- Obtener iniciales ---
    partes = nombre.strip().split()
    iniciales = "".join(p[0].upper() for p in partes if p)

    # --- Fecha actual o pasada ---
    if fecha is None:
        fecha = datetime.datetime.now().strftime("%Y%m%d")

    # --- Determinar número incremental ---
    if not ultima_lesion_id:  # si no hay lesiones previas
        numero = 1
    else:
        # Extraer número final del ID existente (después del guion)
        match = re.search(r"-(\d+)$", ultima_lesion_id)
        if match:
            numero = int(match.group(1)) + 1
        else:
            numero = 1  # si no tiene formato esperado, reinicia en 1

    # --- Construir ID ---
    nuevo_id = f"{iniciales}{fecha}-{numero}"
    return nuevo_id

def sanitize_lesion_data(lesion_data: dict) -> dict:
    """
    Limpia y normaliza los campos de una lesión cargada desde la BD.
    Convierte todas las fechas a string ISO ('YYYY-MM-DD') o ('YYYY-MM-DDTHH:MM:SS')
    y decodifica los campos JSON.
    """
    clean = {}

    for k, v in lesion_data.items():

        # --- Campos de fecha pura ---
        if k in ("fecha_lesion", "fecha_alta_diagnostico", "fecha_alta_medica", "fecha_alta_deportiva"):
            parsed_date = parse_fecha(v)
            clean[k] = parsed_date.isoformat() if parsed_date else None

        # --- Campo con fecha y hora ---
        elif k == "fecha_hora_registro":
            if isinstance(v, pd.Timestamp):
                clean[k] = v.to_pydatetime().isoformat()
            elif isinstance(v, datetime.datetime):
                clean[k] = v.isoformat()
            elif isinstance(v, datetime.date):
                clean[k] = datetime.datetime.combine(v, datetime.time.min).isoformat()
            elif isinstance(v, str):
                # Si ya es una cadena válida, mantenerla
                clean[k] = v.strip()
            else:
                clean[k] = datetime.datetime.now().isoformat()

        # --- JSON almacenado como texto ---
        elif isinstance(v, str) and v.strip().startswith("["):
            try:
                clean[k] = json.loads(v)
            except json.JSONDecodeError:
                clean[k] = v

        else:
            clean[k] = v

    return clean

def contar_sesiones(evol_raw):
    
    """Cuenta cuántas sesiones tiene una evolución (campo JSON o lista)."""
    if not evol_raw:
        return 0
    if isinstance(evol_raw, str):
        try:
            evol_list = json.loads(evol_raw)
        except json.JSONDecodeError:
            return 0
    elif isinstance(evol_raw, list):
        evol_list = evol_raw
    else:
        return 0

    return len(evol_list) if isinstance(evol_list, list) else 0

def set_background_image_local(image_path: str, fixed: bool = False, overlay: float = 0.0):
    """
    Aplica una imagen de fondo local a toda la app Streamlit usando Base64.
    
    Parámetros:
        image_path (str): Ruta de la imagen local. Ej: "assets/images/banner.jpg"
        fixed (bool): Si True, fondo con efecto parallax (fixed).
        overlay (float): Oscurecer fondo (0.0 = sin overlay, 0.0–1.0 máximo).
    """

    # Convertir imagen local a Base64
    with open(image_path, "rb") as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode()

    attachment = "fixed" if fixed else "scroll"

    overlay_css = ""
    if overlay > 0:
        overlay_css = f"""
        [data-testid="stAppViewContainer"]::before {{
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,{overlay});
            z-index: 0;
        }}
        [data-testid="stAppViewContainer"] > * {{
            position: relative;
            z-index: 1;
        }}
        """

    css = f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: url("data:image/jpg;base64,{img_base64}");
        background-size: cover;
        background-repeat: no-repeat;
        background-position: center center;
        background-attachment: {attachment};
    }}

    [data-testid="stHeader"] {{
        background: rgba(0,0,0,0);
    }}

    {overlay_css}
    </style>
    """

    st.markdown(css, unsafe_allow_html=True)

def set_background_image(image_url: str, fixed: bool = False, overlay: float = 0.0):
    """
    Aplica una imagen de fondo a toda la app Streamlit.

    Parámetros:
        image_url (str): URL o ruta local de la imagen.
        fixed (bool): Si True, el fondo queda fijo (efecto parallax).
        overlay (float): Oscurecer fondo (0.0 = sin overlay, 0.0–1.0).
    """

    attachment = "fixed" if fixed else "scroll"

    overlay_css = ""
    if overlay > 0:
        overlay_css = f"""
        [data-testid="stAppViewContainer"]::before {{
            content: "";
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,{overlay});
            z-index: 0;
        }}
        [data-testid="stAppViewContainer"] > * {{
            position: relative;
            z-index: 1;
        }}
        """

    css = f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: url("{image_url}");
        background-size: cover;
        background-repeat: no-repeat;
        background-position: center center;
        background-attachment: {attachment};
    }}

    [data-testid="stHeader"] {{
        background: rgba(0,0,0,0);
    }}

    {overlay_css}
    </style>
    """

    st.markdown(css, unsafe_allow_html=True)
