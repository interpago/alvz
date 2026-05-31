"""Test: compilar Alvz a WASM y ejecutar con wasmtime."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
pytest.importorskip("wasmtime")

from alvz.core.lexer import Lexer
from alvz.core.parser import Parser
from alvz.core.wasm_compiler import WasmCompiler


def _compile_and_wasm(code):
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    bytecode, constants, line_map, functions = parser.compile()
    compiler = WasmCompiler(bytecode, constants, functions, line_map)
    return compiler.compile()


def test_wasm_suma_imprimir():
    codigo = """variable x = 2 + 3\nimprimir(x)"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert len(wasm_bytes) > 0
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_constante():
    codigo = """imprimir(42)"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_resta():
    codigo = """imprimir(10 - 3)"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_multiplicacion():
    codigo = """imprimir(4 * 5)"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_division():
    codigo = """imprimir(20 / 4)"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_null():
    codigo = """variable x = nulo\nimprimir(x)"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_booleano():
    codigo = """imprimir(verdadero)\nimprimir(falso)"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_and():
    codigo = """si verdadero y falso { imprimir(1) }"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_or():
    codigo = """si falso o verdadero { imprimir(1) }"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_and_con_numeros():
    codigo = """si 1 y 0 { imprimir(1) }"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_random():
    codigo = """imprimir(azar(1, 10))"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_input():
    codigo = """variable x = leer()\nimprimir(x)"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_string():
    codigo = """imprimir("hola mundo")"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_string_variable():
    codigo = """variable nombre = "Alvz"\nimprimir(nombre)"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_lista_crear():
    codigo = """variable x = []"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_lista_agregar():
    codigo = """variable x = []\nagregar(x, 42)\nimprimir(longitud(x))"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_lista_indice():
    codigo = """variable x = [10, 20, 30]\nimprimir(x[1])"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_lista_asignar_indice():
    codigo = """variable x = [1, 2, 3]\nx[1] = 99\nimprimir(x[1])"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_lista_longitud():
    codigo = """variable x = [1, 2, 3, 4, 5]\nimprimir(longitud(x))"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_diccionario():
    codigo = """variable d = {}\nimprimir(d)"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_funcion_simple():
    codigo = """funcion suma(a, b) {\n  retornar a + b\n}\nimprimir(suma(2, 3))"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_funcion_sin_retorno():
    codigo = """funcion saludar() {\n  imprimir("hola")\n}\nsaludar()"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_negacion():
    codigo = """imprimir(-5)"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_comparacion_encadenada():
    codigo = """imprimir(1 < 2 y 2 < 3)"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_lista_vacia_longitud():
    codigo = """imprimir(longitud([]))"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_modulo():
    codigo = """imprimir(10 % 3)"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_jump_if_true():
    """OP_JUMP_IF_TRUE con si-sino (condicion negada -> OP_JUMP_IF_FALSE, sino -> OP_JUMP)"""
    codigo = """si 1 < 2 { imprimir(1) } sino { imprimir(2) }"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_make_func():
    codigo = """funcion suma(a, b) { retornar a + b }\nvariable f = suma\nimprimir(f(2, 3))"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_slice_lista():
    codigo = """variable x = [1, 2, 3, 4, 5]\nimprimir(x[1:4])"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_dict_keys():
    codigo = """variable d = {"a": 1}
cada k en d {
    imprimir(k)
}"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_clear():
    codigo = """limpiar()"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_wait():
    codigo = """esperar(1)"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_web_send():
    codigo = """enviar_web("url", {})"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_write_file():
    codigo = """escribir_archivo("test.txt", "hola")"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_read_file():
    codigo = """variable c = leer_archivo("test.txt")"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_lower():
    codigo = """imprimir(minusculas("HOLA"))"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_upper():
    codigo = """imprimir(mayusculas("hola"))"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_get_output():
    codigo = """variable s = obtener_salida()"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_supabase_insert():
    codigo = """supabase_insertar("url", "key", "tabla", {"dato": 1})"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_supabase_select():
    codigo = """supabase_consultar("url", "key", "tabla")"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_round():
    codigo = """imprimir(redondear(3.7))"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_pow():
    codigo = """imprimir(potencia(2, 3))"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_sqrt():
    codigo = """imprimir(raiz(9))"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_abs():
    codigo = """imprimir(absoluto(-5))"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_try_except():
    codigo = """intentar { imprimir(1) } capturar { imprimir(2) }"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_error_msg():
    codigo = """variable e = error_msj()"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_class_new():
    codigo = """clase MiClase { funcion inicializar() { } }\nvariable obj = nuevo MiClase()"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_get_set_attr():
    codigo = """variable d = {"x": 10}\nimprimir(d.x)\nd.x = 20"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_super_attr():
    codigo = """clase Padre { funcion saludar() { retornar "hola" } }\nclase Hijo de Padre { funcion test() { retornar super.saludar() } }"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_instanceof():
    codigo = """clase MiClase { }\nvariable obj = nuevo MiClase()\nimprimir(obj instancia MiClase)"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_json_encode_decode():
    codigo = """variable j = json_codificar({"a": 1})\nvariable d = json_decodificar(j)"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_import():
    codigo = """importar "math" """
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_time():
    codigo = """variable t = tiempo()"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_type():
    codigo = """imprimir(tipo(42))"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_replace():
    codigo = """imprimir(reemplazar("hola mundo", "mundo", "amigo"))"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_input_num():
    codigo = """variable n = leer_numero()"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_start_server():
    codigo = """iniciar_servidor(8080, {})"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_date_format():
    codigo = """variable f = fecha_actual("%Y-%m-%d")"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_string_split():
    codigo = """variable l = dividir("a,b,c", ",")"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_string_join():
    codigo = """variable s = unir(["a", "b"], ",")"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_to_number():
    codigo = """variable n = a_numero("42")"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_regex_search():
    codigo = """variable r = regex_buscar("abc123", "\\\\d+")"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_async_await():
    codigo = """funcion async test() { retornar 1 }\nvariable c = test()\nvariable r = aguardar(c)"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_solicitud_http():
    codigo = """variable r = solicitud_http("GET", "url", {})"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_sqlite_abrir():
    codigo = """variable conn = sqlite_abrir("test.db")"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_sqlite_ejecutar():
    codigo = """variable conn = sqlite_abrir("test.db")\nsqlite_ejecutar(conn, "CREATE TABLE t (id INT)")"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_sqlite_consultar():
    codigo = """variable conn = sqlite_abrir("test.db")\nvariable r = sqlite_consultar(conn, "SELECT * FROM t")"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_global_var():
    codigo = """variable x = 5\nfuncion test() {\n  global x\n  x = 10\n}\ntest()\nimprimir(x)"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_global_fn():
    codigo = """funcion test() {\n  global x\n  x = 10\n}\nx = 5\ntest()\nimprimir(x)"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_while():
    codigo = """variable i = 0\nmientras i < 3 {\n  imprimir(i)\n  i = i + 1\n}"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_for():
    codigo = """para i de 0 a 3 {\n  imprimir(i)\n}"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_break():
    codigo = """para i de 0 a 10 {\n  si i == 2 { romper }\n  imprimir(i)\n}"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


def test_wasm_negation():
    codigo = """imprimir(-5)"""
    wasm_bytes = _compile_and_wasm(codigo)
    assert wasm_bytes[:4] == b'\x00asm'


@pytest.mark.skipif('wasmtime' not in sys.modules, reason="wasmtime no instalado")
def test_wasm_execute_suma(tmp_path):
    """Compila y ejecuta WASM, verifica salida numerica."""
    codigo = """imprimir(2 + 3)"""
    wasm_bytes = _compile_and_wasm(codigo)
    wasm_path = tmp_path / "test.wasm"
    wasm_path.write_bytes(wasm_bytes)

    from alvz.core.wasm_runtime import run
    output = []
    result = run(str(wasm_path), output_buffer=output)
    assert result is True
    assert any("5" in s for s in output)


@pytest.mark.skipif('wasmtime' not in sys.modules, reason="wasmtime no instalado")
def test_wasm_execute_list(tmp_path):
    """Compila y ejecuta WASM con listas, verifica output."""
    codigo = """variable x = [10, 20, 30]\nimprimir(longitud(x))"""
    wasm_bytes = _compile_and_wasm(codigo)
    wasm_path = tmp_path / "test_list.wasm"
    wasm_path.write_bytes(wasm_bytes)

    from alvz.core.wasm_runtime import run
    output = []
    result = run(str(wasm_path), output_buffer=output)
    assert result is True
    assert len(output) >= 1
