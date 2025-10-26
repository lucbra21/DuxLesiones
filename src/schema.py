
# Diccionario principal → subcategorías

# --- Reglas clínicas para desactivar el selector de subtipo ---
reglas_desactivar_subtipo = [
    {"mecanismo": "SOBRECARGA", "tipo": "MUSCULAR"},
    {"mecanismo": "SOBRECARGA", "tipo": "TENDINOSA"},
    {"mecanismo": "MICROTRAUMA REPETITIVO", "tipo": "TENDINOSA"},
    {"mecanismo": "MICROTRAUMA REPETITIVO", "tipo": "ÓSEA"},
    {"mecanismo": "OTRO", "tipo": "OTRAS"},
    {"mecanismo": "DESCONOCIDO", "tipo": "OTRAS"}
]

# Diccionario de equivalencias
MAP_POSICIONES = {
    "POR": "Portera",
    "DEF": "Defensa",
    "MC": "Centro",
    "DEL": "Delantera"
}

#segmentos_corporales = ["TREN SUPERIOR", "TRONCO / MEDIO", "TREN INFERIOR"]

# zonas_por_segmento = {
#     "TREN SUPERIOR": ["HOMBRO", "BRAZO", "CODO", "ANTEBRAZO", "MUÑECA", "MANO", "CABEZA", "CUELLO"],
#     "TRONCO / MEDIO": ["CADERA", "PELVIS", "COLUMNA LUMBAR"],
#     "TREN INFERIOR": ["MUSLO", "PIERNA", "RODILLA", "TOBILLO", "PIE"]
# }

# zonas_anatomicas = {
#     "MUSLO": ["ISQUIOTIBIALES", "CUÁDRICEPS", "ADUCTORES"],
#     "PIERNA": ["GEMELOS", "SÓLEO", "TIBIAL ANTERIOR"],
#     "RODILLA": ["LCA", "LCP", "MENISCO INTERNO", "MENISCO EXTERNO", "RÓTULA"],
#     "TOBILLO": ["LIGAMENTOS LATERALES", "PERONEOS", "TIBIAL POSTERIOR", "ASTRÁGALO"],
#     "PIE": ["FASCIA PLANTAR", "METATARSIANOS", "FALANGES"],
#     "CADERA": ["PSOAS", "GLÚTEO MEDIO", "ROTADORES INTERNOS"],
#     "PELVIS": ["PUBIS", "SINFISIS PÚBICA", "ISQUIOS PROXIMALES"],
#     "COLUMNA LUMBAR": ["PARAVERTEBRALES", "DISCOS INTERVERTEBRALES", "L5-S1"],
#     "HOMBRO": ["DELTOIDES", "MANGUITO ROTADOR", "CLAVÍCULA", "ACROMIOCLAVICULAR"],
#     "BRAZO": ["BÍCEPS", "TRÍCEPS"],
#     "CODO": ["EPICÓNDILO", "EPITRÓCLEA", "OLECRANON"],
#     "ANTEBRAZO": ["FLEXORES", "EXTENSORES", "PRONADORES"],
#     "MUÑECA": ["ESCAFOIDES", "RADIO DISTAL", "LIGAMENTOS CARPIANOS"],
#     "MANO": ["METACARPIANOS", "FALANGES", "PULGAR"],
#     "CABEZA": ["CRÁNEO", "CARA", "MANDÍBULA"],
#     "CUELLO": ["CERVICALES", "TRAPECIO SUPERIOR"],
#     "OTRO": ["ZONA NO ESPECIFICADA"]
# }

# tratamientos = [
#     "CRIOTERAPIA",
#     "TERMOTERAPIA",
#     "ELECTROTERAPIA",
#     "MASOTERAPIA / DRENAJE",
#     "PUNCIÓN SECA",
#     "EJERCICIOS DE MOVILIDAD",
#     "EJERCICIOS DE FUERZA",
#     "TRABAJO PROPIOCEPTIVO",
#     "TRABAJO DE CAMPO",
#     "REEDUCACIÓN TÉCNICA / RETORNO PROGRESIVO"
# ]

#lugares = ["ENTRENAMIENTO", "PARTIDO", "GIMNASIO", "OTRO"]
#mecanismos = ["SIN CONTACTO", "CON CONTACTO", "SOBRECARGA O MICROTRAUMA REPETITIVO", "TORSIÓN O DESEQUILIBRIO", "GOLPE DIRECTO"]
#lateralidades = ["DERECHA", "IZQUIERDA", "BILATERAL"]
#tipos_lesion = ["CONTUSIÓN", "DISTENSIÓN MUSCULAR", "ESGUINCE", "FRACTURA", "LACERACIÓN", "LESIÓN ARTICULAR", "LESIÓN LIGAMENTARIA", "LUXACIÓN / SUBLUXACIÓN", "ROTURA FIBRILAR", "TENDINOPATÍA", "OTRA"]

# tipos_lesion = {
#     "MUSCULAR": ["CONTUSIÓN MUSCULAR", "DISTENSIÓN", "ROTURA FIBRILAR"],
#     "TENDINOSA": ["TENDINOPATÍA", "ROTURA TENDINOSA"],
#     "LIGAMENTARIA / ARTICULAR": ["ESGUINCE", "LESIÓN LIGAMENTARIA", "LUXACIÓN / SUBLUXACIÓN", "LESIÓN ARTICULAR"],
#     "ÓSEA": ["FRACTURA"],
#     "TRAUMÁTICA / SUPERFICIAL": ["LACERACIÓN", "CONTUSIÓN SUPERFICIAL"],
#     "OTRAS": ["OTRA"]
# }

# gravedad_dias = {
#     "LEVE": (1, 3),
#     "MODERADA": (4, 7),
#     "GRAVE": (8, 28),
#     "MUY GRAVE": (29, None)
# }

#gravedad_clinica = ["LEVE", "MODERADA", "GRAVE", "MUY GRAVE", "RECIDIVA"]

# tipos_recidiva = [
#     "TEMPRANA (≤ 2 MESES)",
#     "TARDÍA (2-12 MESES)"
# ]

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

