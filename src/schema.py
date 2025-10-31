
# Diccionario de equivalencias
MAP_POSICIONES = {
    "POR": "Portera",
    "DEF": "Defensa",
    "MC": "Centro",
    "DEL": "Delantera"
}

def validate_checkin(record: dict) -> tuple[bool, str]:
    # Required 1..5
    for field in ["recuperacion", "fatiga", "sueno", "stress", "dolor"]:
        value = record.get(field)
        if value is None:
            return False, f"Completa el campo '{field}'."
        if not (1 <= int(value) <= 5):
            return False, f"El campo '{field}' debe estar entre 1 y 5."
    # Dolor parts if dolor > 1
    if int(record.get("dolor", 0)) > 1:
        if not record.get("partes_cuerpo_dolor"):
            return False, "Selecciona al menos una parte del cuerpo con dolor."
    return True, ""

essential_checkout_fields = ("minutos_sesion", "rpe")

