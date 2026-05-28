"""
Encoder binario WASM - genera modulos .wasm desde Python.
"""

import struct

WASM_OP = {
    'unreachable': 0x00, 'nop': 0x01, 'block': 0x02, 'loop': 0x03,
    'if': 0x04, 'else': 0x05, 'end': 0x0B, 'br': 0x0C, 'br_if': 0x0D,
    'br_table': 0x0E, 'return': 0x0F, 'call': 0x10, 'call_indirect': 0x11,
    'drop': 0x1A, 'select': 0x1B, 'local_get': 0x20, 'local_set': 0x21,
    'local_tee': 0x22, 'global_get': 0x23, 'global_set': 0x24,
    'i32_load': 0x28, 'i64_load': 0x29, 'f64_load': 0x2B,
    'i32_load8_u': 0x2D,
    'i32_store': 0x36, 'i64_store': 0x37, 'f32_store': 0x38, 'f64_store': 0x39,
    'memory_size': 0x3F, 'memory_grow': 0x40,
    'i32_const': 0x41, 'i64_const': 0x42, 'f64_const': 0x44,
    'i32_eqz': 0x45, 'i32_eq': 0x46, 'i32_ne': 0x47,
    'i32_lt_s': 0x48, 'i32_gt_s': 0x4A, 'i32_le_s': 0x4C, 'i32_ge_s': 0x4E,
    'f64_eq': 0x61, 'f64_ne': 0x62, 'f64_lt': 0x63, 'f64_gt': 0x64,
    'f64_le': 0x65, 'f64_ge': 0x66,
    'i32_add': 0x6A, 'i32_sub': 0x6B, 'i32_mul': 0x6C,
    'f64_add': 0xA0, 'f64_sub': 0xA1, 'f64_mul': 0xA2, 'f64_div': 0xA3,
    'f64_neg': 0x9F, 'f64_abs': 0x9E,
    'i32_wrap_i64': 0xA7, 'i64_extend_i32_s': 0xAE,
    'i32_trunc_f64_s': 0xAA, 'f64_convert_i32_s': 0xB7,
    'f64_reinterpret_i64': 0xBF, 'i64_reinterpret_f64': 0xBE,
    'i32_and': 0x71, 'i32_or': 0x72, 'i32_xor': 0x73,
}

VALTYPE = {'i32': 0x7F, 'i64': 0x7E, 'f32': 0x7D, 'f64': 0x7C, 'funcref': 0x70}
EXTERN_KIND = {'func': 0x00, 'table': 0x01, 'mem': 0x02, 'global': 0x03}


def _uleb128(value):
    result = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            byte |= 0x80
        result.append(byte)
        if not value:
            break
    return bytes(result)


def _sleb128(value):
    result = bytearray()
    more = True
    while more:
        byte = value & 0x7F
        value >>= 7
        cond1 = (value == 0 and (byte & 0x40) == 0)
        cond2 = (value == -1 and (byte & 0x40) != 0)
        if cond1 or cond2:
            more = False
        else:
            byte |= 0x80
        result.append(byte)
    return bytes(result)


def _vec(items):
    """Encode a WASM vector: count (LEB128) + items (concatenated)."""
    data = bytearray(_uleb128(len(items)))
    for item in items:
        if isinstance(item, int):
            data.append(item)
        else:
            data.extend(item)
    return bytes(data)


def _section(id, content):
    return bytes([id]) + _uleb128(len(content)) + content


class WasmModule:
    def __init__(self):
        self._types = []
        self._imports = []
        self._functions = []
        self._memories = []
        self._globals = []
        self._exports = []
        self._codes = []
        self._data_segments = []

    def add_type(self, param_types, result_types):
        idx = len(self._types)
        self._types.append((param_types, result_types))
        return idx

    def add_import_func(self, module_name, field_name, type_idx):
        idx = len(self._imports)
        self._imports.append(('func', module_name, field_name, type_idx))
        return idx

    def add_function(self, type_idx):
        idx = len(self._functions)
        self._functions.append(type_idx)
        return idx

    def add_memory(self, min_pages, max_pages=0):
        self._memories.append((min_pages, max_pages if max_pages else None))

    def add_global(self, valtype, mutable, init_bytes):
        idx = len(self._globals)
        self._globals.append((valtype, mutable, init_bytes))
        return idx

    def add_export(self, name, kind, index):
        self._exports.append((name, kind, index))

    def add_code(self, local_types, instr_bytes):
        self._codes.append((local_types, instr_bytes))

    def add_data(self, offset_bytes, data_bytes):
        self._data_segments.append((offset_bytes, data_bytes))

    def to_bytes(self):
        sections = bytearray()
        sections.extend(self._encode_type())
        sections.extend(self._encode_import())
        if self._functions:
            sections.extend(self._encode_function())
        if self._memories:
            sections.extend(self._encode_memory())
        if self._globals:
            sections.extend(self._encode_global())
        sections.extend(self._encode_export())
        sections.extend(self._encode_code())
        if self._data_segments:
            sections.extend(self._encode_data())

        header = b'\x00asm' + struct.pack('<I', 1)
        return header + bytes(sections)

    def _encode_type(self):
        type_items = []
        for params, results in self._types:
            item = bytearray([0x60])
            item.extend(_vec([VALTYPE[p] for p in params]))
            item.extend(_vec([VALTYPE[r] for r in results]))
            type_items.append(bytes(item))
        return _section(1, _vec(type_items))

    def _encode_import(self):
        items = []
        for kind, mod, field, type_idx in self._imports:
            mbytes = mod.encode('utf-8')
            fbytes = field.encode('utf-8')
            item = bytearray()
            item.extend(_uleb128(len(mbytes)) + mbytes)
            item.extend(_uleb128(len(fbytes)) + fbytes)
            item.append(EXTERN_KIND[kind])
            if kind == 'func':
                item.extend(_uleb128(type_idx))
            items.append(bytes(item))
        return _section(2, _vec(items))

    def _encode_function(self):
        items = [_uleb128(t) for t in self._functions]
        return _section(3, _vec(items))

    def _encode_memory(self):
        items = []
        for min_p, max_p in self._memories:
            item = bytearray([0x00] if max_p is None else [0x01])
            item.extend(_uleb128(min_p))
            if max_p is not None:
                item.extend(_uleb128(max_p))
            items.append(bytes(item))
        return _section(5, _vec(items))

    def _encode_global(self):
        items = []
        for vtype, mutable, init in self._globals:
            item = bytearray([VALTYPE[vtype], 0x01 if mutable else 0x00])
            item.extend(init)
            item.append(0x0B)  # end
            items.append(bytes(item))
        return _section(6, _vec(items))

    def _encode_export(self):
        items = []
        for name, kind, idx in self._exports:
            nbytes = name.encode('utf-8')
            item = bytearray(_uleb128(len(nbytes)) + nbytes)
            item.append(EXTERN_KIND[kind])
            item.extend(_uleb128(idx))
            items.append(bytes(item))
        return _section(7, _vec(items))

    def _encode_code(self):
        items = []
        for local_types, instr in self._codes:
            body = bytearray()
            if local_types:
                local_items = []
                for count, t in local_types:
                    local_items.append(bytes([_uleb128(count)[0], VALTYPE[t]]))
                body.extend(_vec(local_items))
            else:
                body.extend(_uleb128(0))
            body.extend(instr)
            items.append(_uleb128(len(body)) + body)
        return _section(10, _vec(items))

    def _encode_data(self):
        items = []
        for offset_bytes, seg_bytes in self._data_segments:
            item = bytearray([0x00])  # active, memory 0
            item.extend(offset_bytes)
            item.append(0x0B)  # end of init expression
            item.extend(_uleb128(len(seg_bytes)) + seg_bytes)
            items.append(bytes(item))
        return _section(11, _vec(items))


# Instruction builder helpers (re-exported for wasm_compiler)

def instr_i32_const(value):
    return bytes([WASM_OP['i32_const']]) + _sleb128(value)

def instr_f64_const(value):
    return bytes([WASM_OP['f64_const']]) + struct.pack('<d', value)

def instr_local_get(idx):
    return bytes([WASM_OP['local_get']]) + _uleb128(idx)

def instr_local_set(idx):
    return bytes([WASM_OP['local_set']]) + _uleb128(idx)

def instr_local_tee(idx):
    return bytes([WASM_OP['local_tee']]) + _uleb128(idx)

def instr_global_get(idx):
    return bytes([WASM_OP['global_get']]) + _uleb128(idx)

def instr_global_set(idx):
    return bytes([WASM_OP['global_set']]) + _uleb128(idx)

def instr_call(idx):
    return bytes([WASM_OP['call']]) + _uleb128(idx)

def instr_return():
    return bytes([WASM_OP['return']])

def instr_drop():
    return bytes([WASM_OP['drop']])
