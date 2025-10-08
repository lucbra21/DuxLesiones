import streamlit as st
import json
import random
import datetime
from pathlib import Path
import pandas as pd

import src.config as config
config.init_config()

from src.auth import init_app_state, login_view, menu, validate_login
from src.io_files import get_records_df
init_app_state()

validate_login()

# Authentication gate
if not st.session_state["auth"]["is_logged_in"]:
    login_view()
    st.stop()

st.header("Simulador de :red[Lesiones]", divider=True)

menu()

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
    estados = ["Activo", "Inactivo"]
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

#output_lesiones="data/lesiones.jsonl"
jugadoras_path="data/jugadoras.jsonl"

if st.button("Generar lesiones aleatorias"):
    try:
        output_lesiones = generar_lesiones_aleatorias(
            jugadoras_path="data/jugadoras.jsonl",
            output_dir="data",
            lesiones_por_jugadora=10
        )
        st.success(f"✅ Lesiones generadas correctamente en: {output_lesiones.name}")

        df, error = load_lesiones_jsonl(output_lesiones)

        if error:
            st.error(error)
        else:
            st.success(f"Se cargaron {len(df)} lesiones correctamente.")
            st.dataframe(df)
    except Exception as e:
            st.error(f"❌ Error al generar lesiones: {e}")



