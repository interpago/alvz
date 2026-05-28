"""
Utilidades de errores y sugerencias para Alvz Language.
"""

import difflib

KEYWORDS_ALVZ = [
    "variable", "imprimir", "leer", "leer_numero", "azar", "limpiar",
    "longitud", "agregar", "esperar", "enviar_web", "escribir_archivo",
    "minusculas", "mayusculas", "obtener_salida", "supabase_insertar",
    "leer_archivo", "supabase_consultar", "json_decodificar", "importar",
    "tiempo", "json_codificar", "reemplazar", "absoluto", "redondear",
    "potencia", "raiz", "intentar", "capturar", "lanzar", "clase", "nuevo",
    "error_msj", "funcion", "retornar", "si", "sino", "mientras", "para",
    "cada", "en", "de", "a", "verdadero", "falso", "y", "o",
    "iniciar_servidor",
    "romper", "continuar",
    "solicitud_http", "sqlite_abrir", "sqlite_ejecutar", "sqlite_consultar",
    "fecha_actual", "dividir", "unir", "a_numero", "regex_buscar",
    "nulo", "async", "aguardar", "estatico", "propiedad", "obtener",
    "establecer", "super", "instancia"
]


def obtener_sugerencia(palabra_erronea, opciones=KEYWORDS_ALVZ):
    """Encuentra la palabra mas cercana a la erronea."""
    coincidencias = difflib.get_close_matches(
        palabra_erronea, opciones, n=1, cutoff=0.6
    )
    return coincidencias[0] if coincidencias else None
