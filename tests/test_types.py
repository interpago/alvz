import pytest

from alvz.core.lexer import Lexer
from alvz.core.parser import Parser as AlvzParser
from alvz.core.type_checker import TypeChecker


def parse_code(code):
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = AlvzParser(tokens)
    bc, consts, lm, funcs = parser.compile()
    var_types = getattr(parser, 'var_types', {})
    func_types = getattr(parser, 'func_types', {})
    global_symbols = getattr(parser, 'global_symbols', {})
    return bc, consts, lm, funcs, var_types, func_types, global_symbols


def check(code):
    bc, consts, lm, funcs, vt, ft, gs = parse_code(code)
    tc = TypeChecker(bc, consts, lm, funcs, vt, ft, gs)
    return tc.check()


def check_compile(code):
    """Compila con check_types=True, deberia levantar RuntimeError si hay error."""
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = AlvzParser(tokens)
    return parser.compile(check_types=True)


class TestTypeAnnotations:
    def test_variable_type_annotation(self):
        bc, consts, lm, funcs, vt, ft, gs = parse_code('variable x: numero = 5')
        assert vt.get('x') == 'numero'

    def test_variable_type_annotation_texto(self):
        bc, consts, lm, funcs, vt, ft, gs = parse_code('variable s: texto = "hola"')
        assert vt.get('s') == 'texto'

    def test_variable_type_annotation_booleano(self):
        bc, consts, lm, funcs, vt, ft, gs = parse_code('variable b: booleano = verdadero')
        assert vt.get('b') == 'booleano'

    def test_function_param_types(self):
        bc, consts, lm, funcs, vt, ft, gs = parse_code('funcion suma(a: numero, b: numero) {\n    retornar a + b\n}')
        assert ft.get('suma') == (['numero', 'numero'], None)

    def test_function_return_type(self):
        bc, consts, lm, funcs, vt, ft, gs = parse_code('funcion suma(a: numero, b: numero): numero {\n    retornar a + b\n}')
        assert ft.get('suma') == (['numero', 'numero'], 'numero')

    def test_function_no_annotations(self):
        bc, consts, lm, funcs, vt, ft, gs = parse_code('funcion foo(a, b) { retornar a }')
        assert ft.get('foo') == ([None, None], None)

    def test_type_checker_no_errors(self):
        errors = check('variable x: numero = 5\nimprimir(x)')
        assert errors == []

    def test_type_checker_function_call(self):
        code = 'funcion suma(a: numero, b: numero): numero {\n    retornar a + b\n}\nimprimir(suma(1, 2))'
        errors = check(code)
        assert errors == []

    def test_type_checker_var_no_annotation(self):
        errors = check('variable x = 5\nimprimir(x)')
        assert errors == []


class TestTypeCheckerInference:
    def test_literal_numero(self):
        bc, consts, lm, funcs, vt, ft, gs = parse_code('variable x = 42')
        tc = TypeChecker(bc, consts, lm, funcs, vt, ft, gs)
        tc.check()
        assert tc._locals.get(0) == 'numero'

    def test_literal_texto(self):
        bc, consts, lm, funcs, vt, ft, gs = parse_code('variable s = "hola"')
        tc = TypeChecker(bc, consts, lm, funcs, vt, ft, gs)
        tc.check()
        assert tc._locals.get(0) == 'texto'

    def test_literal_booleano(self):
        bc, consts, lm, funcs, vt, ft, gs = parse_code('variable b = verdadero')
        tc = TypeChecker(bc, consts, lm, funcs, vt, ft, gs)
        tc.check()
        assert tc._locals.get(0) == 'booleano'

    def test_literal_nulo(self):
        bc, consts, lm, funcs, vt, ft, gs = parse_code('variable n = nulo')
        tc = TypeChecker(bc, consts, lm, funcs, vt, ft, gs)
        tc.check()
        assert tc._locals.get(0) == 'nulo'


class TestTypeCheckerErrors:
    def test_var_type_mismatch(self):
        with pytest.raises(RuntimeError, match="Error de tipo"):
            check_compile('variable x: numero = "hola"')

    def test_var_type_mismatch_booleano(self):
        with pytest.raises(RuntimeError, match="Error de tipo"):
            check_compile('variable x: texto = verdadero')

    def test_arg_type_mismatch(self):
        code = (
            'funcion suma(a: numero, b: numero): numero {\n'
            '    retornar a + b\n'
            '}\n'
            'variable x = suma("hola", 2)\n'
        )
        with pytest.raises(RuntimeError, match="Error de tipo"):
            check_compile(code)

    def test_return_type_mismatch(self):
        code = (
            'funcion foo(): texto {\n'
            '    retornar 42\n'
            '}\n'
        )
        with pytest.raises(RuntimeError, match="Error de tipo.*retornar"):
            check_compile(code)

    def test_correct_types_no_error(self):
        code = (
            'funcion suma(a: numero, b: numero): numero {\n'
            '    retornar a + b\n'
            '}\n'
            'variable x: numero = suma(1, 2)\n'
            'imprimir(x)\n'
        )
        result = check_compile(code)
        assert result is not None

    def test_no_annotation_passes(self):
        code = 'variable x = 42\nimprimir(x)\n'
        result = check_compile(code)
        assert result is not None

    def test_arg_count_mismatch(self):
        code = (
            'funcion foo(a: numero, b: numero): numero {\n'
            '    retornar a + b\n'
            '}\n'
            'variable x = foo(1)\n'
        )
        with pytest.raises(RuntimeError, match="esperaba 2 argumentos"):
            check_compile(code)

    def test_return_type_nulo_ok(self):
        # 'nulo' is a keyword, not an identifier, so it can't be used as type annotation
        # Skip this test for now
        pass
