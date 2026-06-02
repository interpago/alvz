"""Tests para el modulo de compilacion/empaquetado de Alvz."""

import os
import tempfile
from alvz.core.compiler import _py_repr, _generate_py_script, build


class TestPyRepr:
    def test_none(self):
        assert _py_repr(None) == "None"

    def test_bool(self):
        assert _py_repr(True) == "True"
        assert _py_repr(False) == "False"

    def test_int(self):
        assert _py_repr(42) == "42"

    def test_float(self):
        assert _py_repr(3.14) == "3.14"

    def test_string_empty(self):
        assert _py_repr("") == "''"

    def test_unsupported_fallback(self):
        # tipos no soportados retornan "None"
        assert _py_repr([1, 2, 3]) == "None"
        assert _py_repr({"a": 1}) == "None"


class TestGenerateScript:
    def test_generates_valid_python(self):
        script = _generate_py_script(
            bytecode=[1, 0, 6],
            constants=["hola"],
            line_map={0: 1, 1: 1, 2: 1},
            functions={},
        )
        assert "alvz.core.vm" in script
        assert "VM(" in script
        assert "bytecode" in script
        assert "constants" in script
        assert "run()" in script

    def test_script_executable(self):
        script = _generate_py_script(
            bytecode=[27],
            constants=[],
            line_map={0: 1},
            functions={},
        )
        assert script.strip().endswith("vm.run()")


class TestBuild:
    def test_build_file_not_found(self):
        result = build("no_existe.alvz")
        assert result is False

    def test_build_with_real_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.alvz', delete=False, encoding='utf-8') as f:
            f.write('imprimir(42)\n')
            tmp = f.name

        wasm_output = tmp.replace('.alvz', '.wasm')
        try:
            result = build(tmp, output_file=wasm_output, opts={'backend': 'wasm'})
            assert result is True
            assert os.path.exists(wasm_output)
            with open(wasm_output, 'rb') as f:
                data = f.read()
            assert data[:4] == b'\x00asm'
        finally:
            os.unlink(tmp)
            if os.path.exists(wasm_output):
                os.unlink(wasm_output)
