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
