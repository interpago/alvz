"""Tests para el runtime WASM de Alvz (sin dependencia de wasmtime)."""

import ctypes
from alvz.core.wasm_runtime import (
    _read_tag, _read_f64, _read_i32,
    _write_tag, _write_f64, _write_i32,
    _read_str, _write_str, _read_value,
    _tag_name, _MemWrapper,
    HOST_BUF_BASE, BC_BASE, CONST_BASE, STR_BASE, VAR_BASE,
    LIST_META, LIST_HEAP, CALL_STACK,
    TAG_NUM, TAG_BOOL, TAG_STR, TAG_NULL, TAG_LIST, TAG_DICT, TAG_FUNC,
    HOST_ROUND, HOST_POW, HOST_WAIT, HOST_SLICE,
    run,
)


def _make_mem():
    return bytearray(0x20000)


class TestHelpers:
    def test_read_write_tag(self):
        mem = _make_mem()
        _write_tag(mem, 100, TAG_STR)
        assert _read_tag(mem, 100) == TAG_STR
        _write_tag(mem, 200, TAG_LIST)
        assert _read_tag(mem, 200) == TAG_LIST

    def test_read_write_f64(self):
        mem = _make_mem()
        _write_f64(mem, 50, 3.14159)
        assert abs(_read_f64(mem, 50) - 3.14159) < 1e-10
        _write_f64(mem, 50, -2.5)
        assert _read_f64(mem, 50) == -2.5

    def test_read_write_i32(self):
        mem = _make_mem()
        _write_i32(mem, 10, 42)
        assert _read_i32(mem, 10) == 42
        _write_i32(mem, 10, -1)
        assert _read_i32(mem, 10) == -1

    def test_read_write_str(self):
        mem = _make_mem()
        offset = _write_str(mem, "hola mundo")
        assert isinstance(offset, float)
        assert _read_str(mem, offset) == "hola mundo"

    def test_write_str_multiple(self):
        mem = _make_mem()
        o1 = _write_str(mem, "abc")
        o2 = _write_str(mem, "def")
        assert _read_str(mem, o1) == "abc"
        assert _read_str(mem, o2) == "def"
        assert o1 != o2  # diferentes offsets

    def test_write_str_vacio(self):
        mem = _make_mem()
        offset = _write_str(mem, "")
        assert _read_str(mem, offset) == ""

    def test_read_write_str_unicode(self):
        mem = _make_mem()
        s = "español ñ ü áéíóú 😊"
        offset = _write_str(mem, s)
        assert _read_str(mem, offset) == s

    def test_read_value(self):
        mem = _make_mem()
        _write_tag(mem, HOST_BUF_BASE, TAG_NUM)
        _write_f64(mem, HOST_BUF_BASE + 8, 42.0)
        tag, data = _read_value(mem, HOST_BUF_BASE)
        assert tag == TAG_NUM
        assert data == 42.0

    def test_read_value_bool(self):
        mem = _make_mem()
        _write_tag(mem, HOST_BUF_BASE, TAG_BOOL)
        _write_f64(mem, HOST_BUF_BASE + 8, 1.0)
        tag, data = _read_value(mem, HOST_BUF_BASE)
        assert tag == TAG_BOOL
        assert data == 1.0

    def test_read_value_null(self):
        mem = _make_mem()
        _write_tag(mem, HOST_BUF_BASE, TAG_NULL)
        tag, data = _read_value(mem, HOST_BUF_BASE)
        assert tag == TAG_NULL

    def test_tag_name(self):
        assert _tag_name(TAG_NUM) == 'numero'
        assert _tag_name(TAG_BOOL) == 'booleano'
        assert _tag_name(TAG_STR) == 'texto'
        assert _tag_name(TAG_NULL) == 'nulo'
        assert _tag_name(TAG_LIST) == 'lista'
        assert _tag_name(TAG_DICT) == 'diccionario'
        assert _tag_name(99) == 'desconocido'


class TestMemWrapper:
    def test_get_set_byte(self):
        arr = (ctypes.c_ubyte * 10)()
        w = _MemWrapper(arr)
        w[0] = 42
        assert w[0] == 42

    def test_get_slice(self):
        arr = (ctypes.c_ubyte * 10)()
        for i in range(10):
            arr[i] = i
        w = _MemWrapper(arr)
        assert w[2:5] == bytes([2, 3, 4])

    def test_set_slice(self):
        arr = (ctypes.c_ubyte * 10)()
        w = _MemWrapper(arr)
        w[0:4] = [10, 20, 30, 40]
        assert w[0] == 10
        assert w[3] == 40

    def test_from_bytearray(self):
        ba = bytearray([1, 2, 3])
        arr = (ctypes.c_ubyte * 3).from_buffer(ba)
        w = _MemWrapper(arr)
        assert w[0] == 1
        assert w[2] == 3
        w[1] = 99
        assert ba[1] == 99


class TestConstants:
    def test_memory_layout(self):
        assert HOST_BUF_BASE == 0x500
        assert BC_BASE == 0x4000
        assert CONST_BASE == 0x5000
        assert STR_BASE == 0x6000
        assert VAR_BASE == 0x8000
        assert LIST_META == 0xA000
        assert LIST_HEAP == 0xC000
        assert CALL_STACK == 0xE000

    def test_tags(self):
        assert TAG_NUM == 0
        assert TAG_BOOL == 1
        assert TAG_STR == 2
        assert TAG_NULL == 3
        assert TAG_LIST == 4
        assert TAG_DICT == 5
        assert TAG_FUNC == 6

    def test_host_opcodes(self):
        assert HOST_ROUND == 0
        assert HOST_POW == 1
        assert HOST_WAIT == 2
        assert HOST_SLICE == 44

    def test_host_opcode_range(self):
        """Los opcodes host van de 0 a 44 inclusive."""
        assert HOST_ROUND <= HOST_SLICE


class TestRun:
    def test_run_wasm_minimal(self):
        """Compila y ejecuta un .alvz minimo a .wasm."""
        import tempfile
        import os
        code = 'imprimir(42)\n'
        tmp_alvz = tempfile.NamedTemporaryFile(mode='w', suffix='.alvz', delete=False, encoding='utf-8')
        tmp_alvz.write(code)
        tmp_alvz.close()

        wasm_out = tmp_alvz.name.replace('.alvz', '.wasm')
        try:
            from alvz.core.compiler import build
            ok = build(tmp_alvz.name, output_file=wasm_out, opts={'backend': 'wasm'})
            assert ok, "Compilacion WASM fallo"
            assert os.path.exists(wasm_out)

            buf = []
            result = run(wasm_out, output_buffer=buf)
            assert result is True
            assert any('42' in str(s) for s in buf)
        finally:
            os.unlink(tmp_alvz.name)
            if os.path.exists(wasm_out):
                os.unlink(wasm_out)
