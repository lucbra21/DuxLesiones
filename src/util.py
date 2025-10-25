import requests
import plotly.express as px
import pandas as pd
import json
import random
import datetime
from pathlib import Path

from src.schema import reglas_desactivar_subtipo

def get_photo(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Verifica si hubo un error (por ejemplo, 404 o 500)
    except requests.exceptions.RequestException:
        response = None  # Si hay un error, no asignamos nada a response

    return response

def clean_df(records):
    columnas_excluir = [
    "id_jugadora",
    "fecha_hora",
    #"posicion",
    "tipo_tratamiento",
    "diagnostico",
    "descripcion",
    "fecha",
    "fecha_dia",
    "evolucion",
    "mecanismo_lesion",
    "dias_baja_estimado",
    "fecha_alta_lesion",
    "fecha_alta_diagnostico",
    "fecha_hora_registro",
    "periodo",
    "es_recidiva",
    "tipo_recidiva",
    "evolucion",
    "periodo"
    #"usuario"
    ]
    # --- eliminar columnas si existen ---
    df_filtrado = records.drop(columns=[col for col in columnas_excluir if col in records.columns])

    orden = ["fecha_lesion", "nombre_jugadora", "posicion", "plantel" ,"id_lesion", "lugar", "segmento", "zona_cuerpo", "zona_especifica", "lateralidad", "tipo_lesion", "tipo_especifico", "gravedad", "personal_reporta", "estado_lesion"]
    
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

    fig = px.scatter(
        df.sort_values("fecha_lesion"),
        x="fecha_lesion",
        y="dias_baja_estimado",
        color="impacto_dias_baja_estimado",
        size="dias_baja_estimado",
        hover_data=["tipo_lesion", "zona_cuerpo", "mecanismo_lesion"],
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
        color="mecanismo_lesion",
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
                "mecanismo_lesion": random.choice(mecanismos),
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

    print(f"✅ Generadas {len(lesiones)} lesiones en: {output_path}")
    return output_path

