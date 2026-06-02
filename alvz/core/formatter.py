"""
Formateador de codigo Alvz.

Convierte codigo fuente Alvz en codigo formateado consistentemente,
preservando comentarios y strings.
"""

import re


_TOKEN_SPEC = [
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
    ('PROPIEDAD',   r'propiedad\b'),
    ('OBTENER_SALIDA', r'obtener_salida\b'),
    ('OBTENER',     r'obtener\b'),
    ('ESTABLECER',  r'establecer\b'),
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
    ('STRING_TRIPLE', r'"""(?:(?!""").)*"""|\'\'\'(?:(?!\'\'\').)*\'\'\''),
    ('STRING',      r'"(?:[^"\\]|\\.)*"|\'(?:[^\'\\]|\\.)*\''),
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
    ('ESPACIO',     r'[ \t]+'),
    ('MISMATCH',    r'.'),
]

_TOKEN_RE = re.compile('|'.join(f'(?P<{name}>{pattern})' for name, pattern in _TOKEN_SPEC))

_OPEN_BRACES = {'LLAVE_IZQ', 'PAREN_IZQ', 'CORCHETE_IZQ'}
_CLOSE_BRACES = {'LLAVE_DER', 'PAREN_DER', 'CORCHETE_DER'}
_NO_SPACE_BEFORE = {'COMA', 'PAREN_DER', 'CORCHETE_DER', 'LLAVE_DER', 'PUNTO',
                    'DOS_PUNTOS'}
_NO_SPACE_AFTER = {'PAREN_IZQ', 'CORCHETE_IZQ', 'PUNTO', 'LLAVE_IZQ'}
_SPACE_BEFORE = {'Y', 'O', 'IGUAL_IGUAL', 'DIFERENTE', 'MAYOR', 'MENOR',
                 'MAYOR_IGUAL', 'MENOR_IGUAL', 'MAS', 'MENOS', 'POR',
                 'ENTRE', 'MODULO', 'ASIGNACION', 'MAS_IGUAL', 'MENOS_IGUAL',
                 'POR_IGUAL', 'ENTRE_IGUAL', 'MOD_IGUAL', 'COMA',
                 'DOS_PUNTOS', 'INSTANCIA'}
_SPACE_AFTER = {'COMA', 'Y', 'O', 'IGUAL_IGUAL', 'DIFERENTE', 'MAYOR', 'MENOR',
                'MAYOR_IGUAL', 'MENOR_IGUAL', 'MAS', 'MENOS', 'POR',
                'ENTRE', 'MODULO', 'ASIGNACION', 'MAS_IGUAL', 'MENOS_IGUAL',
                'POR_IGUAL', 'ENTRE_IGUAL', 'MOD_IGUAL', 'DOS_PUNTOS',
                'INSTANCIA'}
_KEYWORDS = {'VARIABLE', 'FUNCION', 'CLASE', 'SI', 'SINO', 'MIENTRAS', 'PARA',
             'CADA', 'RETORNAR', 'IMPORTAR', 'INTENTAR', 'CAPTURAR', 'LANZAR',
             'GLOBAL', 'ESTATICO', 'ASYNC', 'AGUARDAR', 'ROMPER', 'CONTINUAR',
             'PROPIEDAD', 'OBTENER', 'ESTABLECER', 'NUEVO', 'SUPER'}


def _tokenize(code):
    tokens = []
    for mo in _TOKEN_RE.finditer(code):
        kind = mo.lastgroup
        value = mo.group()
        if kind == 'MISMATCH':
            raise RuntimeError(f"Caracter inesperado: {value!r}")
        tokens.append((kind, value, mo.start()))
    return tokens


def _fmt_tokens(tokens, indent_size=1):
    result = []
    indent_level = 0
    pending_newline = False
    paren_depth = [0]

    def out(s):
        nonlocal pending_newline
        if pending_newline:
            result.append('\n' + '\t' * indent_level)
            pending_newline = False
        result.append(s)

    def newline():
        nonlocal pending_newline
        pending_newline = True

    def space():
        if result and not result[-1].endswith(' ') and not result[-1].endswith('\t'):
            result.append(' ')

    i = 0
    while i < len(tokens):
        kind, value, pos = tokens[i]

        if kind == 'NEWLINE':
            if paren_depth[-1] == 0:
                newline()
            i += 1
            continue

        if kind == 'COMENTARIO':
            if result and not pending_newline:
                newline()
            out(value)
            newline()
            i += 1
            continue

        if kind == 'ESPACIO':
            i += 1
            continue

        if kind in _CLOSE_BRACES:
            if kind == 'LLAVE_DER':
                indent_level = max(0, indent_level - 1)
            if kind == 'PAREN_DER':
                paren_depth[-1] -= 1
            if not pending_newline and result:
                if result[-1] != ' ' and result[-1] != '\t':
                    pass
                while result and result[-1] in (' ', '\t'):
                    result.pop()
            out(value)
            i += 1
            continue

        if kind in _OPEN_BRACES:
            if kind == 'LLAVE_IZQ':
                out(' ')
                out(value)
                indent_level += 1
                newline()
            elif kind == 'PAREN_IZQ':
                paren_depth[-1] += 1
                out(value)
            elif kind == 'CORCHETE_IZQ':
                out(value)
            i += 1
            continue

        if pending_newline and kind not in ('NEWLINE', 'COMENTARIO', 'ESPACIO'):
            indent_adjust = indent_level
            result.append('\n' + '\t' * indent_adjust)
            pending_newline = False

        if result and result[-1] not in (' ', '\n', '\t') and not result[-1].endswith(' '):
            if kind not in _NO_SPACE_BEFORE:
                if kind in _SPACE_BEFORE:
                    space()
                elif result[-1] not in ('(', ' ', '\t') and kind not in ('PAREN_DER', 'CORCHETE_DER', 'LLAVE_DER', 'COMA', 'PUNTO'):
                    if result[-1] not in _OPEN_BRACES:
                        space()

        out(value)

        if kind not in _NO_SPACE_AFTER and kind in _SPACE_AFTER:
            space()

        i += 1

    return ''.join(result).strip() + '\n'


def formatear(codigo):
    """Formatea codigo fuente Alvz y retorna el codigo formateado."""
    tokens = _tokenize(codigo)
    return _fmt_tokens(tokens)


def main():
    import sys
    if len(sys.argv) < 2:
        print("Uso: alvz fmt <archivo.alvz> [--check]")
        sys.exit(1)

    args = sys.argv[1:]
    check_only = '--check' in args
    args = [a for a in args if a != '--check']

    for filename in args:
        with open(filename, 'r', encoding='utf-8-sig') as f:
            codigo = f.read()

        try:
            formateado = formatear(codigo)
        except Exception as e:
            print(f"Error al formatear {filename}: {e}")
            sys.exit(1)

        if check_only:
            if codigo != formateado:
                print(f"{filename}: necesita formateo")
                sys.exit(1)
            print(f"{filename}: bien formateado")
        else:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(formateado)
            print(f"Formateado: {filename}")


if __name__ == '__main__':
    main()
