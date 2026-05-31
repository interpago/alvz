from alvz.core.lexer import Lexer, Token
from alvz.core.parser import Parser
from .protocol import SymbolKind


class Symbol:
    VARIABLE = 1
    FUNCION = 2
    CLASE = 3
    METODO = 4
    PROPIEDAD = 5
    PARAMETRO = 6
    BUILTIN = 7
    KEYWORD = 8

    def __init__(self, name, kind, line, col, uri='', detail=''):
        self.name = name
        self.kind = kind
        self.line = line
        self.col = col
        self.uri = uri
        self.detail = detail

    def __repr__(self):
        return f'Symbol({self.name}, kind={self.kind}, line={self.line})'


class Scope:
    def __init__(self, parent=None, type_='global'):
        self.parent = parent
        self.type = type_
        self.symbols = {}
        self.children = []

    def define(self, name, symbol):
        self.symbols[name] = symbol

    def resolve(self, name):
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.resolve(name)
        return None

    def resolve_local(self, name):
        return self.symbols.get(name)


_BUILTIN_FUNCTIONS = {
    'imprimir', 'leer', 'leer_numero', 'azar', 'limpiar',
    'reemplazar', 'absoluto', 'redondear', 'potencia', 'raiz',
    'longitud', 'agregar', 'esperar', 'enviar_web', 'escribir_archivo',
    'obtener_salida', 'minusculas', 'mayusculas', 'iniciar_servidor',
    'tipo', 'fecha_actual', 'dividir', 'unir', 'a_numero', 'regex_buscar',
    'lanzar', 'error_msj',
}

_KEYWORDS = {
    'si', 'sino', 'mientras', 'para', 'cada', 'en', 'de', 'a',
    'funcion', 'retornar', 'variable', 'verdadero', 'falso', 'y', 'o',
    'importar', 'intentar', 'capturar', 'romper', 'continuar',
    'clase', 'nuevo', 'super', 'instancia', 'estatico',
    'propiedad', 'obtener', 'establecer',
}


class Analyzer:
    def __init__(self):
        self.uris = {}
        self.global_scope = Scope(type_='global')

    def open_file(self, uri, code):
        self.uris[uri] = code
        return self._analyze(uri, code)

    def update_file(self, uri, code):
        self.uris[uri] = code
        return self._analyze(uri, code)

    def close_file(self, uri):
        self.uris.pop(uri, None)

    def get_symbols(self, uri):
        code = self.uris.get(uri)
        if code is None:
            return []
        return self._build_symbols(uri, code)

    def find_definition(self, uri, line, col):
        code = self.uris.get(uri)
        if code is None:
            return None
        return self._find_def(uri, code, line, col)

    def get_completions(self, uri, line, col):
        code = self.uris.get(uri)
        if code is None:
            return []
        return self._get_completions(uri, code, line, col)

    def get_hover(self, uri, line, col):
        code = self.uris.get(uri)
        if code is None:
            return None
        return self._get_hover(uri, code, line, col)

    def _tokenize(self, code):
        try:
            lexer = Lexer(code)
            return lexer.tokenize()
        except RuntimeError as e:
            raise e
        except Exception:
            return []

    def _parse_error_to_dict(self, e):
        msg = str(e)
        line = 1
        col = 0
        if 'linea' in msg:
            try:
                line = int(msg.split('linea ')[1].split(')')[0])
            except (IndexError, ValueError):
                pass
        return {'line': line, 'col': col, 'message': msg, 'severity': 1}

    def _analyze(self, uri, code):
        errors = []
        try:
            lexer = Lexer(code)
            tokens = lexer.tokenize()
        except RuntimeError as e:
            errors.append(self._parse_error_to_dict(e))
            tokens = []
        except Exception as e:
            errors.append({'line': 1, 'col': 0, 'message': str(e), 'severity': 1})
            tokens = []

        if tokens:
            self._check_syntax(uri, tokens, code, errors)
            try:
                parser = Parser(tokens)
                parser.compile(check_types=False)
            except RuntimeError as e:
                errors.append(self._parse_error_to_dict(e))
            except Exception as e:
                errors.append({'line': 1, 'col': 0, 'message': f"Error interno: {e}", 'severity': 1})

        return errors

    def _check_syntax(self, uri, tokens, code, errors):
        lines = code.split('\n')

        depth_paren = 0
        depth_brace = 0
        depth_bracket = 0

        for t in tokens:
            t_type, t_val, t_line = t
            if t_type == Token.PAREN_IZQ:
                depth_paren += 1
            elif t_type == Token.PAREN_DER:
                depth_paren -= 1
                if depth_paren < 0:
                    errors.append({
                        'line': t_line,
                        'col': 0,
                        'message': "Parentesis de cierre sin apertura",
                        'severity': 1,
                    })
                    depth_paren = 0
            elif t_type == Token.LLAVE_IZQ:
                depth_brace += 1
            elif t_type == Token.LLAVE_DER:
                depth_brace -= 1
                if depth_brace < 0:
                    errors.append({
                        'line': t_line,
                        'col': 0,
                        'message': "Llave de cierre sin apertura",
                        'severity': 1,
                    })
                    depth_brace = 0
            elif t_type == Token.CORCHETE_IZQ:
                depth_bracket += 1
            elif t_type == Token.CORCHETE_DER:
                depth_bracket -= 1
                if depth_bracket < 0:
                    errors.append({
                        'line': t_line,
                        'col': 0,
                        'message': "Corchete de cierre sin apertura",
                        'severity': 1,
                    })
                    depth_bracket = 0


        if depth_paren > 0:
            errors.append({
                'line': len(lines),
                'col': 0,
                'message': f"Faltan {depth_paren} parentesis de cierre",
                'severity': 1,
            })
        if depth_brace > 0:
            errors.append({
                'line': len(lines),
                'col': 0,
                'message': f"Faltan {depth_brace} llaves de cierre",
                'severity': 1,
            })

    def _find_col(self, lines, line, val):
        try:
            idx = lines[line - 1].find(val)
            return max(0, idx)
        except (IndexError, ValueError):
            return 0

    def _build_symbols(self, uri, code):
        tokens = self._tokenize(code)
        symbols = []
        i = 0
        while i < len(tokens):
            t_type, t_val, t_line = tokens[i]
            if t_type == Token.FUNCION:
                i += 1
                if i < len(tokens) and tokens[i][0] == Token.ESTATICO:
                    i += 1
                if i < len(tokens) and tokens[i][0] == Token.IDENTIFICADOR:
                    name = tokens[i][1]
                    line = tokens[i][2]
                    symbols.append({
                        'name': name,
                        'kind': SymbolKind.FUNCTION,
                        'line': line,
                        'col': 0,
                        'detail': 'funcion',
                        'selectionRange': {'start': {'line': line - 1, 'character': 0}, 'end': {'line': line - 1, 'character': len(name)}},
                    })
            elif t_type == Token.VARIABLE:
                if i + 1 < len(tokens) and tokens[i + 1][0] == Token.IDENTIFICADOR:
                    name = tokens[i + 1][1]
                    line = tokens[i + 1][2]
                    symbols.append({
                        'name': name,
                        'kind': SymbolKind.VARIABLE,
                        'line': line,
                        'col': 0,
                        'detail': 'variable',
                        'selectionRange': {'start': {'line': line - 1, 'character': 0}, 'end': {'line': line - 1, 'character': len(name)}},
                    })
            elif t_type == Token.CLASE:
                if i + 1 < len(tokens) and tokens[i + 1][0] == Token.IDENTIFICADOR:
                    name = tokens[i + 1][1]
                    line = tokens[i + 1][2]
                    symbols.append({
                        'name': name,
                        'kind': SymbolKind.CLASS,
                        'line': line,
                        'col': 0,
                        'detail': 'clase',
                        'selectionRange': {'start': {'line': line - 1, 'character': 0}, 'end': {'line': line - 1, 'character': len(name)}},
                    })
            elif t_type == Token.PROPIEDAD:
                if i + 1 < len(tokens) and tokens[i + 1][0] == Token.IDENTIFICADOR:
                    name = tokens[i + 1][1]
                    line = tokens[i + 1][2]
                    symbols.append({
                        'name': name,
                        'kind': SymbolKind.PROPERTY,
                        'line': line,
                        'col': 0,
                        'detail': 'propiedad',
                        'selectionRange': {'start': {'line': line - 1, 'character': 0}, 'end': {'line': line - 1, 'character': len(name)}},
                    })
            i += 1
        return symbols

    def _find_def(self, uri, code, line, col):
        tokens = self._tokenize(code)
        target_word = self._word_at(code, line, col)
        if not target_word:
            return None

        defs = []
        i = 0
        while i < len(tokens):
            t_type, t_val, t_line = tokens[i]

            if t_type == Token.FUNCION:
                j = i + 1
                if j < len(tokens) and tokens[j][0] == Token.ESTATICO:
                    j += 1
                if j < len(tokens) and tokens[j][0] == Token.IDENTIFICADOR and tokens[j][1] == target_word:
                    defs.append({
                        'uri': uri,
                        'line': tokens[j][2],
                        'col': 0,
                    })
            elif t_type == Token.VARIABLE:
                if i + 1 < len(tokens) and tokens[i + 1][0] == Token.IDENTIFICADOR and tokens[i + 1][1] == target_word:
                    defs.append({
                        'uri': uri,
                        'line': tokens[i + 1][2],
                        'col': 0,
                    })
            elif t_type == Token.CLASE:
                if i + 1 < len(tokens) and tokens[i + 1][0] == Token.IDENTIFICADOR and tokens[i + 1][1] == target_word:
                    defs.append({
                        'uri': uri,
                        'line': tokens[i + 1][2],
                        'col': 0,
                    })
            i += 1

        if defs:
            d = defs[-1]
            return {
                'uri': d['uri'],
                'range': {
                    'start': {'line': d['line'] - 1, 'character': d['col']},
                    'end': {'line': d['line'] - 1, 'character': d['col'] + len(target_word)},
                },
            }
        return None

    def _word_at(self, code, line, col):
        lines = code.split('\n')
        if line < 0 or line >= len(lines):
            return None
        text = lines[line]
        if col < 0 or col >= len(text):
            return None
        start = col
        while start > 0 and (text[start - 1].isalnum() or text[start - 1] == '_'):
            start -= 1
        end = col
        while end < len(text) and (text[end].isalnum() or text[end] == '_'):
            end += 1
        return text[start:end] if end > start else None

    def _get_completions(self, uri, code, line, col):
        items = []

        for kw in sorted(_KEYWORDS):
            items.append({
                'label': kw,
                'kind': 14,
                'detail': 'keyword',
            })

        for bf in sorted(_BUILTIN_FUNCTIONS):
            items.append({
                'label': bf,
                'kind': 3,
                'detail': 'builtin',
            })

        tokens = self._tokenize(code)
        seen = {'a', 'en', 'de', 'y', 'o'}
        i = 0
        while i < len(tokens):
            t_type, t_val, t_line = tokens[i]

            if t_type == Token.IDENTIFICADOR and t_val not in seen:
                seen.add(t_val)
                items.append({
                    'label': t_val,
                    'kind': 6,
                    'detail': 'identificador',
                })

            i += 1

        return items[:100]

    def _get_hover(self, uri, code, line, col):
        word = self._word_at(code, line, col)
        if not word:
            return None

        lines = code.split('\n')

        if word in _KEYWORDS:
            return {
                'contents': f'**{word}** — Palabra clave de Alvz',
                'range': self._word_range(lines, line, col),
            }

        if word in _BUILTIN_FUNCTIONS:
            return {
                'contents': f'**{word}** — Función incorporada de Alvz',
                'range': self._word_range(lines, line, col),
            }

        tokens = self._tokenize(code)
        for t_type, t_val, t_line in tokens:
            if t_val == word and t_type in (Token.IDENTIFICADOR, Token.FUNCION, Token.CLASE):
                return {
                    'contents': f'**{word}** — (linea {t_line})',
                    'range': self._word_range(lines, line, col),
                }

        return {
            'contents': f'`{word}`',
            'range': self._word_range(lines, line, col),
        }

    def _word_range(self, lines, line, col):
        text = lines[line] if 0 <= line < len(lines) else ''
        start = col
        while start > 0 and (text[start - 1].isalnum() or text[start - 1] == '_'):
            start -= 1
        end = col
        while end < len(text) and (text[end].isalnum() or text[end] == '_'):
            end += 1
        return {
            'start': {'line': line, 'character': start},
            'end': {'line': line, 'character': end},
        }
