import pytest
from alvz.core.lexer import Lexer, Token


class TestTokenize:
    def test_empty_code(self, tokenize):
        tokens = tokenize("")
        assert len(tokens) == 1
        assert tokens[0][0] == Token.EOF

    def test_only_whitespace(self, tokenize):
        tokens = tokenize("   \t  ")
        assert len(tokens) == 1
        assert tokens[0][0] == Token.EOF

    def test_only_comment(self, tokenize):
        tokens = tokenize("# esto es un comentario")
        assert len(tokens) == 1
        assert tokens[0][0] == Token.EOF

    def test_number_integer(self, tokenize):
        tokens = tokenize("42")
        assert len(tokens) == 2
        assert tokens[0][0] == Token.NUMERO
        assert tokens[0][1] == 42

    def test_number_float(self, tokenize):
        tokens = tokenize("3.14")
        assert len(tokens) == 2
        assert tokens[0][0] == Token.NUMERO
        assert tokens[0][1] == 3.14

    def test_string_double_quotes(self, tokenize):
        tokens = tokenize('"hola mundo"')
        assert len(tokens) == 2
        assert tokens[0][0] == Token.STRING
        assert tokens[0][1] == "hola mundo"

    def test_string_single_quotes(self, tokenize):
        tokens = tokenize("'hola mundo'")
        assert len(tokens) == 2
        assert tokens[0][0] == Token.STRING
        assert tokens[0][1] == "hola mundo"

    def test_keyword_variable(self, tokenize):
        tokens = tokenize("variable")
        assert tokens[0][0] == Token.VARIABLE

    def test_keyword_imprimir(self, tokenize):
        tokens = tokenize("imprimir")
        assert tokens[0][0] == Token.IMPRIMIR

    def test_keyword_si(self, tokenize):
        tokens = tokenize("si")
        assert tokens[0][0] == Token.SI

    def test_keyword_sino(self, tokenize):
        tokens = tokenize("sino")
        assert tokens[0][0] == Token.SINO

    def test_keyword_mientras(self, tokenize):
        tokens = tokenize("mientras")
        assert tokens[0][0] == Token.MIENTRAS

    def test_keyword_funcion(self, tokenize):
        tokens = tokenize("funcion")
        assert tokens[0][0] == Token.FUNCION

    def test_keyword_retornar(self, tokenize):
        tokens = tokenize("retornar")
        assert tokens[0][0] == Token.RETORNAR

    def test_keyword_verdadero(self, tokenize):
        tokens = tokenize("verdadero")
        assert tokens[0][0] == Token.VERDADERO

    def test_keyword_falso(self, tokenize):
        tokens = tokenize("falso")
        assert tokens[0][0] == Token.FALSO

    def test_keyword_nulo(self, tokenize):
        tokens = tokenize("nulo")
        assert tokens[0][0] == Token.NULO

    def test_keyword_para(self, tokenize):
        tokens = tokenize("para")
        assert tokens[0][0] == Token.PARA

    def test_keyword_cada(self, tokenize):
        tokens = tokenize("cada")
        assert tokens[0][0] == Token.CADA

    def test_keyword_en(self, tokenize):
        tokens = tokenize("en")
        assert tokens[0][0] == Token.EN

    def test_keyword_de(self, tokenize):
        tokens = tokenize("de")
        assert tokens[0][0] == Token.DE

    def test_keyword_clase(self, tokenize):
        tokens = tokenize("clase")
        assert tokens[0][0] == Token.CLASE

    def test_keyword_nuevo(self, tokenize):
        tokens = tokenize("nuevo")
        assert tokens[0][0] == Token.NUEVO

    def test_identifier(self, tokenize):
        tokens = tokenize("miVariable")
        assert tokens[0][0] == Token.IDENTIFICADOR
        assert tokens[0][1] == "miVariable"

    def test_assignment(self, tokenize):
        tokens = tokenize("=")
        assert tokens[0][0] == Token.ASIGNACION

    def test_operators(self, tokenize):
        code = "+ - * / % == != > < >= <="
        tokens = tokenize(code)
        expected = [
            Token.MAS, Token.MENOS, Token.POR, Token.ENTRE, Token.MODULO,
            Token.IGUAL_IGUAL, Token.DIFERENTE, Token.MAYOR, Token.MENOR,
            Token.MAYOR_IGUAL, Token.MENOR_IGUAL, Token.EOF,
        ]
        assert [t[0] for t in tokens] == expected

    def test_parentheses(self, tokenize):
        tokens = tokenize("()")
        assert tokens[0][0] == Token.PAREN_IZQ
        assert tokens[1][0] == Token.PAREN_DER

    def test_braces(self, tokenize):
        tokens = tokenize("{}")
        assert tokens[0][0] == Token.LLAVE_IZQ
        assert tokens[1][0] == Token.LLAVE_DER

    def test_brackets(self, tokenize):
        tokens = tokenize("[]")
        assert tokens[0][0] == Token.CORCHETE_IZQ
        assert tokens[1][0] == Token.CORCHETE_DER

    def test_comma(self, tokenize):
        tokens = tokenize(",")
        assert tokens[0][0] == Token.COMA

    def test_dot(self, tokenize):
        tokens = tokenize(".")
        assert tokens[0][0] == Token.PUNTO

    def test_colon(self, tokenize):
        tokens = tokenize(":")
        assert tokens[0][0] == Token.DOS_PUNTOS

    def test_keyword_y(self, tokenize):
        tokens = tokenize("y")
        assert tokens[0][0] == Token.Y

    def test_keyword_o(self, tokenize):
        tokens = tokenize("o")
        assert tokens[0][0] == Token.O

    def test_keyword_importar(self, tokenize):
        tokens = tokenize("importar")
        assert tokens[0][0] == Token.IMPORTAR

    def test_keyword_intentar(self, tokenize):
        tokens = tokenize("intentar")
        assert tokens[0][0] == Token.INTENTAR

    def test_keyword_capturar(self, tokenize):
        tokens = tokenize("capturar")
        assert tokens[0][0] == Token.CAPTURAR

    def test_keyword_leer(self, tokenize):
        tokens = tokenize("leer()")
        assert tokens[0][0] == Token.LEER

    def test_keyword_leer_numero(self, tokenize):
        tokens = tokenize("leer_numero()")
        assert tokens[0][0] == Token.LEER_NUMERO

    def test_keyword_azar(self, tokenize):
        tokens = tokenize("azar")
        assert tokens[0][0] == Token.AZAR

    def test_keyword_longitud(self, tokenize):
        tokens = tokenize("longitud")
        assert tokens[0][0] == Token.LONGITUD

    def test_keyword_agregar(self, tokenize):
        tokens = tokenize("agregar")
        assert tokens[0][0] == Token.AGREGAR

    def test_keyword_limpiar(self, tokenize):
        tokens = tokenize("limpiar")
        assert tokens[0][0] == Token.LIMPIAR

    def test_keyword_esperar(self, tokenize):
        tokens = tokenize("esperar")
        assert tokens[0][0] == Token.ESPERAR

    def test_variable_assignment(self, tokenize):
        code = 'variable x = 10'
        tokens = tokenize(code)
        types = [t[0] for t in tokens]
        assert types == [Token.VARIABLE, Token.IDENTIFICADOR, Token.ASIGNACION, Token.NUMERO, Token.EOF]
        assert tokens[1][1] == "x"
        assert tokens[3][1] == 10

    def test_print_statement(self, tokenize):
        code = 'imprimir("hola")'
        tokens = tokenize(code)
        types = [t[0] for t in tokens]
        assert types == [Token.IMPRIMIR, Token.PAREN_IZQ, Token.STRING, Token.PAREN_DER, Token.EOF]
        assert tokens[2][1] == "hola"

    def test_si_expression(self, tokenize):
        code = 'si x == 5 {}'
        tokens = tokenize(code)
        types = [t[0] for t in tokens]
        assert types[:3] == [Token.SI, Token.IDENTIFICADOR, Token.IGUAL_IGUAL]

    def test_mientras_loop(self, tokenize):
        code = 'mientras x < 10 { x = x + 1 }'
        tokens = tokenize(code)
        types = [t[0] for t in tokens]
        assert types[0] == Token.MIENTRAS

    def test_function_definition(self, tokenize):
        code = 'funcion suma(a, b) { retornar a + b }'
        tokens = tokenize(code)
        types = [t[0] for t in tokens]
        assert types[0] == Token.FUNCION
        assert types[1] == Token.IDENTIFICADOR
        assert tokens[1][1] == "suma"
        assert types[2] == Token.PAREN_IZQ

    def test_newline_handling(self, tokenize):
        code = "variable x = 1\nvariable y_val = 2"
        tokens = tokenize(code)
        assert len(tokens) >= 7
        assert tokens[3][0] == Token.NUMERO
        assert tokens[4][0] == Token.VARIABLE

    def test_comment_ignored(self, tokenize):
        code = "variable x = 1 # esto es un comentario\nvariable y_val = 2"
        tokens = tokenize(code)
        assert len(tokens) >= 7

    def test_multiple_keywords(self, tokenize):
        code = "si mientras para funcion retornar clase"
        tokens = tokenize(code)
        types = [t[0] for t in tokens]
        assert types[:-1] == [
            Token.SI, Token.MIENTRAS, Token.PARA,
            Token.FUNCION, Token.RETORNAR, Token.CLASE,
        ]

    def test_builtin_functions(self, tokenize):
        code = "tipo() tiempo() redondear() potencia() raiz() absoluto()"
        tokens = tokenize(code)
        types = [t[0] for t in tokens]
        assert Token.TIPO_KW in types
        assert Token.TIEMPO in types
        assert Token.REDONDEAR in types
        assert Token.POTENCIA in types
        assert Token.RAIZ in types
        assert Token.ABSOLUTO in types

    def test_string_functions(self, tokenize):
        code = "minusculas() mayusculas() reemplazar() longitud()"
        tokens = tokenize(code)
        types = [t[0] for t in tokens]
        assert Token.MINUSCULAS in types
        assert Token.MAYUSCULAS in types
        assert Token.REEMPLAZAR in types
        assert Token.LONGITUD in types

    def test_io_functions(self, tokenize):
        code = "escribir_archivo() leer_archivo() enviar_web() obtener_salida()"
        tokens = tokenize(code)
        types = [t[0] for t in tokens]
        assert Token.ESCRIBIR_ARCHIVO in types
        assert Token.LEER_ARCHIVO in types
        assert Token.ENVIAR_WEB in types
        assert Token.OBTENER_SALIDA in types

    def test_supabase_functions(self, tokenize):
        code = "supabase_insertar() supabase_consultar()"
        tokens = tokenize(code)
        types = [t[0] for t in tokens]
        assert Token.SUPABASE_INSERTAR in types
        assert Token.SUPABASE_CONSULTAR in types

    def test_json_functions(self, tokenize):
        code = "json_codificar() json_decodificar()"
        tokens = tokenize(code)
        types = [t[0] for t in tokens]
        assert Token.JSON_CODIFICAR in types
        assert Token.JSON_DECODIFICAR in types

    def test_error_msj(self, tokenize):
        tokens = tokenize("error_msj()")
        assert tokens[0][0] == Token.ERROR_MSJ

    def test_iniciar_servidor(self, tokenize):
        tokens = tokenize("iniciar_servidor()")
        assert tokens[0][0] == Token.INICIAR_SERVIDOR

    def test_error_on_unknown_token(self, tokenize):
        with pytest.raises(RuntimeError, match="Error lexico"):
            tokenize("@")

    def test_suggestion_on_typo(self, tokenize):
        with pytest.raises(RuntimeError, match="Error lexico"):
            tokenize("@typo")

    def test_complex_expression(self, tokenize):
        code = '(10 + 20) * 3 - 5 / 2'
        tokens = tokenize(code)
        types = [t[0] for t in tokens]
        expected = [
            Token.PAREN_IZQ, Token.NUMERO, Token.MAS, Token.NUMERO,
            Token.PAREN_DER, Token.POR, Token.NUMERO, Token.MENOS,
            Token.NUMERO, Token.ENTRE, Token.NUMERO, Token.EOF,
        ]
        assert types == expected

    def test_list_literal(self, tokenize):
        code = '[1, 2, 3]'
        tokens = tokenize(code)
        types = [t[0] for t in tokens]
        assert types[:2] == [Token.CORCHETE_IZQ, Token.NUMERO]
        assert Token.CORCHETE_DER in types

    def test_dict_literal(self, tokenize):
        code = '{"clave": "valor"}'
        tokens = tokenize(code)
        types = [t[0] for t in tokens]
        assert types[:2] == [Token.LLAVE_IZQ, Token.STRING]
        assert Token.DOS_PUNTOS in types

    def test_iniciar_servidor_keyword(self, tokenize):
        tokens = tokenize("iniciar_servidor")
        assert tokens[0][0] == Token.INICIAR_SERVIDOR

    def test_with_multiple_lines(self, tokenize):
        code = """variable a = 1
variable b = 2
imprimir(a + b)"""
        tokens = tokenize(code)
        assert tokens[-2][0] != Token.EOF  # penultimo debe ser PAREN_DER
        # check EOF is last
        assert tokens[-1][0] == Token.EOF

    def test_keywords_inside_identifiers(self, tokenize):
        tokens = tokenize("variable variable")
        assert tokens[0][0] == Token.VARIABLE
        assert tokens[1][0] == Token.VARIABLE


class TestTokenizeNewFeatures:
    def test_compound_add(self, tokenize):
        tokens = tokenize("x += 1")
        types = [t[0] for t in tokens]
        assert types[:2] == [Token.IDENTIFICADOR, Token.MAS_IGUAL]

    def test_compound_sub(self, tokenize):
        tokens = tokenize("x -= 1")
        assert tokens[1][0] == Token.MENOS_IGUAL

    def test_compound_mul(self, tokenize):
        tokens = tokenize("x *= 2")
        assert tokens[1][0] == Token.POR_IGUAL

    def test_compound_div(self, tokenize):
        tokens = tokenize("x /= 2")
        assert tokens[1][0] == Token.ENTRE_IGUAL

    def test_compound_mod(self, tokenize):
        tokens = tokenize("x %= 2")
        assert tokens[1][0] == Token.MOD_IGUAL

    def test_romper(self, tokenize):
        tokens = tokenize("romper")
        assert tokens[0][0] == Token.ROMPER

    def test_continuar(self, tokenize):
        tokens = tokenize("continuar")
        assert tokens[0][0] == Token.CONTINUAR

    def test_string_triple_double(self, tokenize):
        tokens = tokenize('"""hola mundo"""')
        assert tokens[0][0] == Token.STRING_TRIPLE
        assert tokens[0][1] == "hola mundo"

    def test_string_triple_single(self, tokenize):
        tokens = tokenize("'''hola mundo'''")
        assert tokens[0][0] == Token.STRING_TRIPLE
        assert tokens[0][1] == "hola mundo"

    def test_string_triple_multiline(self, tokenize):
        tokens = tokenize('"""linea1\nlinea2"""')
        assert tokens[0][0] == Token.STRING_TRIPLE
        assert "linea1" in tokens[0][1]

    def test_async_keyword(self, tokenize):
        tokens = tokenize("async")
        assert tokens[0][0] == Token.ASYNC

    def test_aguardar_keyword(self, tokenize):
        tokens = tokenize("aguardar")
        assert tokens[0][0] == Token.AGUARDAR
