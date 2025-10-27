import math
import re
import numpy as np
import requests
import plotly.express as px
import pandas as pd
import json
import random
import datetime
from pathlib import Path
import streamlit as st

from src.schema import reglas_desactivar_subtipo
import unicodedata

def normalize_text(s):
    """Limpia texto eliminando tildes, espacios invisibles y normalizando Unicode."""
    if not isinstance(s, str):
        return ""
    s = s.strip().upper()
    s = unicodedata.normalize("NFKC", s)  # Normaliza forma Unicode
    return s

import json
import streamlit as st

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
    import re
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", url)
    if not match:
        raise ValueError("No se pudo extraer el ID del archivo de la URL")

    file_id = match.group(1)
    return f"https://drive.google.com/uc?export=view&id={file_id}"

def grafico_evolucion_lesiones(df: pd.DataFrame):
    """Muestra una línea temporal de lesiones con color por gravedad y tamaño según días de baja."""
    if df.empty:
        return None

    df = df.copy()
    df["fecha_lesion"] = pd.to_datetime(df["fecha_lesion"], errors="coerce")

    # Filtrar solo las columnas que existen
    hover_cols = [col for col in ["tipo_lesion", "zona_cuerpo", "mecanismo", "descripcion"] if col in df.columns]

    fig = px.scatter(
        df.sort_values("fecha_lesion"),
        x="fecha_lesion",
        y="dias_baja_estimado",
        color="impacto_dias_baja_estimado",
        size="dias_baja_estimado",
        hover_data=hover_cols,
        color_discrete_sequence=px.colors.qualitative.Safe,
        title="Evolución temporal de lesiones"
    )
    fig.update_layout(
        xaxis_title="Fecha de lesión",
        yaxis_title="Días de baja estimados",
        template="simple_white",
        height=400
    )
    return fig

def grafico_zonas_lesionadas(df: pd.DataFrame):
    """Bar chart horizontal de zonas corporales más lesionadas."""
    if df.empty:
        return None

    zonas = df["zona_cuerpo"].value_counts().reset_index()
    zonas.columns = ["Zona corporal", "Frecuencia"]

    fig = px.bar(
        zonas,
        x="Frecuencia",
        y="Zona corporal",
        orientation="h",
        color="Frecuencia",
        color_continuous_scale="Reds",
        title="Zonas corporales más lesionadas"
    )
    fig.update_layout(template="simple_white", height=400)
    return fig

def grafico_tipo_mecanismo(df: pd.DataFrame):
    """Comparación entre tipo de lesión y mecanismo."""
    if df.empty:
        return None

    fig = px.histogram(
        df,
        x="tipo_lesion",
        color="mecanismo",
        barmode="group",
        title="Relación entre tipo de lesión y mecanismo",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_layout(
        xaxis_title="Tipo de lesión",
        yaxis_title="Frecuencia",
        template="simple_white",
        height=400
    )
    return fig

from collections import Counter

def grafico_tratamientos(df: pd.DataFrame):
    """Muestra la frecuencia de uso de tratamientos aplicados."""
    if df.empty or "tipo_tratamiento" not in df.columns:
        return None

    tratamientos = []
    for t in df["tipo_tratamiento"]:
        if isinstance(t, list):
            tratamientos.extend(t)
        elif isinstance(t, str) and t.strip():
            tratamientos.extend([x.strip() for x in t.split(",")])

    conteo = Counter(tratamientos)
    df_t = pd.DataFrame(conteo.items(), columns=["Tratamiento", "Frecuencia"]).sort_values("Frecuencia", ascending=True)

    fig = px.bar(
        df_t,
        x="Frecuencia",
        y="Tratamiento",
        orientation="h",
        color="Frecuencia",
        color_continuous_scale="Blues",
        title="Tratamientos más utilizados"
    )
    fig.update_layout(template="simple_white", height=400)
    return fig

def grafico_dias_baja(df: pd.DataFrame):
    """Boxplot que muestra la distribución de días de baja por nivel de impacto o severidad."""
    if df.empty:
        return None

    fig = px.box(
        df,
        x="impacto_dias_baja_estimado",
        y="dias_baja_estimado",
        color="impacto_dias_baja_estimado",
        title="Días de baja según impacto o severidad",
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    fig.update_layout(
        xaxis_title="Impacto o Severidad",
        yaxis_title="Días de baja",
        template="simple_white",
        height=400
    )
    return fig

def grafico_recidivas(df: pd.DataFrame):
    """Pie chart de proporción de lesiones recidivantes vs nuevas."""
    if df.empty or "es_recidiva" not in df.columns:
        return None

    conteo = df["es_recidiva"].map({True: "Recidiva", False: "Nueva"}).value_counts().reset_index()
    conteo.columns = ["Tipo", "Frecuencia"]

    fig = px.pie(
        conteo,
        names="Tipo",
        values="Frecuencia",
        color="Tipo",
        color_discrete_sequence=px.colors.qualitative.Set2,
        title="Proporción de recidivas vs nuevas"
    )
    fig.update_layout(template="simple_white", height=350)
    return fig

def debe_deshabilitar_subtipo(mecanismo: str, tipo: str) -> bool:
    """
    Determina si debe deshabilitarse el selector de tipo específico 
    según las reglas clínicas establecidas.
    """
    return any(
        r["mecanismo"] == mecanismo and r["tipo"] == tipo
        for r in reglas_desactivar_subtipo
    )

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

def generar_lesiones_aleatorias(
    jugadoras_path: str,
    output_dir: str = "data",
    lesiones_por_jugadora: int = 10
) -> Path:
    """
    Genera lesiones aleatorias para cada jugadora y guarda los datos en un archivo JSONL.
    Si el archivo no existe, se crea uno nuevo con el nombre 'lesiones_YYYY-MM-DD_HHMM.jsonl'.

    Compatible tanto con formato JSON estándar (lista []) como JSONL (una jugadora por línea).
    """

    jugadoras = []
    with open(jugadoras_path, "r", encoding="utf-8") as f:
        content = f.read().strip()

        try:
            # Si es una lista JSON estándar
            parsed = json.loads(content)
            if isinstance(parsed, list):
                jugadoras = parsed
            elif isinstance(parsed, dict):
                jugadoras = [parsed]
        except json.JSONDecodeError:
            # Si no es JSON válido, intentar como JSONL
            for line in content.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    jugadoras.append(json.loads(line))
                except json.JSONDecodeError:
                    print(f"⚠️ Línea ignorada (no es JSON válido): {line[:40]}...")

    if not jugadoras:
        raise ValueError(f"No se encontraron jugadoras válidas en {jugadoras_path}")

    # --- Listas de opciones según tu app ---
    estados = ["ACTIVO", "INACTIVO"]
    zonas = ["Cabeza", "Cuello", "Tronco", "Hombro", "Codo", "Muñeca", "Mano",
             "Cadera", "Ingle", "Rodilla", "Tobillo", "Pie", "Muslo", "Pierna"]
    gravedades = ["Leve", "Moderada", "Grave"]
    tipos_lesion = ["Muscular", "Ósea", "Tendinosa", "Articular", "Ligamentosa", "Contusión"]
    mecanismos = ["Entrenamiento", "Partido", "Gimnasio", "Otro"]
    lateralidades = ["Derecha", "Izquierda", "Bilateral"]
    tratamientos = ["Fisioterapia", "Medicación", "Gimnasio", "Cirugía", "Reposo", "Readaptación"]

    today = datetime.date.today()
    lesiones = []

    for j in jugadoras:
        id_j = j.get("id_jugadora") or j.get("id") or str(random.randint(1000, 9999))
        nombre_j = j.get("nombre_jugadora") or j.get("nombre") or "Desconocida"

        for _ in range(lesiones_por_jugadora):
            dias_baja = random.randint(3, 45)
            fecha_inicio = today - datetime.timedelta(days=random.randint(1, 180))
            fecha_diagnostico = fecha_inicio + datetime.timedelta(days=random.randint(2, 7))
            fecha_alta_real = fecha_diagnostico + datetime.timedelta(days=dias_baja)

            lesion = {
                "id_jugadora": id_j,
                "nombre_jugadora": nombre_j,
                "estado_lesion": random.choice(estados),
                "zona_cuerpo": random.choice(zonas),
                "fecha_alta_diagnostico": fecha_diagnostico.isoformat(),
                "gravedad": random.choice(gravedades),
                "dias_baja_estimado": dias_baja,
                "fecha_alta_lesion": fecha_alta_real.isoformat(),
                "tipo_lesion": random.choice(tipos_lesion),
                "mecanismo": random.choice(mecanismos),
                "personal_reporta": random.choice(["Dr. López", "Dra. García", "Fisio Martín", "Dra. Pérez"]),
                "lateralidad": random.choice(lateralidades),
                "tipo_tratamiento": random.sample(tratamientos, k=random.randint(1, 3))
            }
            lesiones.append(lesion)

    # --- Crear archivo dinámico ---
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M")
    output_path = Path(output_dir) / f"lesiones_{timestamp}.jsonl"

    with open(output_path, "w", encoding="utf-8") as f:
        for lesion in lesiones:
            f.write(json.dumps(lesion, ensure_ascii=False) + "\n")

    #print(f"✅ Generadas {len(lesiones)} lesiones en: {output_path}")
    return output_path

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