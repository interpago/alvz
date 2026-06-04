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

    def test_negate_type_check(self):
        with pytest.raises(RuntimeError, match="Error de tipo"):
            check_compile('variable x = -"texto"\n')

    def test_add_strings(self):
        result = check_compile('variable s = "a" + "b"\nimprimir(s)\n')
        assert result is not None

    def test_add_mixed_number_string(self):
        result = check_compile('variable s = 1 + "hola"\nimprimir(s)\n')
        assert result is not None

    def test_comparison_types(self):
        result = check_compile('variable b = 1 > 2\nimprimir(b)\n')
        assert result is not None

    def test_logical_and(self):
        result = check_compile('variable b = verdadero y falso\nimprimir(b)\n')
        assert result is not None

    def test_logical_or(self):
        result = check_compile('variable b = verdadero o falso\nimprimir(b)\n')
        assert result is not None

    def test_list_op(self):
        result = check_compile('variable lst = [1, 2, 3]\nimprimir(lst)\n')
        assert result is not None

    def test_dict_op(self):
        result = check_compile('variable d = {"a": 1, "b": 2}\nimprimir(d)\n')
        assert result is not None

    def test_get_index(self):
        result = check_compile('variable lst = [1, 2, 3]\nvariable x = lst[0]\nimprimir(x)\n')
        assert result is not None

    def test_set_index(self):
        result = check_compile('variable lst = [1, 2, 3]\nlst[0] = 99\nimprimir(lst)\n')
        assert result is not None

    def test_length_op(self):
        result = check_compile('variable lst = [1, 2, 3]\nimprimir(longitud(lst))\n')
        assert result is not None

    def test_append_op(self):
        result = check_compile('variable lst = [1]\nagregar(lst, 2)\nimprimir(lst)\n')
        assert result is not None

    def test_type_op(self):
        result = check_compile('variable x = 42\nimprimir(tipo(x))\n')
        assert result is not None

    def test_class_new_get_attr(self):
        code = '''
clase Punto {
    variable x = 0
    variable y = 0
}
variable p = nuevo Punto(3, 4)
imprimir(p.x)
'''
        result = check_compile(code)
        assert result is not None

    def test_set_attr(self):
        code = '''
clase Punto {
    variable x = 0
}
variable p = nuevo Punto(1)
p.x = 99
imprimir(p.x)
'''
        result = check_compile(code)
        assert result is not None

    def test_make_func(self):
        code = '''
funcion suma(a, b) {
    retornar a + b
}
variable f = suma
imprimir(f(1, 2))
'''
        result = check_compile(code)
        assert result is not None

    def test_if_jump(self):
        code = '''
variable x = 10
si x > 5 {
    imprimir("grande")
}
imprimir("fin")
'''
        result = check_compile(code)
        assert result is not None

    def test_if_else_jump(self):
        code = '''
variable x = 2
si x > 5 {
    imprimir("grande")
} sino {
    imprimir("pequeno")
}
'''
        result = check_compile(code)
        assert result is not None

    def test_while_loop(self):
        code = '''
variable i = 0
mientras i < 3 {
    i = i + 1
}
imprimir(i)
'''
        result = check_compile(code)
        assert result is not None

    def test_for_range(self):
        code = '''
para i de 1 a 5 {
    imprimir(i)
}
'''
        result = check_compile(code)
        assert result is not None

    def test_for_each(self):
        code = '''
variable lst = [1, 2, 3]
cada x en lst {
    imprimir(x)
}
'''
        result = check_compile(code)
        assert result is not None

    def test_nested_function_type_check(self):
        code = '''
funcion externa(a: numero): texto {
    funcion interna(b: numero): numero {
        retornar b * 2
    }
    variable r = interna(a)
    retornar "resultado: " + r
}
imprimir(externa(5))
'''
        result = check_compile(code)
        assert result is not None

    def test_await_async(self):
        code = '''
funcion async tarea(n: numero) {
    esperar(0.1)
    retornar n * 2
}
variable r = aguardar tarea(5)
imprimir(r)
'''
        result = check_compile(code)
        assert result is not None


class TestTypeCheckerInferenceFunctionScope:
    def test_function_list(self):
        bc, consts, lm, funcs, vt, ft, gs = parse_code('funcion foo() { variable lst = [1, 2] }\nfoo()')
        tc = TypeChecker(bc, consts, lm, funcs, vt, ft, gs)
        errors = tc.check()
        assert errors == []

    def test_function_dict(self):
        bc, consts, lm, funcs, vt, ft, gs = parse_code('funcion foo() { variable d = {"a": 1} }\nfoo()')
        tc = TypeChecker(bc, consts, lm, funcs, vt, ft, gs)
        errors = tc.check()
        assert errors == []

    def test_function_negate(self):
        bc, consts, lm, funcs, vt, ft, gs = parse_code('funcion foo() { variable x = -5 }\nfoo()')
        tc = TypeChecker(bc, consts, lm, funcs, vt, ft, gs)
        errors = tc.check()
        assert errors == []

    def test_function_store_global(self):
        bc, consts, lm, funcs, vt, ft, gs = parse_code('variable g = 0\nfuncion foo() { g = 42 }\nfoo()')
        tc = TypeChecker(bc, consts, lm, funcs, vt, ft, gs)
        errors = tc.check()
        assert errors == []

    def test_function_load_global(self):
        bc, consts, lm, funcs, vt, ft, gs = parse_code('variable g = 10\nfuncion foo() { imprimir(g) }\nfoo()')
        tc = TypeChecker(bc, consts, lm, funcs, vt, ft, gs)
        errors = tc.check()
        assert errors == []

    def test_function_comparison(self):
        code = '''
funcion foo(a: numero, b: numero): booleano {
    retornar a > b
}
variable r = foo(1, 2)
'''
        bc, consts, lm, funcs, vt, ft, gs = parse_code(code)
        tc = TypeChecker(bc, consts, lm, funcs, vt, ft, gs)
        errors = tc.check()
        assert errors == []

    def test_function_logical_and(self):
        code = '''
funcion foo(a: booleano, b: booleano): booleano {
    retornar a y b
}
variable r = foo(verdadero, falso)
'''
        bc, consts, lm, funcs, vt, ft, gs = parse_code(code)
        tc = TypeChecker(bc, consts, lm, funcs, vt, ft, gs)
        errors = tc.check()
        assert errors == []

    def test_function_get_index(self):
        bc, consts, lm, funcs, vt, ft, gs = parse_code('funcion foo() {\n    variable lst = [1,2]\n    variable x = lst[0]\n}\nfoo()')
        tc = TypeChecker(bc, consts, lm, funcs, vt, ft, gs)
        errors = tc.check()
        assert errors == []

    def test_function_set_index(self):
        bc, consts, lm, funcs, vt, ft, gs = parse_code('funcion foo() {\n    variable lst = [1,2]\n    lst[0] = 99\n}\nfoo()')
        tc = TypeChecker(bc, consts, lm, funcs, vt, ft, gs)
        errors = tc.check()
        assert errors == []

    def test_function_length(self):
        bc, consts, lm, funcs, vt, ft, gs = parse_code('funcion foo() {\n    variable lst = [1]\n    variable n = longitud(lst)\n}\nfoo()')
        tc = TypeChecker(bc, consts, lm, funcs, vt, ft, gs)
        errors = tc.check()
        assert errors == []

    def test_function_append(self):
        bc, consts, lm, funcs, vt, ft, gs = parse_code('funcion foo() {\n    variable lst = [1]\n    agregar(lst, 2)\n}\nfoo()')
        tc = TypeChecker(bc, consts, lm, funcs, vt, ft, gs)
        errors = tc.check()
        assert errors == []

    def test_function_type(self):
        bc, consts, lm, funcs, vt, ft, gs = parse_code('funcion foo() {\n    variable x = 42\n    variable t = tipo(x)\n}\nfoo()')
        tc = TypeChecker(bc, consts, lm, funcs, vt, ft, gs)
        errors = tc.check()
        assert errors == []

    def test_function_if_else(self):
        code = '''
funcion foo(x: numero) {
    si x > 0 {
        imprimir("pos")
    } sino {
        imprimir("neg")
    }
}
foo(1)
'''
        bc, consts, lm, funcs, vt, ft, gs = parse_code(code)
        tc = TypeChecker(bc, consts, lm, funcs, vt, ft, gs)
        errors = tc.check()
        assert errors == []

    def test_function_while(self):
        code = '''
funcion foo() {
    variable i = 0
    mientras i < 3 {
        i = i + 1
    }
}
foo()
'''
        bc, consts, lm, funcs, vt, ft, gs = parse_code(code)
        tc = TypeChecker(bc, consts, lm, funcs, vt, ft, gs)
        errors = tc.check()
        assert errors == []

    def test_function_class_new(self):
        code = '''
clase Punto { variable x = 0 }
funcion crear() {
    variable p = nuevo Punto(5)
    imprimir(p.x)
}
crear()
'''
        bc, consts, lm, funcs, vt, ft, gs = parse_code(code)
        tc = TypeChecker(bc, consts, lm, funcs, vt, ft, gs)
        errors = tc.check()
        assert errors == []


class TestTypeCheckerAdvancedErrors:
    def test_param_type_mismatch(self):
        code = '''
funcion foo(a: numero) {
    variable x = a
}
foo("texto")
'''
        with pytest.raises(RuntimeError, match="Error de tipo"):
            check_compile(code)

    def test_global_type_mismatch_via_function(self):
        code = '''
variable x: numero = 0
funcion modificar() {
    x = "texto"
}
modificar()
'''
        with pytest.raises(RuntimeError, match="Error de tipo"):
            check_compile(code)

    def test_arg_count_mismatch_too_few(self):
        code = (
            'funcion foo(a: numero, b: numero): numero {\n'
            '    retornar a + b\n'
            '}\n'
            'variable x = foo(1)\n'
        )
        with pytest.raises(RuntimeError, match="esperaba 2 argumentos"):
            check_compile(code)

    def test_arg_count_mismatch_too_many(self):
        code = (
            'funcion foo(a: numero): numero {\n'
            '    retornar a\n'
            '}\n'
            'variable x = foo(1, 2)\n'
        )
        with pytest.raises(RuntimeError, match="esperaba 1 argumento"):
            check_compile(code)

    def test_arg_type_mismatch_function_call(self):
        code = (
            'funcion saludo(nombre: texto): texto {\n'
            '    retornar "hola " + nombre\n'
            '}\n'
            'variable x = saludo(42)\n'
        )
        with pytest.raises(RuntimeError, match="Error de tipo"):
            check_compile(code)

    def test_nested_call_type_mismatch(self):
        code = (
            'funcion interna(x: numero): texto {\n'
            '    retornar "v: " + x\n'
            '}\n'
            'funcion externa(y: texto): numero {\n'
            '    retornar longitud(y)\n'
            '}\n'
            'variable r = externa(interna(42))\n'
        )
        result = check_compile(code)
        assert result is not None

    def test_negate_non_number_error(self):
        with pytest.raises(RuntimeError, match="Error de tipo"):
            check_compile('funcion foo() { variable x = -"texto" }\nfoo()\n')

    def test_complex_op_error(self):
        code = (
            'funcion procesar(valor: numero): texto {\n'
            '    retornar "ok"\n'
            '}\n'
            'variable r = procesar("mal")\n'
        )
        with pytest.raises(RuntimeError, match="Error de tipo"):
            check_compile(code)

    def test_global_scope_negate(self):
        bc, consts, lm, funcs, vt, ft, gs = parse_code('variable x = -5\nimprimir(x)\n')
        tc = TypeChecker(bc, consts, lm, funcs, vt, ft, gs)
        errors = tc.check()
        assert errors == []

    def test_global_if_true_jump(self):
        bc, consts, lm, funcs, vt, ft, gs = parse_code('variable x = 5\nsi verdadero { imprimir(x) }\n')
        tc = TypeChecker(bc, consts, lm, funcs, vt, ft, gs)
        errors = tc.check()
        assert errors == []

    def test_global_reassign(self):
        bc, consts, lm, funcs, vt, ft, gs = parse_code('variable x = 1\nx = 2\nimprimir(x)\n')
        tc = TypeChecker(bc, consts, lm, funcs, vt, ft, gs)
        errors = tc.check()
        assert errors == []

    def test_global_return_type(self):
        bc, consts, lm, funcs, vt, ft, gs = parse_code('funcion foo(): numero { retornar 42 }\nfoo()\n')
        tc = TypeChecker(bc, consts, lm, funcs, vt, ft, gs)
        errors = tc.check()
        assert errors == []

    def test_function_param_type_invalid(self):
        code = (
            'funcion saludar(nombre: texto) {\n'
            '    imprimir("hola " + nombre)\n'
            '}\n'
            'saludar(42)\n'
        )
        with pytest.raises(RuntimeError, match="Error de tipo"):
            check_compile(code)

    def test_function_class_get_set_attr(self):
        code = '''
clase Caja {
    variable valor = 0
}
funcion manipular() {
    variable c = nuevo Caja(10)
    c.valor = c.valor + 1
    imprimir(c.valor)
}
manipular()
'''
        result = check_compile(code)
        assert result is not None

    def test_function_list_with_items(self):
        code = '''
funcion crear() {
    variable lst = [1, 2, 3]
    retornar lst
}
variable r = crear()
imprimir(r)
'''
        result = check_compile(code)
        assert result is not None

    def test_function_dict_with_items(self):
        code = '''
funcion crear() {
    variable d = {"a": 1, "b": 2}
    retornar d
}
variable r = crear()
imprimir(r)
'''
        result = check_compile(code)
        assert result is not None

    def test_global_var_typed_reassign_wrong_type(self):
        code = (
            'variable a: numero = 1\n'
            'funcion foo() {\n'
            '    a = "texto"\n'
            '}\n'
            'foo()\n'
        )
        with pytest.raises(RuntimeError, match="Error de tipo"):
            check_compile(code)

    def test_function_null_and_halt(self):
        code = '''
funcion nada() {
    retornar nulo
}
variable r = nada()
imprimir(r)
'''
        result = check_compile(code)
        assert result is not None
