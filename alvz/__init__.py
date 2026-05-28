"""Alvz Language - Un lenguaje de programacion con sintaxis en espanol."""

from .core.lexer import Lexer as __Lexer
from .core.parser import Parser as __Parser
from .core.vm import VM as __VM
from .repl import repl, main

def ejecutar(archivo):
    """Ejecuta un archivo .alvz."""
    with open(archivo, "r", encoding="utf-8-sig") as f:
        codigo = f.read()
    lexer = __Lexer(codigo)
    tokens = lexer.tokenize()
    parser = __Parser(tokens)
    bytecode, constants, line_map, funcs = parser.compile()
    vm = __VM(bytecode, constants, line_map, funcs)
    vm.run()

def leer_linea(linea):
    """Compila y ejecuta una linea de codigo Alvz."""
    lexer = __Lexer(linea)
    tokens = lexer.tokenize()
    parser = __Parser(tokens)
    bytecode, constants, line_map, funcs = parser.compile()
    vm = __VM(bytecode, constants, line_map, funcs)
    vm.run()

__all__ = ['ejecutar', 'leer_linea', 'repl', 'main']
