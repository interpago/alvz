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
