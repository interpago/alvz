import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from alvz.core.lexer import Lexer, Token
from alvz.core.parser import Parser
from alvz.core.vm import VM


@pytest.fixture
def lexer():
    def _lexer(code):
        return Lexer(code)
    return _lexer


@pytest.fixture
def tokenize():
    def _tokenize(code):
        lexer = Lexer(code)
        return lexer.tokenize()
    return _tokenize


@pytest.fixture
def compile_code():
    def _compile(code):
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        bytecode, constants, line_map, funcs = parser.compile()
        return bytecode, constants, line_map, funcs, parser
    return _compile


@pytest.fixture
def execute():
    def _execute(code):
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        bytecode, constants, line_map, funcs = parser.compile()
        vm = VM(bytecode, constants, line_map, funcs)
        vm.run()
        return vm
    return _execute


@pytest.fixture
def vm():
    def _vm(bytecode=None, constants=None, line_map=None, funcs=None):
        return VM(bytecode or [], constants or [], line_map or {}, funcs or {})
    return _vm
