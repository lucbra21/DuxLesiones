
import streamlit as st
import plotly.express as px
import pandas as pd
from src.i18n.i18n import t

from src.util import (get_photo, clean_image_url, calcular_edad)

def player_block_dux(jugadora_seleccionada: dict, unavailable="N/A"):
    """Muestra el bloque visual con la información principal de la jugadora."""

    # Validar jugadora seleccionada
    if not jugadora_seleccionada or not isinstance(jugadora_seleccionada, dict):
        st.info(t("Selecciona una jugadora para continuar."))
        st.stop()
    
    #st.dataframe(jugadora_seleccionada)
    # Extraer información básica
    nombre = jugadora_seleccionada.get("nombre", unavailable).strip().upper()
    apellido = jugadora_seleccionada.get("apellido", "").strip().upper()
    nombre_completo = f"{nombre.capitalize()} {apellido.capitalize()}"
    id_jugadora = jugadora_seleccionada.get("identificacion", unavailable)
    posicion = jugadora_seleccionada.get("posicion", unavailable)
    pais = jugadora_seleccionada.get("nacionalidad", unavailable)
    fecha_nac = jugadora_seleccionada.get("fecha_nacimiento", unavailable)
    genero = jugadora_seleccionada.get("genero", "")
    competicion = jugadora_seleccionada.get("plantel", "")
    dorsal = jugadora_seleccionada.get("dorsal", "")
    url_drive = jugadora_seleccionada.get("foto_url", "")

    dorsal_number = f":red[/ Dorsal #{int(dorsal)}]" if pd.notna(dorsal) else ""

    # Calcular edad
    edad_texto, fnac = calcular_edad(fecha_nac)

    # Color temático
    #color = "violet" if genero.upper() == "F" else "blue"

    # Icono de género
    if genero.upper() == "F":
        genero_icono = ":material/girl:"
        profile_image = "female"
    elif genero.upper() == "H":
        genero_icono = ":material/boy:"
        profile_image = "male"
    else:
        genero_icono = ""
        profile_image = "profile"

    # Bloque visual
    st.markdown(f"### {nombre_completo.title()} {dorsal_number}")
    #st.markdown(f"##### **_:red[Identificación:]_** _{id_jugadora}_ | **_:red[País:]_** _{pais.upper()}_")

    col1, col2, col3 = st.columns([1.6, 2, 2])

    with col1:
        if pd.notna(url_drive) and url_drive and url_drive != "No Disponible":
            direct_url = clean_image_url(url_drive)
            #st.text(direct_url)
            response = get_photo(direct_url)
            if response and response.status_code == 200 and 'image' in response.headers.get("Content-Type", ""):
                st.image(response.content, width=300)
            else:
                st.image(f"assets/images/{profile_image}.png", width=300)
        else:
            st.image(f"assets/images/{profile_image}.png", width=300)

    with col2:
        #st.markdown(f"**:material/sports_soccer: Competición:** {competicion}")
        #st.markdown(f"**:material/cake: Fecha Nac.:** {fecha_nac}")

        st.metric(label=t(":red[:material/id_card: Identificación]"), value=f"{id_jugadora}", border=True)
        st.metric(label=t(":red[:material/sports_soccer: Plantel]"), value=f"{competicion}", border=True)
        st.metric(label=t(":red[:material/cake: F. Nacimiento]"), value=f"{fecha_nac}", border=True)
                    
    with col3:
        #st.markdown(f"**:material/person: Posición:** {posicion.capitalize()}")
        #st.markdown(f"**:material/favorite: Edad:** {edad if edad != unavailable else 'N/A'} años")

        st.metric(label=t(":red[:material/globe: País]"), value=f"{pais if pais else 'N/A'}", border=True)
        st.metric(label=t(":red[:material/person: Posición]"), value=f"{posicion.capitalize() if posicion else 'N/A'}", border=True)
        st.metric(label=t(":red[:material/favorite: Edad]"), value=f"{edad_texto}", border=True)
          
    st.divider()

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
        title=t("Evolución temporal de lesiones")
    )
    fig.update_layout(
        xaxis_title=t("Fecha de lesión"),
        yaxis_title=t("Días de baja estimados"),
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
        title=t("Zonas corporales más lesionadas")
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
        title=t("Relación entre tipo de lesión y mecanismo"),
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
    for tr in df["tipo_tratamiento"]:
        if isinstance(tr, list):
            tratamientos.extend(tr)
        elif isinstance(tr, str) and tr.strip():
            tratamientos.extend([x.strip() for x in tr.split(",")])

    conteo = Counter(tratamientos)
    df_t = pd.DataFrame(conteo.items(), columns=["Tratamiento", "Frecuencia"]).sort_values("Frecuencia", ascending=True)

    fig = px.bar(
        df_t,
        x="Frecuencia",
        y="Tratamiento",
        orientation="h",
        color="Frecuencia",
        color_continuous_scale="Blues",
        title=t("Tratamientos más utilizados")
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
        title=t("Días de baja según impacto o severidad"),
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
        title=t("Proporción de recidivas vs nuevas")
    )
    fig.update_layout(template="simple_white", height=350)
    return fig

