from src.db.db_connection import get_connection

def fetch_all(query, params=None):
    """Obtiene múltiples registros."""
    conn = get_connection()
    if not conn:
        return []

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        data = cursor.fetchall()
        return data
    except Exception as e:
        print(f"⚠️ Error en query: {e}")
        return []
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

def execute_query(query, params=None):
    """Ejecuta INSERT, UPDATE o DELETE."""
    conn = get_connection()
    if not conn:
        return False

    try:
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        return True
    except Exception as e:
        print(f"⚠️ Error en query: {e}")
        conn.rollback()
        return False
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
