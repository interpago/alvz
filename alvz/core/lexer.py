"""
Lexer para Alvz Language.

Convierte el texto fuente en una secuencia de tokens que seran
consumidos por el parser.
"""

import re
import enum
from .errors import obtener_sugerencia


class Token(enum.Enum):
    ASYNC = "ASYNC"
    AGUARDAR = "AGUARDAR"
    NULO = "NULO"
    VARIABLE = "VARIABLE"
    IDENTIFICADOR = "IDENTIFICADOR"
    ASIGNACION = "ASIGNACION"
    STRING = "STRING"
    NUMERO = "NUMERO"
    IMPRIMIR = "IMPRIMIR"
    LEER = "LEER"
    LEER_NUMERO = "LEER_NUMERO"
    AZAR = "AZAR"
    LIMPIAR = "LIMPIAR"
    FUNCION = "FUNCION"
    RETORNAR = "RETORNAR"
    SI = "SI"
    SINO = "SINO"
    MIENTRAS = "MIENTRAS"
    PARA = "PARA"
    CADA = "CADA"
    EN = "EN"
    DE = "DE"
    A = "A"
    VERDADERO = "VERDADERO"
    FALSO = "FALSO"
    Y = "Y"
    O = "O"  # noqa: E741
    PAREN_IZQ = "PAREN_IZQ"
    PAREN_DER = "PAREN_DER"
    LLAVE_IZQ = "LLAVE_IZQ"
    LLAVE_DER = "LLAVE_DER"
    MAS = "MAS"
    MENOS = "MENOS"
    POR = "POR"
    ENTRE = "ENTRE"
    MAS_IGUAL = "MAS_IGUAL"
    MENOS_IGUAL = "MENOS_IGUAL"
    POR_IGUAL = "POR_IGUAL"
    ENTRE_IGUAL = "ENTRE_IGUAL"
    MOD_IGUAL = "MOD_IGUAL"
    IGUAL_IGUAL = "IGUAL_IGUAL"
    DIFERENTE = "DIFERENTE"
    MAYOR = "MAYOR"
    MENOR = "MENOR"
    MAYOR_IGUAL = "MAYOR_IGUAL"
    MENOR_IGUAL = "MENOR_IGUAL"
    COMA = "COMA"
    CORCHETE_IZQ = "CORCHETE_IZQ"
    CORCHETE_DER = "CORCHETE_DER"
    COMENTARIO = "COMENTARIO"
    LONGITUD = "LONGITUD"
    AGREGAR = "AGREGAR"
    ESPERAR = "ESPERAR"
    ENVIAR_WEB = "ENVIAR_WEB"
    ESCRIBIR_ARCHIVO = "ESCRIBIR_ARCHIVO"
    MINUSCULAS = "MINUSCULAS"
    MAYUSCULAS = "MAYUSCULAS"
    OBTENER_SALIDA = "OBTENER_SALIDA"
    SUPABASE_INSERTAR = "SUPABASE_INSERTAR"
    REDONDEAR = "REDONDEAR"
    POTENCIA = "POTENCIA"
    RAIZ = "RAIZ"
    INTENTAR = "INTENTAR"
    CAPTURAR = "CAPTURAR"
    LANZAR = "LANZAR"
    CLASE = "CLASE"
    NUEVO = "NUEVO"
    SUPER = "SUPER"
    INSTANCIA = "INSTANCIA"
    ESTATICO = "ESTATICO"
    PROPIEDAD = "PROPIEDAD"
    OBTENER = "OBTENER"
    ESTABLECER = "ESTABLECER"
    PUNTO = "PUNTO"
    MODULO = "MODULO"
    ERROR_MSJ = "ERROR_MSJ"
    LEER_ARCHIVO = "LEER_ARCHIVO"
    SUPABASE_CONSULTAR = "SUPABASE_CONSULTAR"
    JSON_DECODIFICAR = "JSON_DECODIFICAR"
    IMPORTAR = "IMPORTAR"
    TIEMPO = "TIEMPO"
    JSON_CODIFICAR = "JSON_CODIFICAR"
    TIPO_KW = "TIPO_KW"
    REEMPLAZAR = "REEMPLAZAR"
    ABSOLUTO = "ABSOLUTO"
    INICIAR_SERVIDOR = "INICIAR_SERVIDOR"
    ROMPER = "ROMPER"
    CONTINUAR = "CONTINUAR"
    FECHA_ACTUAL = "FECHA_ACTUAL"
    DIVIDIR = "DIVIDIR"
    UNIR = "UNIR"
    A_NUMERO = "A_NUMERO"
    REGEX_BUSCAR = "REGEX_BUSCAR"
    STRING_TRIPLE = "STRING_TRIPLE"
    DOS_PUNTOS = "DOS_PUNTOS"
    SQLITE_ABRIR = "SQLITE_ABRIR"
    SQLITE_EJECUTAR = "SQLITE_EJECUTAR"
    SQLITE_CONSULTAR = "SQLITE_CONSULTAR"
    SOLICITUD_HTTP = "SOLICITUD_HTTP"
    GLOBAL = "GLOBAL"
    EOF = "EOF"


class Lexer:
    """Convierte el texto fuente en una secuencia de tokens."""

    def __init__(self, code):
        self.code = code
        self.tokens = []
        self.pos = 0
        self.line = 1

    def tokenize(self):
        token_specification = [
            ('VARIABLE',    r'variable\b'),
            ('IMPRIMIR',    r'imprimir\b'),
            ('LEER_NUMERO', r'leer_numero\b'),
            ('LEER',        r'leer\b'),
            ('AZAR',        r'azar\b'),
            ('LIMPIAR',     r'limpiar\b'),
            ('LONGITUD',    r'longitud\b'),
            ('AGREGAR',     r'agregar\b'),
            ('ESPERAR',     r'esperar\b'),
            ('ENVIAR_WEB',  r'enviar_web\b'),
            ('ESCRIBIR_ARCHIVO', r'escribir_archivo\b'),
            ('MINUSCULAS',  r'minusculas\b'),
            ('MAYUSCULAS',  r'mayusculas\b'),
            ('PROPIEDAD',    r'propiedad\b'),
            ('OBTENER_SALIDA', r'obtener_salida\b'),
            ('OBTENER',      r'obtener\b'),
            ('ESTABLECER',   r'establecer\b'),
            ('SUPABASE_INSERTAR', r'supabase_insertar\b'),
            ('LEER_ARCHIVO', r'leer_archivo\b'),
            ('SUPABASE_CONSULTAR', r'supabase_consultar\b'),
            ('JSON_DECODIFICAR', r'json_decodificar\b'),
            ('IMPORTAR',    r'importar\b'),
            ('TIEMPO',      r'tiempo\b'),
            ('JSON_CODIFICAR', r'json_codificar\b'),
            ('CLASE',       r'clase\b'),
            ('NUEVO',       r'nuevo\b'),
            ('FUNCION',     r'funcion\b'),
            ('RETORNAR',    r'retornar\b'),
            ('SI',          r'si\b'),
            ('SINO',        r'sino\b'),
            ('MIENTRAS',    r'mientras\b'),
            ('PARA',        r'para\b'),
            ('CADA',        r'cada\b'),
            ('EN',          r'en\b'),
            ('DE',          r'de\b'),
            ('A',           r'a\b'),
            ('VERDADERO',   r'verdadero\b'),
            ('FALSO',       r'falso\b'),
            ('Y',           r'y\b'),
            ('O',           r'o\b'),
            ('TIPO_KW',     r'tipo\b'),
            ('REEMPLAZAR',  r'reemplazar\b'),
            ('ABSOLUTO',    r'absoluto\b'),
            ('SQLITE_ABRIR', r'sqlite_abrir\b'),
            ('SQLITE_EJECUTAR', r'sqlite_ejecutar\b'),
            ('SQLITE_CONSULTAR', r'sqlite_consultar\b'),
            ('SOLICITUD_HTTP', r'solicitud_http\b'),
            ('AGUARDAR',    r'aguardar\b'),
            ('ASYNC',       r'async\b'),
            ('INICIAR_SERVIDOR', r'iniciar_servidor\b'),
            ('REDONDEAR',   r'redondear\b'),
            ('POTENCIA',    r'potencia\b'),
            ('RAIZ',        r'raiz\b'),
            ('INTENTAR',    r'intentar\b'),
            ('CAPTURAR',    r'capturar\b'),
            ('LANZAR',      r'lanzar\b'),
            ('ERROR_MSJ',   r'error_msj\b'),
            ('ROMPER',      r'romper\b'),
            ('CONTINUAR',   r'continuar\b'),
            ('FECHA_ACTUAL', r'fecha_actual\b'),
            ('DIVIDIR',     r'dividir\b'),
            ('UNIR',        r'unir\b'),
            ('A_NUMERO',    r'a_numero\b'),
            ('REGEX_BUSCAR', r'regex_buscar\b'),
            ('SUPER',       r'super\b'),
            ('INSTANCIA',   r'instancia\b'),
            ('ESTATICO',    r'estatico\b'),
            ('GLOBAL',      r'global\b'),
            ('NULO',        r'nulo\b'),
            ('IDENTIFICADOR', r'[a-zA-Z_]\w*'),
            ('STRING_TRIPLE', r'"""[^"]*"""|\'\'\'[^\']*\'\'\''),
            ('STRING',      r'"[^"]*"|\'[^\']*\''),
            ('NUMERO',      r'\d+(\.\d+)?'),
            ('IGUAL_IGUAL', r'=='),
            ('DIFERENTE',   r'!='),
            ('MAYOR_IGUAL', r'>='),
            ('MENOR_IGUAL', r'<='),
            ('MAS_IGUAL',   r'\+='),
            ('MENOS_IGUAL', r'-='),
            ('POR_IGUAL',   r'\*='),
            ('ENTRE_IGUAL', r'/='),
            ('MOD_IGUAL',   r'%='),
            ('ASIGNACION',  r'='),
            ('PUNTO',       r'\.'),
            ('MODULO',      r'%'),
            ('MAYOR',       r'>'),
            ('MENOR',       r'<'),
            ('MAS',         r'\+'),
            ('MENOS',       r'-'),
            ('POR',         r'\*'),
            ('ENTRE',       r'/'),
            ('PAREN_IZQ',   r'\('),
            ('PAREN_DER',   r'\)'),
            ('LLAVE_IZQ',   r'\{'),
            ('LLAVE_DER',   r'\}'),
            ('CORCHETE_IZQ', r'\['),
            ('CORCHETE_DER', r'\]'),
            ('DOS_PUNTOS',  r':'),
            ('COMA',        r','),
            ('COMENTARIO',  r'#.*'),
            ('NEWLINE',     r'\n'),
            ('SKIP',        r'[ \t\r]+'),
            ('MISMATCH',    r'.'),
        ]

        tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)

        for mo in re.finditer(tok_regex, self.code):
            kind = mo.lastgroup
            value = mo.group()

            if kind == 'NEWLINE':
                self.line += 1
                continue
            elif kind == 'SKIP' or kind == 'COMENTARIO':
                continue
            elif kind == 'MISMATCH':
                sugerencia = obtener_sugerencia(value)
                mensaje = (
                    f'Error lexico en linea {self.line}: "{value}"'
                )
                if sugerencia:
                    mensaje += f'. Quisiste decir "{sugerencia}"?'
                raise RuntimeError(mensaje)
            elif kind == 'STRING_TRIPLE':
                value = value[3:-3]
            elif kind == 'STRING':
                value = value[1:-1]
            elif kind == 'NUMERO':
                value = float(value) if '.' in value else int(value)

            self.tokens.append((Token[kind], value, self.line))

        self.tokens.append((Token.EOF, None, self.line))
        return self.tokens
