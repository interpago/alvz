"""Sistema de tipos para Alvz."""


class Tipo:
    NUMERO = "numero"
    TEXTO = "texto"
    BOOLEANO = "booleano"
    NULO = "nulo"
    LISTA = "lista"
    DICCIONARIO = "diccionario"
    FUNCION = "funcion"
    CUALQUIERA = "cualquiera"

    BUILTIN = {NUMERO, TEXTO, BOOLEANO, NULO, LISTA, DICCIONARIO, FUNCION, CUALQUIERA}

    NOMBRES = {
        NUMERO: "numero",
        TEXTO: "texto",
        BOOLEANO: "booleano",
        NULO: "nulo",
        LISTA: "lista",
        DICCIONARIO: "diccionario",
        FUNCION: "funcion",
        CUALQUIERA: "cualquiera",
    }


def tipo_desde_valor(val):
    if val is None:
        return Tipo.NULO
    if isinstance(val, bool):
        return Tipo.BOOLEANO
    if isinstance(val, (int, float)):
        return Tipo.NUMERO
    if isinstance(val, str):
        return Tipo.TEXTO
    if isinstance(val, list):
        return Tipo.LISTA
    if isinstance(val, dict):
        return Tipo.DICCIONARIO
    if isinstance(val, tuple):
        return Tipo.FUNCION
    return Tipo.CUALQUIERA


def tipo_compatible(a, b):
    """Dos tipos son compatibles si son iguales o uno es CUALQUIERA."""
    if a == Tipo.CUALQUIERA or b == Tipo.CUALQUIERA:
        return True
    if a == b:
        return True
    if a == Tipo.NUMERO and b == Tipo.NUMERO:
        return True
    return False
