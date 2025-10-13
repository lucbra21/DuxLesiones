import pandas as pd
import streamlit as st
import src.config as config
config.init_config()

from src.io_files import get_records_df, load_jugadoras, upsert_jsonl, load_competiciones

from src.auth import init_app_state, login_view, menu, validate_login
init_app_state()
validate_login()

# Authentication gate
if not st.session_state["auth"]["is_logged_in"]:
    login_view()
    st.stop()

st.header("Seguimiento de :red[Lesiones]", divider="red")

menu()

records = get_records_df()  # Carga y cachea los datos

if records.empty:    
    st.warning("No hay datos de lesiones disponibles.")
    st.stop()   
    
records["fecha_alta_diagnostico"] = pd.to_datetime(records["fecha_alta_diagnostico"], errors="coerce")

jug_df, jug_error = load_jugadoras()
comp_df, comp_error = load_competiciones()

col1, col2, col3 = st.columns([2,2,1])

with col1:
    competiciones_options = comp_df.to_dict("records")
    competicion = st.selectbox(
        "Competición",
        options=competiciones_options,
        format_func=lambda x: f'{x["nombre"]} ({x["codigo"]})',
        placeholder="Seleccione una Competición",
        #index=None
    )
    #jugadoras = sorted(records["nombre"].dropna().unique())
    #selected_jugadora = st.selectbox("Filtrar por jugadora", ["Todas"] + jugadoras)

with col2:

    if competicion:
        codigo_competicion = competicion["codigo"]
        jug_df_filtrado = jug_df[jug_df["competicion"] == codigo_competicion]

        # Convertir el DataFrame filtrado a lista de opciones
        jugadoras_filtradas = jug_df_filtrado.to_dict("records")
    else:
        jugadoras_filtradas = jug_df.to_dict("records")

    # La nueva columna para el nombre de la jugadora
    jugadora_seleccionada = st.selectbox(
        "Jugadora",
        options=jugadoras_filtradas,
        format_func=lambda x: f'{jugadoras_filtradas.index(x) + 1} - {x["nombre"]} {x["apellido"]}',
        placeholder="Seleccione una Jugadora",
        index=None
    )
    # Filtro por rango de fechas
    # min_fecha = records["fecha_alta_diagnostico"].min()
    # max_fecha = records["fecha_alta_diagnostico"].max()
    # fecha_inicio, fecha_fin = st.date_input(
    #     "Rango de fechas (diagnóstico)",
    #     [min_fecha, max_fecha]
    # )

with col3:
    tipos = sorted(records["tipo_lesion"].dropna().unique())
    selected_tipo = st.selectbox("Tipo de lesión", ["Todas"] + tipos)

# with col4:
#     gravedades = sorted(records["gravedad"].dropna().unique())
#     selected_gravedad = st.selectbox("Gravedad", ["Todas"] + gravedades)


# === Aplicar filtros dinámicamente ===
filtered = records.copy()

#if jugadora_seleccionada != "Todas":
if jugadora_seleccionada and isinstance(jugadora_seleccionada, dict):
    nombre_completo = (jugadora_seleccionada["nombre"] + " " + jugadora_seleccionada["apellido"]).upper()
    #st.text(f"Mostrando lesiones de: {nombre_completo}")
    filtered = filtered[filtered["id_jugadora"] == jugadora_seleccionada["identificacion"]]

#if selected_tipo != "Todas":
#    filtered = filtered[filtered["tipo_lesion"] == selected_tipo]

# if selected_gravedad != "Todas":
#     filtered = filtered[filtered["gravedad"] == selected_gravedad]

# filtered = filtered[
#     (filtered["fecha_alta_diagnostico"].dt.date >= fecha_inicio)
#     & (filtered["fecha_alta_diagnostico"].dt.date <= fecha_fin)
# ]

# === Mostrar resultado ===
st.markdown(f"**{len(filtered)} lesiones encontradas**")

# Añadir una columna "Acción" con enlaces dinámicos
#filtered["Acción"] = filtered["id_jugadora"].apply(lambda x: f"https://example.com/editar?id={x}")
disabled_cols = [col for col in filtered.columns]

columnas_excluir = [
    "id_jugadora",
    "fecha_hora",
    "posicion",
    "tipo_tratamiento",
    "diagnostico",
    "descripcion",
    "fecha",
    "fecha_dia"
]

# --- eliminar columnas si existen ---
df_filtrado = filtered.drop(columns=[col for col in columnas_excluir if col in filtered.columns])


st.dataframe(df_filtrado)

input_id = st.text_input("Introduce el ID de la lesion:", placeholder="Ejemplo: AJB20251013-4")

# Si se introduce un ID y se presiona Enter
if input_id:
    # Intentamos convertir a número si aplica
    try:
        id_buscar = int(input_id)
    except ValueError:
        id_buscar = input_id  # por si los ID son strings

    # Buscar el registro
    lesion = records.loc[records["id_lesion"] == id_buscar]

    if not lesion.empty:
        zona = lesion.iloc[0]["zona_cuerpo"]
        st.success(f"Zona del Cuerpo: **{zona}**")
    else:
        st.error("No se encontró ninguna jugadora con ese ID.")