import pytest
from alvz.lsp.analyzer import Analyzer, _KEYWORDS


class TestAnalyzer:
    def test_diagnostics_balanced(self):
        a = Analyzer()
        errors = a.open_file('test.alvz', 'variable x = 1\nimprimir(x)\n')
        assert errors == []

    def test_diagnostics_mismatched_paren(self):
        a = Analyzer()
        errors = a.open_file('test.alvz', 'imprimir(1\n')
        paren_errors = [e for e in errors if 'parentesis' in e['message'].lower()]
        assert len(paren_errors) >= 1

    def test_diagnostics_mismatched_brace(self):
        a = Analyzer()
        errors = a.open_file('test.alvz', 'si verdadero {\n')
        brace_errors = [e for e in errors if 'llave' in e['message'].lower()]
        assert len(brace_errors) >= 1

    def test_diagnostics_unknown_char(self):
        a = Analyzer()
        errors = a.open_file('test.alvz', 'variable x = @\n')
        # The lexer catches the @ char and raises an error
        assert len(errors) >= 1

    def test_completions_includes_keywords(self):
        a = Analyzer()
        a.open_file('test.alvz', '')
        items = a.get_completions('test.alvz', 0, 0)
        labels = {i['label'] for i in items}
        assert 'si' in labels
        assert 'funcion' in labels
        assert 'clase' in labels

    def test_completions_includes_builtins(self):
        a = Analyzer()
        a.open_file('test.alvz', '')
        items = a.get_completions('test.alvz', 0, 0)
        labels = {i['label'] for i in items}
        assert 'imprimir' in labels
        assert 'azar' in labels

    def test_completions_includes_identifiers(self):
        a = Analyzer()
        a.open_file('test.alvz', 'variable mi_var = 42\n')
        items = a.get_completions('test.alvz', 1, 0)
        labels = {i['label'] for i in items}
        assert 'mi_var' in labels

    def test_symbols_variable(self):
        a = Analyzer()
        a.open_file('test.alvz', 'variable x = 10\n')
        syms = a.get_symbols('test.alvz')
        names = [s['name'] for s in syms]
        assert 'x' in names

    def test_symbols_function(self):
        a = Analyzer()
        a.open_file('test.alvz', 'funcion saludar() {}\n')
        syms = a.get_symbols('test.alvz')
        names = [s['name'] for s in syms]
        assert 'saludar' in names

    def test_symbols_class(self):
        a = Analyzer()
        a.open_file('test.alvz', 'clase Persona {}\n')
        syms = a.get_symbols('test.alvz')
        names = [s['name'] for s in syms]
        assert 'Persona' in names

    def test_symbols_property(self):
        a = Analyzer()
        a.open_file('test.alvz',
            'clase Foo {\n'
            '  propiedad x {}\n'
            '}\n')
        syms = a.get_symbols('test.alvz')
        names = [s['name'] for s in syms]
        assert 'x' in names

    def test_word_at(self):
        a = Analyzer()
        word = a._word_at('variable hola = 1', 0, 9)
        assert word == 'hola'
        word = a._word_at('variable hola = 1', 0, 16)
        assert word == '1'

    def test_hover_keyword(self):
        a = Analyzer()
        a.open_file('test.alvz', 'si verdadero {}\n')
        result = a.get_hover('test.alvz', 0, 0)
        assert result is not None
        assert 'si' in result['contents']

    def test_hover_builtin(self):
        a = Analyzer()
        a.open_file('test.alvz', 'imprimir(1)\n')
        result = a.get_hover('test.alvz', 0, 0)
        assert result is not None
        assert 'imprimir' in result['contents']

    def test_definition_function(self):
        a = Analyzer()
        code = 'funcion foo() {}\nfoo()\n'
        a.open_file('test.alvz', code)
        result = a.find_definition('test.alvz', 1, 0)
        assert result is not None
        assert result['range']['start']['line'] == 0

    def test_definition_class(self):
        a = Analyzer()
        code = 'clase Bar {}\nvariable b = nuevo Bar()\n'
        a.open_file('test.alvz', code)
        result = a.find_definition('test.alvz', 1, 22)
        assert result is not None
        assert result['range']['start']['line'] == 0

    def test_definition_variable(self):
        a = Analyzer()
        code = 'variable data = 1\nimprimir(data)\n'
        a.open_file('test.alvz', code)
        result = a.find_definition('test.alvz', 1, 10)
        assert result is not None
        assert result['range']['start']['line'] == 0
