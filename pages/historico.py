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
    jugadoras = sorted(records["nombre_jugadora"].dropna().unique())
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

# if jugadora_seleccionada != "Todas":
#     filtered = filtered[filtered["nombre_jugadora"] == jugadora_seleccionada]

if selected_tipo != "Todas":
    filtered = filtered[filtered["tipo_lesion"] == selected_tipo]

# if selected_gravedad != "Todas":
#     filtered = filtered[filtered["gravedad"] == selected_gravedad]

# filtered = filtered[
#     (filtered["fecha_alta_diagnostico"].dt.date >= fecha_inicio)
#     & (filtered["fecha_alta_diagnostico"].dt.date <= fecha_fin)
# ]

# === Mostrar resultado ===
st.markdown(f"**{len(filtered)} lesiones encontradas**")
st.dataframe(filtered, width='stretch')

