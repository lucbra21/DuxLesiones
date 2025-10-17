import datetime
import os
import json
import pandas as pd

from pathlib import Path
from io import BytesIO
from typing import Optional
import streamlit as st

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
DATA_DIR = os.path.join(BASE_DIR, "data")
JUGADORAS_JSON = os.path.join(DATA_DIR, "jugadoras.jsonl")
PARTES_CUERPO_JSON = os.path.join(DATA_DIR, "partes_cuerpo.jsonl")
REGISTROS_JSONL = os.path.join(DATA_DIR, "registros.jsonl")
COMPETICIONES_JSONL = os.path.join(DATA_DIR, "competiciones.jsonl")

#st.text(f"BASE_DIR: {DATA_DIR}")

def _ensure_data_dir():
    """
    Creates the 'data' directory if it doesn't exist.

    This function ensures that the main data directory exists,
    which is used to store input/output files such as 
    'jugadoras.jsonl', 'registros.jsonl', 'partes_cuerpo.json', etc.

    It does not raise an error if the directory already exists.
    """
    os.makedirs("data", exist_ok=True)

def load_competiciones() -> tuple[pd.DataFrame | None, str | None]:
    """
    Carga jugadoras desde archivo JSON. Se esperan las claves: id_jugadora, nombre_jugadora

    Returns:
        tuple: (DataFrame o None, mensaje de error o None)
    """
    _ensure_data_dir()
    if not os.path.exists(COMPETICIONES_JSONL):
        return None, f"No se encontró {COMPETICIONES_JSONL}. Descarga y coloca el archivo."

    try:
        with open(COMPETICIONES_JSONL, "r", encoding="utf-8") as f:
            data = json.load(f)

        df = pd.DataFrame(data)
        #df = df[df["activo"] == 1]
        df = df.sort_values("nombre")

        return df, None

    except Exception as e:
        return None, f"Error leyendo jugadoras.json: {e}"

def load_jugadoras() -> tuple[pd.DataFrame | None, str | None]:
    """
    Carga jugadoras desde archivo JSON. Se esperan las claves: id_jugadora, nombre_jugadora

    Returns:
        tuple: (DataFrame o None, mensaje de error o None)
    """
    _ensure_data_dir()
    if not os.path.exists(JUGADORAS_JSON):
        return None, f"No se encontró {JUGADORAS_JSON}. Descarga y coloca el archivo."

    try:
        with open(JUGADORAS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)

        df = pd.DataFrame(data)
        df = df[df["activo"] == 1]
        df = df.sort_values("nombre")

        return df, None

    except Exception as e:
        return None, f"Error leyendo jugadoras.json: {e}"

def load_partes_json(path: str | Path) -> tuple[pd.DataFrame | None, str | None]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Verifica que el formato sea tipo: {"parte": [ ... ]}
        if not isinstance(data, dict) or "parte" not in data:
            return None, "Formato inválido: se esperaba una clave 'parte' con lista de valores."

        partes = data["parte"]
        if not isinstance(partes, list) or not all(isinstance(p, str) for p in partes):
            return None, "Los valores bajo 'parte' deben ser una lista de strings."

        # Convertimos a DataFrame como espera la app
        df = pd.DataFrame({"parte": partes})
        return df, None

    except Exception as e:
        return None, f"Error al cargar el archivo: {e}"

def _read_all_records() -> list[dict]:
    """Read all JSONL records as a list of dicts. Missing file -> empty list."""
    _ensure_data_dir()
    records: list[dict] = []
    if not os.path.exists(REGISTROS_JSONL):
        return records
    with open(REGISTROS_JSONL, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except Exception:
                # Skip malformed lines
                continue
    return records

def _write_all_records(records: list[dict]) -> None:
    """Overwrite the JSONL file with the provided records list."""
    try:
        _ensure_data_dir()
        with open(REGISTROS_JSONL, "w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception as e:
        st.error(f"Error al guardar los datos: {e}")

def _date_only(ts: str) -> str:
    """Extract YYYY-MM-DD from timestamp string like YYYY-MM-DDTHH:MM:SS."""
    return (ts or "").split("T")[0]

def upsert_jsonl(record: dict) -> None:
    """Upsert de registro de lesión:
    - Si existe un registro con los mismos datos (excepto personal_reporta y descripcion), se actualiza.
    - Si no existe, se agrega como nuevo.
    """
    records = _read_all_records()

    def same_lesion(a: dict, b: dict) -> bool:
        """Compara todos los campos excepto personal_reporta y descripcion"""
        keys_to_compare = [
            "id_lesion", "id_jugadora", "fecha_lesion", "posicion", "zona_cuerpo", "lateralidad", "tipo_lesion", "gravedad"
        ]
        return all(a.get(k) == b.get(k) for k in keys_to_compare)

    # Buscar si ya existe un registro idéntico
    idx_to_update = None
    for idx, rec in enumerate(records):
        if same_lesion(rec, record):
            idx_to_update = idx
            break

    if idx_to_update is not None:
        # Si existe, actualizamos solo los campos informativos
        records[idx_to_update]["evolucion"] = record.get("evolucion", "")
        records[idx_to_update]["fecha_alta_medica"] = record.get("fecha_alta_medica", "")
        records[idx_to_update]["fecha_alta_deportiva"] = record.get("fecha_alta_deportiva", "")
        records[idx_to_update]["estado_lesion"] = record.get("estado_lesion", "")
        #records[idx_to_update]["fecha_hora"] = datetime.datetime.now().isoformat()
    else:
        # Si no existe, lo añadimos
        records.append(record)

    _write_all_records(records)

def get_records_df() -> pd.DataFrame:
    """Return all registros as a pandas DataFrame. If none, returns empty DF.

    Adds helper columns:
    - fecha (datetime)
    - fecha_dia (date)
    """

    recs = _read_all_records()
    jug_df, jug_error = load_jugadoras()

    if not recs:
        return pd.DataFrame()
    df = pd.DataFrame(recs)
   
    return df

def get_records_plus_players_df() -> pd.DataFrame:
    """Return all registros as a pandas DataFrame. If none, returns empty DF.

    Adds helper columns:
    - fecha (datetime)
    - fecha_dia (date)
    - nombre_completo (joined from jugadoras)
    """

    # --- Leer registros y jugadoras ---
    recs = _read_all_records()
    jug_df, jug_error = load_jugadoras()

    # --- Validar registros ---
    if not recs:
        return pd.DataFrame()

    df = pd.DataFrame(recs)

    # --- Añadir columna nombre_completo ---
    if (
        jug_df is not None
        and not jug_df.empty
        and "identificacion" in jug_df.columns
        and "nombre" in jug_df.columns
        and "apellido" in jug_df.columns
        and "id_jugadora" in df.columns
    ):
        # Normalizar formatos
        jug_df["identificacion"] = jug_df["identificacion"].astype(str).str.strip().str.upper()
        df["id_jugadora"] = df["id_jugadora"].astype(str).str.strip().str.upper()

        # Crear mapa {identificacion: nombre completo}
        map_nombres = dict(
            zip(
                jug_df["identificacion"],
                jug_df["nombre"].fillna("") + " " + jug_df["apellido"].fillna(""),
            )
        )

        # Mapear nombres al df de registros
        df["nombre_jugadora"] = df["id_jugadora"].map(map_nombres).fillna("")

        # Reordenar columnas: nombre_completo justo después de id_jugadora
        cols = df.columns.tolist()
        if "id_jugadora" in cols and "nombre_jugadora" in cols:
            idx = cols.index("id_jugadora") + 1
            cols.insert(idx, cols.pop(cols.index("nombre_jugadora")))
            df = df[cols]
    else:
        df["nombre_jugadora"] = ""

    return df


def append_jsonl(record: dict) -> None:
    """Append a dict as one line of JSON to the registros.jsonl file."""
    _ensure_data_dir()
    # Ensure file exists
    if not os.path.exists(REGISTROS_JSONL):
        with open(REGISTROS_JSONL, "w", encoding="utf-8") as f:
            pass
    with open(REGISTROS_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def registrar_lesion(data):
    try:
        
        st.success("¡Lesión registrada con éxito! Los datos han sido guardados.")
        st.balloons() 
        # Limpiar el caché de datos para que el dashboard se actualice
        st.cache_data.clear()
        st.rerun() # Volver a ejecutar para mostrar el dashboard actualizado
        
    except Exception as e:
        st.error(f"Error al guardar los datos: {e}")

