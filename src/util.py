import requests
import plotly.express as px
import pandas as pd

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
    "posicion",
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
    "tipo_recidiva"
    ]
    # --- eliminar columnas si existen ---
    df_filtrado = records.drop(columns=[col for col in columnas_excluir if col in records.columns])

    orden = ["fecha_lesion", "nombre_jugadora", "id_lesion", "lugar", "segmento", "zona_cuerpo", "zona_especifica", "lateralidad", "tipo_lesion", "tipo_especifico", "gravedad", "personal_reporta", "estado_lesion"]
    
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
        color="gravedad_clinica",
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
    """Boxplot que muestra la distribución de días de baja por nivel de gravedad clínica."""
    if df.empty:
        return None

    fig = px.box(
        df,
        x="gravedad_clinica",
        y="dias_baja_estimado",
        color="gravedad_clinica",
        title="Días de baja según gravedad clínica",
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    fig.update_layout(
        xaxis_title="Gravedad clínica",
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
