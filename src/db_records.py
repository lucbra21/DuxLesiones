import pandas as pd
from src.db_connection import get_connection
import streamlit as st
import json
from src.schema import MAP_POSICIONES
from mysql.connector import Error
from src.util import generar_id_lesion, contar_sesiones

import json
import streamlit as st

def save_lesion(data: dict, modo: str = "nuevo") -> bool:
    """
    Inserta o actualiza una lesión en la base de datos 'lesiones'.

    Parámetros:
        data (dict): Diccionario con todos los campos del registro.
        modo (str): 'nuevo' o 'editar'.

    Retorna:
        bool: True si la operación fue exitosa, False si hubo error.
    """

    conn = get_connection()
    if not conn:
        st.error(":material/warning: No se pudo establecer conexión con la base de datos.")
        return False

    try:
        cursor = conn.cursor(dictionary=True)

        # ============================================================
        # 🔹 Validación de columnas según DDL
        # ============================================================
        columnas_validas = {
            "id_lesion", "id_jugadora", "posicion", "fecha_lesion", "lugar_id",
            "segmento_id", "zona_cuerpo_id", "zona_especifica_id", "lateralidad",
            "tipo_lesion_id", "tipo_especifico_id", "es_recidiva", "tipo_recidiva",
            "dias_baja_estimado", "impacto_dias_baja_estimado", "mecanismo_id",
            "tipo_tratamiento", "personal_reporta", "fecha_alta_diagnostico",
            "fecha_alta_medica", "fecha_alta_deportiva", "estado_lesion",
            "diagnostico", "descripcion", "evolucion", "fecha_hora_registro", "usuario"
        }

        # --- Serializar campos JSON ---
        if isinstance(data.get("tipo_tratamiento"), (list, dict)):
            data["tipo_tratamiento"] = json.dumps(data["tipo_tratamiento"], ensure_ascii=False)
        if isinstance(data.get("evolucion"), (list, dict)):
            data["evolucion"] = json.dumps(data["evolucion"], ensure_ascii=False)

        # --- Limpiar campos no válidos ---
        data = {k: v for k, v in data.items() if k in columnas_validas or k == "nombre"}

        # ============================================================
        # 🟢 MODO NUEVO → INSERT
        # ============================================================
        if modo == "nuevo":
            nombre_jugadora = data.get("nombre", "")
            id_last = get_ultima_lesion_id_por_jugadora(data["id_jugadora"])
            id_lesion = generar_id_lesion(nombre_jugadora, data["id_jugadora"], id_last)
            data["id_lesion"] = id_lesion
            data.pop("nombre", None)

            # Validar columnas finales
            data = {k: v for k, v in data.items() if k in columnas_validas}

            query_insert = f"""
            INSERT INTO lesiones ({', '.join(data.keys())})
            VALUES ({', '.join(['%(' + k + ')s' for k in data.keys()])});
            """

            cursor.execute(query_insert, data)
            conn.commit()
            st.success(f":material/done_all: Lesión **{data['id_lesion']}** insertada correctamente.")
            return True

        # ============================================================
        # 🟡 MODO EDITAR → UPDATE (ya viene con evolución completa)
        # ============================================================
        elif modo == "editar":
            id_lesion = data.get("id_lesion")
            if not id_lesion:
                st.error(":material/warning: No se proporcionó el ID de la lesión para actualizar.")
                return False

            params = {
                "evolucion": data.get("evolucion"),
                "fecha_alta_medica": data.get("fecha_alta_medica"),
                "fecha_alta_deportiva": data.get("fecha_alta_deportiva"),
                "estado_lesion": data.get("estado_lesion"),
                "descripcion": data.get("descripcion"),
                "id_lesion": id_lesion
            }

            query_update = """
            UPDATE lesiones
            SET
                evolucion = %(evolucion)s,
                fecha_alta_medica = %(fecha_alta_medica)s,
                fecha_alta_deportiva = %(fecha_alta_deportiva)s,
                estado_lesion = %(estado_lesion)s,
                descripcion = %(descripcion)s,
                updated_at = CURRENT_TIMESTAMP
            WHERE id_lesion = %(id_lesion)s;
            """

            # --- Modo developer: mostrar query y params ---
            if st.session_state.get("auth", {}).get("rol") == "developer":
                st.write("🟡 Query UPDATE ejecutada:")
                st.code(query_update, language="sql")
                st.json(params)

            cursor.execute(query_update, params)
            conn.commit()
            st.success(f":material/done_all: Lesión **{id_lesion}** actualizada correctamente.")
            return True

        else:
            st.warning(":material/warning: Modo no reconocido. Use 'nuevo' o 'editar'.")
            return False

    except Exception as e:
        conn.rollback()
        st.error(f":material/warning: Error al guardar la lesión: {e}")

        if st.session_state.get("auth", {}).get("rol") == "developer":
            st.json(data)

        return False

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def load_lesiones_db(as_df=True):
    """
    Carga todos los registros de la tabla 'lesiones' sin cache persistente.
    Incluye joins con catálogos relacionados.
    """
    conn = get_connection()
    if not conn:
        st.error(":material/warning: No se pudo conectar a la base de datos.")
        return pd.DataFrame() if as_df else []

    try:
        query = """
        SELECT 
            l.id,
            l.id_lesion,
            l.id_jugadora,
            l.posicion,
            l.fecha_lesion,
            lu.nombre AS lugar,
            s.nombre AS segmento,
            z.nombre AS zona_cuerpo,
            za.nombre AS zona_especifica,
            l.lateralidad,
            t.nombre AS tipo_lesion,
            te.nombre AS tipo_especifico,
            l.es_recidiva,
            l.tipo_recidiva,
            l.dias_baja_estimado,
            l.impacto_dias_baja_estimado,
            m.nombre AS mecanismo,
            l.tipo_tratamiento,
            l.personal_reporta,
            l.fecha_alta_diagnostico,
            l.fecha_alta_deportiva,
            l.fecha_alta_medica,
            l.estado_lesion,
            l.diagnostico,
            l.descripcion,
            l.evolucion,
            l.fecha_hora_registro,
            l.usuario
        FROM lesiones l
        LEFT JOIN lugares lu ON l.lugar_id = lu.id
        LEFT JOIN segmentos_corporales s ON l.segmento_id = s.id
        LEFT JOIN zonas_segmento z ON l.zona_cuerpo_id = z.id
        LEFT JOIN zonas_anatomicas za ON l.zona_especifica_id = za.id
        LEFT JOIN tipo_lesion t ON l.tipo_lesion_id = t.id
        LEFT JOIN tipo_especifico_lesion te ON l.tipo_especifico_id = te.id
        LEFT JOIN mecanismos m ON l.mecanismo_id = m.id
        ORDER BY l.fecha_hora_registro DESC;
        """

        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        rows = cursor.fetchall()
        df = pd.DataFrame(rows)
        cursor.close()

        if not rows:
            st.info(":material/info: No existen registros de lesiones en la base de datos.")
            st.stop()
        
        df["sesiones"] = df["evolucion"].apply(contar_sesiones)
        df["posicion"] = df["posicion"].map(MAP_POSICIONES).fillna(df["posicion"])

        if st.session_state["auth"]["rol"].lower() == "developer":
            df = df[df["usuario"]=="developer"]
        else:
            df = df[df["usuario"]!="developer"]

        return df if as_df else df.to_dict(orient="records")
    except Exception as e:
        st.error(f":material/warning: Error al cargar lesiones: {e}")
        return pd.DataFrame() if as_df else []
    finally:
        conn.close()

def get_ultima_lesion_id_por_jugadora(id_jugadora: str) -> str | None:
    """
    Devuelve el ID de la última lesión registrada de una jugadora.
    Si no tiene lesiones, retorna None.
    """

    conn = get_connection()
    if not conn:
        st.error(":material/warning: No se pudo conectar a la base de datos.")
        return None

    try:
        query = """
        SELECT id_lesion
        FROM lesiones
        WHERE id_jugadora = %s
        ORDER BY COALESCE(fecha_hora_registro, fecha_lesion) DESC
        LIMIT 1;
        """

        cursor = conn.cursor()
        cursor.execute(query, (id_jugadora,))
        result = cursor.fetchone()

        return result[0] if result else None

    except Exception as e:
        st.error(f":material/warning: Error al obtener el ID de la última lesión: {e}")
        return None

    finally:
        if conn:
            conn.close()

def get_records_plus_players_db(plantel: str = None) -> pd.DataFrame:
    """
    Devuelve todas las lesiones junto con los datos de las jugadoras.
    Si no hay registros, devuelve un DataFrame vacío.

    Combina:
    - lesiones
    - futbolistas (nombre, apellido, competicion)
    - informacion_futbolistas (posicion, altura, peso)
    """

    conn = get_connection()
    if not conn:
        st.error(":material/warning: No se pudo conectar a la base de datos.")
        return pd.DataFrame()

    try:
        query = """
        SELECT 
            l.id AS id_registro,
            l.id_lesion,
            l.id_jugadora,
            f.nombre,
            f.apellido,
            f.competicion AS plantel,
            i.posicion,
            l.fecha_lesion,
            l.estado_lesion,
            l.diagnostico,
            l.dias_baja_estimado,
            l.impacto_dias_baja_estimado,
            l.mecanismo_id,
            m.nombre AS mecanismo,
            t.nombre AS tipo_lesion,
            te.nombre AS tipo_especifico,
            l.lugar_id,
            lu.nombre AS lugar,
            l.segmento_id,
            s.nombre AS segmento,
            l.zona_cuerpo_id,
            z.nombre AS zona_cuerpo,
            l.zona_especifica_id,
            za.nombre AS zona_especifica,
            l.lateralidad,
            l.es_recidiva,
            l.tipo_recidiva,
            l.tipo_tratamiento,
            l.personal_reporta,
            l.fecha_alta_diagnostico,
            l.fecha_alta_medica,
            l.fecha_alta_deportiva,
            l.descripcion,
            l.evolucion,
            l.fecha_hora_registro,
            l.usuario
        FROM lesiones l
        LEFT JOIN futbolistas f ON l.id_jugadora = f.id
        LEFT JOIN informacion_futbolistas i ON l.id_jugadora = i.id_futbolista
        LEFT JOIN lugares lu ON l.lugar_id = lu.id
        LEFT JOIN mecanismos m ON l.mecanismo_id = m.id
        LEFT JOIN tipo_lesion t ON l.tipo_lesion_id = t.id
        LEFT JOIN tipo_especifico_lesion te ON l.tipo_especifico_id = te.id
        LEFT JOIN segmentos_corporales s ON l.segmento_id = s.id
        LEFT JOIN zonas_segmento z ON l.zona_cuerpo_id = z.id
        LEFT JOIN zonas_anatomicas za ON l.zona_especifica_id = za.id
        ORDER BY l.fecha_hora_registro DESC;
        """

        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        rows = cursor.fetchall()
        df = pd.DataFrame(rows)
        cursor.close()

        if not rows:
            st.info(":material/info: No existen registros de lesiones en la base de datos.")
            st.stop()

        # Crear columna nombre_jugadora
        df["nombre_jugadora"] = (
            df["nombre"].fillna("") + " " + df["apellido"].fillna("")
        ).str.strip()

        # Reordenar columnas
        columnas = df.columns.tolist()
        if "id_jugadora" in columnas and "nombre_jugadora" in columnas:
            idx = columnas.index("id_jugadora") + 1
            columnas.insert(idx, columnas.pop(columnas.index("nombre_jugadora")))
        if "posicion" in columnas and "plantel" in columnas:
            idx = columnas.index("posicion") + 1
            columnas.insert(idx, columnas.pop(columnas.index("plantel")))

        df = df[columnas]
        df["posicion"] = df["posicion"].map(MAP_POSICIONES).fillna(df["posicion"])
        df["sesiones"] = df["evolucion"].apply(contar_sesiones)
        
        # Filtrar por plantel si se indica
        if plantel:
            df = df[df["plantel"] == plantel]

        if st.session_state["auth"]["rol"].lower() == "developer":
            df = df[df["usuario"]=="developer"]
        else:
            df = df[df["usuario"]!="developer"]
        
        return df

    except Exception as e:
        st.error(f":material/warning: Error al cargar registros y jugadoras: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

@st.cache_data(ttl=3600)  # cachea por 1 hora (ajústalo según tu frecuencia de actualización)
def load_jugadoras_db() -> tuple[pd.DataFrame | None, str | None]:
    """
    Carga jugadoras desde la base de datos (futbolistas + informacion_futbolistas).
    
    Devuelve:
        tuple: (DataFrame o None, mensaje de error o None)
    """
    conn = get_connection()
    if not conn:
        return None, ":material/warning: No se pudo conectar a la base de datos."

    try:
        query = """
        SELECT 
            f.id AS identificacion,
            f.nombre,
            f.apellido,
            f.competicion AS plantel,
            f.fecha_nacimiento,
            f.sexo,
            i.posicion,
            i.dorsal,
            i.nacionalidad,
            i.altura,
            i.peso,
            i.foto_url
        FROM futbolistas f
        LEFT JOIN informacion_futbolistas i 
            ON f.id = i.id_futbolista
        ORDER BY f.nombre ASC;
        """

        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        rows = cursor.fetchall()
        df = pd.DataFrame(rows)
        cursor.close()

        # Limpiar y preparar los datos
        df["nombre"] = df["nombre"].astype(str).str.strip().str.title()
        df["apellido"] = df["apellido"].astype(str).str.strip().str.title()

        # Crear columna nombre completo
        df["nombre_jugadora"] = (df["nombre"] + " " + df["apellido"]).str.strip()

        # Reordenar columnas
        orden = [
            "identificacion", "nombre_jugadora", "nombre", "apellido", "posicion", "plantel",
            "dorsal", "nacionalidad", "altura", "peso", "fecha_nacimiento",
            "sexo", "foto_url"
        ]
        df = df[[col for col in orden if col in df.columns]]
        df["posicion"] = df["posicion"].map(MAP_POSICIONES).fillna(df["posicion"])

        #st.dataframe(df)

        return df, None

    except Exception as e:
        return None, f":material/warning: Error al cargar jugadoras: {e}"

    finally:
        conn.close()

@st.cache_data(ttl=3600)  # cachea por 1 hora
def load_competiciones_db() -> tuple[pd.DataFrame | None, str | None]:
    """
    Carga competiciones desde la base de datos (tabla 'plantel').

    Devuelve:
        tuple: (DataFrame o None, mensaje de error o None)
    """
    conn = get_connection()
    if not conn:
        return None, ":material/warning: No se pudo conectar a la base de datos."

    try:
        query = """
        SELECT 
            id,
            nombre,
            codigo
        FROM plantel
        ORDER BY nombre ASC;
        """

        cursor = conn.cursor(dictionary=True)
        cursor.execute(query)
        rows = cursor.fetchall()
        df = pd.DataFrame(rows)
        cursor.close()

        if df.empty:
            return None, ":material/warning: No se encontraron registros en la tabla 'plantel'."

        # Limpieza básica
        df["nombre"] = df["nombre"].astype(str).str.strip().str.title()
        df["codigo"] = df["codigo"].astype(str).str.strip().str.upper()

        # Reordenar columnas (por consistencia)
        orden = ["id", "nombre", "codigo"]
        df = df[[col for col in orden if col in df.columns]]

        return df, None

    except Exception as e:
        return None, f":material/warning: Error al cargar competiciones: {e}"

    finally:
        conn.close()