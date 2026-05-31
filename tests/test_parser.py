import pytest
from alvz.core.lexer import Lexer
from alvz.core.parser import Parser
from alvz.core.bytecode import OpCode


def parse(code):
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.compile()


def parse_and_collect(code):
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    bytecode, constants, line_map, funcs = parser.compile()
    return bytecode, constants, line_map, funcs, parser


class TestParserAssignment:
    def test_simple_assignment(self):
        bytecode, constants, _, _, _ = parse_and_collect("variable x = 42")
        assert len(bytecode) >= 3
        assert bytecode[0] == OpCode.OP_CONSTANT
        assert 42 in constants

    def test_string_assignment(self):
        bytecode, constants, _, _, _ = parse_and_collect('variable x = "hola"')
        assert "hola" in constants
        assert OpCode.OP_CONSTANT in bytecode

    def test_multiple_assignments(self):
        bc, constants, _, _, _ = parse_and_collect("variable num1 = 1\nvariable num2 = 2")
        assert 1 in constants
        assert 2 in constants
        assert bc.count(OpCode.OP_STORE_GLOBAL) >= 2

    def test_boolean_true(self):
        bc, constants, _, _, _ = parse_and_collect("variable x = verdadero")
        assert True in constants

    def test_boolean_false(self):
        bc, constants, _, _, _ = parse_and_collect("variable x = falso")
        assert False in constants

    def test_null_keyword(self):
        bc, _, _, _, _ = parse_and_collect("variable x = nulo")
        assert OpCode.OP_NULL in bc


class TestParserPrint:
    def test_print_literal(self):
        bc, _, _, _, _ = parse_and_collect('imprimir("hola")')
        assert OpCode.OP_PRINT in bc

    def test_print_variable(self):
        bc, _, _, _, _ = parse_and_collect('variable x = 1\nimprimir(x)')
        assert OpCode.OP_PRINT in bc

    def test_print_expression(self):
        bc, _, _, _, _ = parse_and_collect('imprimir(1 + 2)')
        assert OpCode.OP_PRINT in bc
        assert OpCode.OP_ADD in bc


class TestParserArithmetic:
    def test_addition(self):
        bc, _, _, _, _ = parse_and_collect("variable x = 1 + 2")
        assert OpCode.OP_ADD in bc

    def test_subtraction(self):
        bc, _, _, _, _ = parse_and_collect("variable x = 5 - 3")
        assert OpCode.OP_SUB in bc

    def test_multiplication(self):
        bc, _, _, _, _ = parse_and_collect("variable x = 4 * 2")
        assert OpCode.OP_MUL in bc

    def test_division(self):
        bc, _, _, _, _ = parse_and_collect("variable x = 10 / 2")
        assert OpCode.OP_DIV in bc

    def test_modulo(self):
        bc, _, _, _, _ = parse_and_collect("variable x = 10 % 3")
        assert OpCode.OP_MOD in bc

    def test_complex_arithmetic(self):
        bc, _, _, _, _ = parse_and_collect("variable x = (1 + 2) * 3")
        assert OpCode.OP_ADD in bc
        assert OpCode.OP_MUL in bc


class TestParserComparison:
    def test_eq(self):
        bc, _, _, _, _ = parse_and_collect("variable x = 1 == 1")
        assert OpCode.OP_EQ in bc

    def test_neq(self):
        bc, _, _, _, _ = parse_and_collect("variable x = 1 != 2")
        assert OpCode.OP_NE in bc

    def test_gt(self):
        bc, _, _, _, _ = parse_and_collect("variable x = 5 > 3")
        assert OpCode.OP_GT in bc

    def test_lt(self):
        bc, _, _, _, _ = parse_and_collect("variable x = 3 < 5")
        assert OpCode.OP_LT in bc

    def test_gte(self):
        bc, _, _, _, _ = parse_and_collect("variable x = 5 >= 3")
        assert OpCode.OP_GTE in bc

    def test_lte(self):
        bc, _, _, _, _ = parse_and_collect("variable x = 3 <= 5")
        assert OpCode.OP_LTE in bc


class TestParserLogical:
    def test_and(self):
        bc, _, _, _, _ = parse_and_collect("variable x = verdadero y falso")
        assert OpCode.OP_AND in bc

    def test_or(self):
        bc, _, _, _, _ = parse_and_collect("variable x = verdadero o falso")
        assert OpCode.OP_OR in bc


class TestParserControlFlow:
    def test_if_statement(self):
        bc, _, _, _, _ = parse_and_collect("si 1 == 1 { imprimir(1) }")
        assert OpCode.OP_JUMP_IF_FALSE in bc

    def test_if_else(self):
        bc, _, _, _, _ = parse_and_collect(
            'si 1 == 1 { imprimir("si") } sino { imprimir("no") }'
        )
        assert OpCode.OP_JUMP_IF_FALSE in bc
        assert OpCode.OP_JUMP in bc

    def test_while_loop(self):
        bc, _, _, _, _ = parse_and_collect(
            "variable x = 0\nmientras x < 3 { x = x + 1 }"
        )
        assert OpCode.OP_JUMP_IF_FALSE in bc
        assert OpCode.OP_JUMP in bc

    def test_for_range(self):
        bc, _, _, _, _ = parse_and_collect(
            "para i de 1 a 3 { imprimir(i) }"
        )
        assert OpCode.OP_JUMP_IF_FALSE in bc
        assert OpCode.OP_JUMP in bc

    def test_for_each(self):
        bc, _, _, _, _ = parse_and_collect(
            "para cada item en [1, 2, 3] { imprimir(item) }"
        )
        assert OpCode.OP_LENGTH in bc
        assert OpCode.OP_LT in bc
        assert OpCode.OP_GET_INDEX in bc


class TestParserFunctions:
    def test_function_definition(self):
        bc, _, _, funcs, _ = parse_and_collect(
            "funcion saludar() { imprimir(1) }"
        )
        assert "saludar" in funcs

    def test_function_with_params(self):
        bc, _, _, funcs, _ = parse_and_collect(
            "funcion suma(p1, p2) { retornar p1 + p2 }"
        )
        assert "suma" in funcs
        assert funcs["suma"][1] == 2  # 2 params

    def test_function_call(self):
        bc, constants, _, funcs, _ = parse_and_collect(
            "funcion foo() { imprimir(1) }\nfoo()"
        )
        assert OpCode.OP_CALL in bc

    def test_return_statement(self):
        bc, _, _, _, _ = parse_and_collect(
            "funcion foo() { retornar 42 }"
        )
        assert OpCode.OP_RETURN in bc


class TestParserLists:
    def test_empty_list(self):
        bc, _, _, _, _ = parse_and_collect("variable x = []")
        assert OpCode.OP_LIST in bc

    def test_list_with_elements(self):
        bc, _, _, _, _ = parse_and_collect("variable x = [1, 2, 3]")
        assert OpCode.OP_LIST in bc

    def test_list_index_get(self):
        bc, _, _, _, _ = parse_and_collect(
            "variable x = [1, 2, 3]\nvariable val = x[0]"
        )
        assert OpCode.OP_GET_INDEX in bc


class TestParserDicts:
    def test_empty_dict(self):
        bc, _, _, _, _ = parse_and_collect("variable x = {}")
        assert OpCode.OP_DICT in bc

    def test_dict_with_pairs(self):
        bc, _, _, _, _ = parse_and_collect('variable x = {"a": 1, "b": 2}')
        assert OpCode.OP_DICT in bc


class TestParserClasses:
    def test_class_definition(self):
        bc, _, _, _, _ = parse_and_collect(
            "clase MiClase { variable x = 1 }"
        )
        assert OpCode.OP_CLASS in bc

    def test_class_with_constructor(self):
        bc, _, _, _, _ = parse_and_collect(
            "clase MiClase { funcion inicializar() { } }"
        )
        assert OpCode.OP_CLASS in bc

    def test_class_new(self):
        bc, _, _, _, _ = parse_and_collect(
            "clase MiClase { variable x = 1 }\nvariable obj = nuevo MiClase()"
        )
        assert OpCode.OP_NEW in bc


class TestParserTryCatch:
    def test_try_catch(self):
        bc, _, _, _, _ = parse_and_collect(
            "intentar { lanzar(1) } capturar { imprimir(1) }"
        )
        assert OpCode.OP_TRY_PUSH in bc
        assert OpCode.OP_THROW in bc
        assert OpCode.OP_TRY_POP in bc


class TestParserBuiltins:
    def test_leer(self):
        bc, _, _, _, _ = parse_and_collect("variable x = leer()")
        assert OpCode.OP_INPUT in bc

    def test_azar(self):
        bc, _, _, _, _ = parse_and_collect("variable x = azar(1, 10)")
        assert OpCode.OP_RANDOM in bc

    def test_longitud(self):
        bc, _, _, _, _ = parse_and_collect('variable x = longitud("hola")')
        assert OpCode.OP_LENGTH in bc

    def test_agregar(self):
        bc, _, _, _, _ = parse_and_collect("variable lista = []\nagregar(lista, 1)")
        assert OpCode.OP_APPEND in bc

    def test_tiempo(self):
        bc, _, _, _, _ = parse_and_collect("variable t = tiempo()")
        assert OpCode.OP_TIME in bc

    def test_tipo(self):
        bc, _, _, _, _ = parse_and_collect("variable t = tipo(42)")
        assert OpCode.OP_TYPE in bc

    def test_minusculas(self):
        bc, _, _, _, _ = parse_and_collect('variable r = minusculas("HOLA")')
        assert OpCode.OP_LOWER in bc

    def test_mayusculas(self):
        bc, _, _, _, _ = parse_and_collect('variable r = mayusculas("hola")')
        assert OpCode.OP_UPPER in bc

    def test_reemplazar(self):
        bc, _, _, _, _ = parse_and_collect(
            'variable r = reemplazar("hola", "h", "H")'
        )
        assert OpCode.OP_REPLACE in bc

    def test_absoluto(self):
        bc, _, _, _, _ = parse_and_collect("variable r = absoluto(0 - 5)")
        assert OpCode.OP_ABS in bc

    def test_redondear(self):
        bc, _, _, _, _ = parse_and_collect("variable r = redondear(3.7)")
        assert OpCode.OP_ROUND in bc

    def test_potencia(self):
        bc, _, _, _, _ = parse_and_collect("variable r = potencia(2, 3)")
        assert OpCode.OP_POW in bc

    def test_raiz(self):
        bc, _, _, _, _ = parse_and_collect("variable r = raiz(9)")
        assert OpCode.OP_SQRT in bc

    def test_json_codificar(self):
        bc, _, _, _, _ = parse_and_collect('variable r = json_codificar(1)')
        assert OpCode.OP_JSON_ENCODE in bc

    def test_json_decodificar(self):
        bc, _, _, _, _ = parse_and_collect('variable r = json_decodificar("{}")')
        assert OpCode.OP_JSON_DECODE in bc

    def test_error_msj(self):
        bc, _, _, _, _ = parse_and_collect("variable r = error_msj()")
        assert OpCode.OP_ERROR_MSG in bc


class TestParserErrors:
    def test_undefined_variable(self):
        with pytest.raises(RuntimeError, match="no existe"):
            parse_and_collect("imprimir(x)")

    def test_undefined_function(self):
        with pytest.raises(RuntimeError, match="no existe"):
            parse_and_collect("foo()")

    def test_syntax_error_assignment(self):
        with pytest.raises(RuntimeError):
            parse_and_collect("variable = 1")

    def test_argument_mismatch(self):
        with pytest.raises(RuntimeError, match="argumentos"):
            parse_and_collect(
                "funcion foo(p1) { }\nfoo(1, 2)"
            )

    def test_reassignment_creates_var(self):
        bc, constants, _, _, parser = parse_and_collect("x = 42")
        assert OpCode.OP_STORE_GLOBAL in bc or OpCode.OP_STORE in bc


class TestParserNewFeatures:
    def test_unary_minus_number(self):
        bc, constants, _, _, _ = parse_and_collect("variable x = -5")
        assert OpCode.OP_NEGATE in bc
        assert 5 in constants

    def test_unary_minus_expr(self):
        bc, constants, _, _, _ = parse_and_collect("variable x = -(3 + 4)")
        assert OpCode.OP_NEGATE in bc
        assert OpCode.OP_ADD in bc

    def test_compound_add(self):
        bc, _, _, _, _ = parse_and_collect("variable x = 1\nx += 2")
        assert OpCode.OP_ADD in bc

    def test_compound_sub(self):
        bc, _, _, _, _ = parse_and_collect("variable x = 5\nx -= 3")
        assert OpCode.OP_SUB in bc

    def test_compound_mul(self):
        bc, _, _, _, _ = parse_and_collect("variable x = 2\nx *= 3")
        assert OpCode.OP_MUL in bc

    def test_compound_div(self):
        bc, _, _, _, _ = parse_and_collect("variable x = 6\nx /= 2")
        assert OpCode.OP_DIV in bc

    def test_compound_mod(self):
        bc, _, _, _, _ = parse_and_collect("variable x = 7\nx %= 3")
        assert OpCode.OP_MOD in bc

    def test_break_outside_loop(self):
        with pytest.raises(RuntimeError, match="bucle"):
            parse_and_collect("romper")

    def test_continue_outside_loop(self):
        with pytest.raises(RuntimeError, match="bucle"):
            parse_and_collect("continuar")

    def test_while_with_break(self):
        bc, _, _, _, _ = parse_and_collect(
            "variable x = 0\nmientras x < 5 { si x == 3 { romper } x = x + 1 }"
        )
        assert OpCode.OP_JUMP in bc
        assert OpCode.OP_JUMP_IF_FALSE in bc

    def test_for_with_continue(self):
        bc, _, _, _, _ = parse_and_collect(
            "para i de 1 a 5 { si i == 3 { continuar } imprimir(i) }"
        )
        assert OpCode.OP_JUMP in bc

    def test_string_triple(self):
        bc, constants, _, _, _ = parse_and_collect('variable x = """hola"""')
        assert "hola" in constants

    def test_function_as_value(self):
        bc, constants, _, funcs, parser = parse_and_collect(
            "funcion foo() { }"
        )
        assert OpCode.OP_MAKE_FUNC in bc

    def test_list_comprehension_parse(self):
        bc, _, _, _, _ = parse_and_collect(
            "variable r = [x * 2 para cada x en [1, 2, 3]]"
        )
        assert OpCode.OP_LIST in bc
        assert OpCode.OP_APPEND in bc

    def test_async_function_definition(self):
        bc, _, _, funcs, _ = parse_and_collect(
            "funcion async foo(n) { retornar n * 2 }"
        )
        assert "foo" in funcs
        assert len(funcs["foo"]) >= 4
        assert funcs["foo"][3] is True

    def test_async_function_call_opcode(self):
        bc, _, _, funcs, _ = parse_and_collect(
            "funcion async foo(n) { retornar n + 1 }\nfoo(5)"
        )
        assert OpCode.OP_ASYNC_CALL in bc
        assert OpCode.OP_CALL not in bc

    def test_regular_function_call_opcode(self):
        bc, _, _, _, _ = parse_and_collect(
            "funcion bar() { imprimir(1) }\nbar()"
        )
        assert OpCode.OP_CALL in bc
        assert OpCode.OP_ASYNC_CALL not in bc

    def test_aguardar_expression(self):
        bc, _, _, _, _ = parse_and_collect(
            "funcion async foo() { retornar 42 }\nvariable x = aguardar foo()"
        )
        assert OpCode.OP_AWAIT in bc

    def test_aguardar_statement(self):
        bc, _, _, _, _ = parse_and_collect(
            "funcion async foo() { retornar 42 }\naguardar foo()"
        )
        assert OpCode.OP_AWAIT in bc
