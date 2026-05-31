"""Tests for the 5 new StdLib modules: aleatorio, csv, expresiones_regulares, consola, json."""

from alvz.core.lexer import Lexer
from alvz.core.parser import Parser
from alvz.core.vm import VM
import json


def run_code(code):
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    bytecode, constants, line_map, funcs = parser.compile()
    vm = VM(bytecode, constants, line_map, funcs)
    vm.run()
    return vm


def run_and_get(code):
    return "\n".join(run_code(code).output_buffer)


class TestAleatorio:
    def test_aleatorio_numero(self):
        code = '''
importar "aleatorio"
variable n = aleatorio_numero(1, 10)
imprimir(n)
'''
        result = int(run_and_get(code))
        assert 1 <= result <= 10

    def test_aleatorio_escoger(self):
        code = '''
importar "aleatorio"
variable lista = [10, 20, 30]
variable e = aleatorio_escoger(lista)
imprimir(e)
'''
        result = int(run_and_get(code))
        assert result in [10, 20, 30]

    def test_aleatorio_booleano(self):
        code = '''
importar "aleatorio"
variable b = aleatorio_booleano()
imprimir(b)
'''
        result = run_and_get(code)
        assert result in ["True", "False"]

    def test_aleatorio_cadena(self):
        code = '''
importar "aleatorio"
variable s = aleatorio_cadena(8)
imprimir(longitud(s))
'''
        result = int(run_and_get(code))
        assert result == 8

    def test_aleatorio_mezclar(self):
        code = '''
importar "aleatorio"
variable original = [1, 2, 3, 4, 5]
variable mezclada = aleatorio_mezclar(original)
imprimir(longitud(original))
imprimir(longitud(mezclada))
'''
        result = run_and_get(code).split("\n")
        assert int(result[0]) == 5
        assert int(result[1]) == 5

    def test_aleatorio_flotante(self):
        code = '''
importar "aleatorio"
variable f = aleatorio_flotante(0, 1)
imprimir(f)
'''
        result = float(run_and_get(code))
        assert 0 <= result <= 1

    def test_aleatorio_escoger_varios(self):
        code = '''
importar "aleatorio"
variable lista = [1, 2, 3, 4, 5]
variable r = aleatorio_escoger_varios(lista, 3)
imprimir(longitud(r))
'''
        result = int(run_and_get(code))
        assert result == 3


class TestCSV:
    def test_csv_a_listas(self):
        code = '''
importar "csv"
variable texto = "a,b,c\\n1,2,3\\n4,5,6"
variable datos = csv_a_listas(texto)
imprimir(longitud(datos))
imprimir(datos[0][0])
'''
        result = run_and_get(code).split("\n")
        assert int(result[0]) == 3
        assert result[1] == "a"

    def test_csv_a_diccionarios(self):
        code = '''
importar "csv"
variable texto = "nombre,edad\\nAlice,30\\nBob,25"
variable datos = csv_a_diccionarios(texto)
imprimir(longitud(datos))
imprimir(datos[0]["nombre"])
'''
        result = run_and_get(code).split("\n")
        assert int(result[0]) == 2
        assert result[1] == "Alice"

    def test_csv_diccionarios_a_texto(self):
        code = '''
importar "csv"
variable datos = [{"nombre": "Alice", "edad": "30"}, {"nombre": "Bob", "edad": "25"}]
variable texto = csv_diccionarios_a_texto(datos)
imprimir(texto)
'''
        result = run_and_get(code)
        assert "Alice" in result
        assert "Bob" in result

    def test_csv_leer_archivo(self):
        import tempfile
        import os
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        tmp.write("x,y\\n1,2\\n3,4")
        tmp.close()
        code = '''
importar "csv"
variable datos = csv_leer("''' + tmp.name.replace("\\", "\\\\") + '''")
imprimir(longitud(datos))
imprimir(datos[0]["x"])
'''
        result = run_and_get(code).split("\n")
        assert int(result[0]) == 2
        assert result[1] == "1"
        os.unlink(tmp.name)

    def test_csv_listas_a_texto(self):
        code = '''
importar "csv"
variable datos = [["a", "b"], ["1", "2"]]
variable texto = csv_listas_a_texto(datos)
imprimir(texto)
'''
        result = run_and_get(code)
        assert "a,b" in result


class TestExpresionesRegulares:
    def test_regex_coincide(self):
        code = '''
importar "expresiones_regulares"
variable ok = regex_coincide("hola123", "\\d+")
imprimir(ok)
'''
        result = run_and_get(code)
        assert result == "True"

    def test_regex_no_coincide(self):
        code = '''
importar "expresiones_regulares"
variable ok = regex_coincide("hola", "\\d+")
imprimir(ok)
'''
        result = run_and_get(code)
        assert result == "False"

    def test_regex_extraer(self):
        code = '''
importar "expresiones_regulares"
variable m = regex_extraer("abc123def", "\\d+")
imprimir(m)
'''
        result = run_and_get(code)
        assert result == "123"

    def test_regex_contar(self):
        code = '''
importar "expresiones_regulares"
variable n = regex_contar("a1b2c3d4", "\\d")
imprimir(n)
'''
        result = int(run_and_get(code))
        assert result == 4


class TestConsola:
    def test_consola_color(self):
        code = '''
importar "consola"
variable c = consola_color("Hola", "rojo")
imprimir(c)
'''
        result = run_and_get(code)
        assert "\x1b[31m" in result
        assert "\x1b[0m" in result

    def test_consola_separador(self):
        code = '''
importar "consola"
consola_separador()
'''
        result = run_and_get(code)
        assert "---" in result

    def test_consola_titulo(self):
        code = '''
importar "consola"
consola_titulo("Prueba")
'''
        result = run_and_get(code)
        assert "Prueba" in result


class TestJSON:
    def test_json_a_texto(self):
        code = '''
importar "json"
variable t = json_a_texto({"a": 1, "b": 2})
imprimir(t)
'''
        result = run_and_get(code)
        data = json.loads(result)
        assert data == {"a": 1, "b": 2}

    def test_texto_a_json(self):
        code = '''
importar "json"
variable d = texto_a_json('{"x": 10}')
imprimir(d["x"])
'''
        result = int(run_and_get(code))
        assert result == 10

    def test_json_valido(self):
        code = '''
importar "json"
variable ok = json_valido('{"a": 1}')
variable no_ok = json_valido("no valido")
imprimir(ok)
imprimir(no_ok)
'''
        result = run_and_get(code).split("\n")
        assert result[0] == "True"
        assert result[1] == "False"

    def test_json_leer_archivo(self):
        import tempfile
        import os
        import json as pyjson
        data = {"nombre": "Alice", "edad": 30}
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        pyjson.dump(data, tmp)
        tmp.close()
        code = '''
importar "json"
variable d = json_leer_archivo("''' + tmp.name.replace("\\", "\\\\") + '''")
imprimir(d["nombre"])
imprimir(d["edad"])
'''
        result = run_and_get(code).split("\n")
        assert result[0] == "Alice"
        assert int(result[1]) == 30
        os.unlink(tmp.name)
