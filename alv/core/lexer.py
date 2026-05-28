import enum
import re
import difflib

# ==========================================
# Utilidades de Errores Amigables
# ==========================================

KEYWORDS_ALVZ = [
    "variable", "imprimir", "leer", "leer_numero", "azar", "limpiar", "longitud", "agregar",
    "esperar", "enviar_web", "escribir_archivo", "minusculas", "mayusculas",
    "obtener_salida", "supabase_insertar", "leer_archivo", "supabase_consultar",
    "json_decodificar", "importar", "tiempo", "json_codificar",
    "reemplazar", "absoluto", "redondear", "potencia", "raiz", "intentar",
    "capturar", "lanzar", "clase", "nuevo", "error_msj", "funcion", "retornar",
    "si", "sino", "mientras", "para", "cada", "en", "de", "a", "verdadero",
    "falso", "y", "o", "iniciar_servidor"
]

def obtener_sugerencia(palabra_erronea, opciones=KEYWORDS_ALVZ):
    """Encuentra la palabra m s cercana a la err nea."""
    coincidencias = difflib.get_close_matches(palabra_erronea, opciones, n=1, cutoff=0.6)
    return coincidencias[0] if coincidencias else None


# ==========================================
# Tokens
# ==========================================

class Token(enum.Enum):
    VARIABLE     = "VARIABLE"
    IDENTIFICADOR = "IDENTIFICADOR"
    ASIGNACION   = "ASIGNACION"
    STRING       = "STRING"
    NUMERO       = "NUMERO"
    IMPRIMIR     = "IMPRIMIR"
    LEER         = "LEER"
    LEER_NUMERO  = "LEER_NUMERO"
    AZAR         = "AZAR"
    LIMPIAR      = "LIMPIAR"
    FUNCION      = "FUNCION"
    RETORNAR     = "RETORNAR"
    SI           = "SI"
    SINO         = "SINO"
    MIENTRAS     = "MIENTRAS"
    PARA         = "PARA"
    CADA         = "CADA"
    EN           = "EN"
    DE           = "DE"
    A            = "A"
    VERDADERO    = "VERDADERO"
    FALSO        = "FALSO"
    Y            = "Y"
    O            = "O"
    PAREN_IZQ    = "PAREN_IZQ"
    PAREN_DER    = "PAREN_DER"
    LLAVE_IZQ    = "LLAVE_IZQ"
    LLAVE_DER    = "LLAVE_DER"
    MAS          = "MAS"
    MENOS        = "MENOS"
    POR          = "POR"
    ENTRE        = "ENTRE"
    IGUAL_IGUAL  = "IGUAL_IGUAL"
    DIFERENTE    = "DIFERENTE"
    MAYOR        = "MAYOR"
    MENOR        = "MENOR"
    MAYOR_IGUAL  = "MAYOR_IGUAL"
    MENOR_IGUAL  = "MENOR_IGUAL"
    COMA         = "COMA"
    CORCHETE_IZQ = "CORCHETE_IZQ"
    CORCHETE_DER = "CORCHETE_DER"
    COMENTARIO   = "COMENTARIO"
    LONGITUD     = "LONGITUD"
    AGREGAR      = "AGREGAR"
    ESPERAR      = "ESPERAR"
    ENVIAR_WEB   = "ENVIAR_WEB"
    ESCRIBIR_ARCHIVO = "ESCRIBIR_ARCHIVO"
    MINUSCULAS   = "MINUSCULAS"
    MAYUSCULAS   = "MAYUSCULAS"
    OBTENER_SALIDA = "OBTENER_SALIDA"
    SUPABASE_INSERTAR = "SUPABASE_INSERTAR"
    REDONDEAR    = "REDONDEAR"
    POTENCIA     = "POTENCIA"
    RAIZ         = "RAIZ"
    INTENTAR     = "INTENTAR"
    CAPTURAR     = "CAPTURAR"
    LANZAR       = "LANZAR"
    CLASE        = "CLASE"
    NUEVO        = "NUEVO"
    PUNTO        = "PUNTO"
    MODULO       = "MODULO"
    ERROR_MSJ    = "ERROR_MSJ"
    LEER_ARCHIVO = "LEER_ARCHIVO"
    SUPABASE_CONSULTAR = "SUPABASE_CONSULTAR"
    JSON_DECODIFICAR = "JSON_DECODIFICAR"
    IMPORTAR     = "IMPORTAR"
    TIEMPO       = "TIEMPO"
    JSON_CODIFICAR = "JSON_CODIFICAR"
    TIPO_KW      = "TIPO_KW"
    REEMPLAZAR   = "REEMPLAZAR"
    ABSOLUTO     = "ABSOLUTO"
    INICIAR_SERVIDOR = "INICIAR_SERVIDOR"
    DOS_PUNTOS   = "DOS_PUNTOS"
    EOF          = "EOF"


# ==========================================
# Lexer
# ==========================================

class Lexer:
    """Convierte el texto fuente en una secuencia de tokens."""
    def __init__(self, code):
        self.code = code
        self.tokens = []
        self.pos = 0
        self.line_count = 1

    def tokenize(self):
        # Definici n de patrones para los tokens
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
            ('OBTENER_SALIDA', r'obtener_salida\b'),
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
            ('IDENTIFICADOR', r'[a-zA-Z_]\w*'),
            ('TIPO_KW',     r'tipo\b'),
            ('REEMPLAZAR',  r'reemplazar\b'),
            ('ABSOLUTO',    r'absoluto\b'),
            ('INICIAR_SERVIDOR', r'iniciar_servidor\b'),
            ('REDONDEAR',   r'redondear\b'),
            ('POTENCIA',    r'potencia\b'),
            ('RAIZ',        r'raiz\b'),
            ('INTENTAR',    r'intentar\b'),
            ('CAPTURAR',    r'capturar\b'),
            ('LANZAR',      r'lanzar\b'),
            ('ERROR_MSJ',   r'error_msj\b'),
            ('STRING',      r'"[^"]*"|\'[^\']*\''),
            ('NUMERO',      r'\d+(\.\d+)?'),
            ('IGUAL_IGUAL', r'=='),
            ('DIFERENTE',   r'!='),
            ('MAYOR_IGUAL', r'>='),
            ('MENOR_IGUAL', r'<='),
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
                self.line_count += 1
                continue
            elif kind == 'SKIP' or kind == 'COMENTARIO':
                continue
            elif kind == 'MISMATCH':
                sugerencia = obtener_sugerencia(value)
                mensaje = f'Error l xico en l nea {self.line_count}: Car cter inesperado "{value}"'
                if sugerencia:
                    mensaje += f'.  Quisiste decir "{sugerencia}"?'
                raise RuntimeError(mensaje)
            elif kind == 'STRING':
                value = value[1:-1]
            elif kind == 'NUMERO':
                value = float(value) if '.' in value else int(value)
            
            self.tokens.append((Token[kind], value, self.line_count))
        
        self.tokens.append((Token.EOF, None, self.line_count))
        return self.tokens
