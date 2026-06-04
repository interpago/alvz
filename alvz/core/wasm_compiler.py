"""
Compilador WASM para Alvz - traduce bytecode a modulo WASM binario.

Arquitectura: maquina virtual de bytecode implementada en WASM.
- Pila de valores en memoria lineal (cada entrada: tag i32 + data f64 = 16 bytes)
- Bytecode y constantes embebidos como data segments
- Loop de dispatch con cadena if/else
- Funciones host importadas para I/O (print, input, random, etc.)
"""

import struct
from .bytecode import OpCode
from .wasm_encoder import (
    WasmModule, _uleb128, _sleb128,
    instr_call
)

# Constantes de layout memoria lineal
MEM_PAGES = 2
VSLOT = 16          # bytes por entrada en pila de valores
STACK_BASE = 0      # offset inicio pila de valores (crece hacia arriba)
BC_BASE = 0x4000    # bytecode
CONST_BASE = 0x5000 # constantes (tag i32 + data f64 = 12 bytes c/u)
STR_BASE = 0x6000   # datos de strings (length-prefixed)
VAR_BASE = 0x8000   # variables locales/globales (512 * 16 = 8KB, hasta 0xA000)
LIST_META = 0xA000  # metadatos de listas (8 bytes c/u: count i32 + heap_start i32)
LIST_HEAP = 0xC000  # datos de elementos de lista (16 bytes c/u: tag + data)
CALL_STACK = 0xE000 # pila de llamadas (8 bytes c/frame: return_ip + saved_sp)

# Tags de tipos Alvz
TAG_NUM = 0
TAG_BOOL = 1
TAG_STR = 2
TAG_NULL = 3
TAG_LIST = 4
TAG_DICT = 5
TAG_FUNC = 6

# Opcodes WASM utilitarios
OP_BLOCK = 0x02
OP_LOOP = 0x03
OP_IF = 0x04
OP_ELSE = 0x05
OP_END = 0x0B
OP_BR = 0x0C
OP_BR_IF = 0x0D
OP_RETURN = 0x0F
OP_CALL = 0x10
OP_DROP = 0x1A
OP_SELECT = 0x1B
OP_LOCAL_GET = 0x20
OP_LOCAL_SET = 0x21
OP_LOCAL_TEE = 0x22
OP_GLOBAL_GET = 0x23
OP_GLOBAL_SET = 0x24
OP_I32_LOAD = 0x28
OP_I32_LOAD8_U = 0x2D
OP_F64_LOAD = 0x2B
OP_I32_STORE = 0x36
OP_F64_STORE = 0x39
OP_I32_CONST = 0x41
OP_F64_CONST = 0x44
OP_I32_EQZ = 0x45
OP_I32_EQ = 0x46
OP_I32_NE = 0x47
OP_I32_LT_S = 0x48
OP_I32_GT_S = 0x4A
OP_I32_LE_S = 0x4C
OP_I32_GE_S = 0x4E
OP_I32_ADD = 0x6A
OP_I32_SUB = 0x6B
OP_I32_MUL = 0x6C
OP_I32_AND = 0x71
OP_I32_OR = 0x72
OP_F64_ADD = 0xA0
OP_F64_SUB = 0xA1
OP_F64_MUL = 0xA2
OP_F64_DIV = 0xA3
OP_F64_EQ = 0x61
OP_F64_NE = 0x62
OP_F64_LT = 0x63
OP_F64_GT = 0x64
OP_F64_LE = 0x65
OP_F64_GE = 0x66
OP_F64_NEG = 0x9F
OP_F64_TRUNC = 0x9D
OP_I32_TRUNC_F64_S = 0xAA
OP_F64_CONVERT_I32_S = 0xB7
OP_F64_ABS = 0x9B
OP_F64_SQRT = 0xA2
OP_F64_CEIL = 0x9E
OP_F64_FLOOR = 0x9F

# Alvz host call opcodes (for single generic host import)
HOST_ROUND = 0
HOST_POW = 1
HOST_WAIT = 2
HOST_TIME = 3
HOST_LOWER = 4
HOST_UPPER = 5
HOST_REPLACE = 6
HOST_FILE_READ = 7
HOST_FILE_WRITE = 8
HOST_HTTP_REQUEST = 9
HOST_JSON_ENCODE = 10
HOST_JSON_DECODE = 11
HOST_SQLITE_OPEN = 12
HOST_SQLITE_EXEC = 13
HOST_SQLITE_QUERY = 14
HOST_SUPABASE_INSERT = 15
HOST_DATE_FORMAT = 16
HOST_STRING_SPLIT = 17
HOST_STRING_JOIN = 18
HOST_TO_NUMBER = 19
HOST_REGEX_SEARCH = 20
HOST_GET_OUTPUT = 21
HOST_INPUT_NUM = 22
HOST_TYPE_OF = 23
HOST_CLEAR = 24
HOST_IMPORT = 25
HOST_SUPABASE_SELECT = 26
HOST_READ_FILE = 27
HOST_WRITE_FILE = 28
HOST_WEB_SEND = 29
HOST_CLASS = 30
HOST_NEW = 31
HOST_GET_ATTR = 32
HOST_SET_ATTR = 33
HOST_SUPER_ATTR = 34
HOST_INSTANCEOF = 35
HOST_TRY_PUSH = 36
HOST_TRY_POP = 37
HOST_THROW = 38
HOST_ERROR_MSG = 39
HOST_ASYNC_CALL = 40
HOST_AWAIT = 41
HOST_SQRT = 42
HOST_ABS = 43
HOST_SLICE = 44

# Buffer para resultados de host
# +0: tag i32, +8: data f64, +16: advance_ip i32 (0 = default 1)
HOST_BUF_BASE = 0x500


def _I32(v):
    return bytes([OP_I32_CONST]) + _sleb128(v)

def _F64(v):
    return bytes([OP_F64_CONST]) + struct.pack('<d', v)

def _GET_LOCAL(idx):
    return bytes([OP_LOCAL_GET]) + _uleb128(idx)

def _SET_LOCAL(idx):
    return bytes([OP_LOCAL_SET]) + _uleb128(idx)

def _TEE_LOCAL(idx):
    return bytes([OP_LOCAL_TEE]) + _uleb128(idx)

def _GET_GLOBAL(idx):
    return bytes([OP_GLOBAL_GET]) + _uleb128(idx)

def _SET_GLOBAL(idx):
    return bytes([OP_GLOBAL_SET]) + _uleb128(idx)

def _STORE_I32(off=0):
    return bytes([OP_I32_STORE]) + _uleb128(0) + _uleb128(off)

def _STORE_F64(off=0):
    return bytes([OP_F64_STORE]) + _uleb128(0) + _uleb128(off)

def _LOAD_I32(off=0):
    return bytes([OP_I32_LOAD]) + _uleb128(0) + _uleb128(off)

def _LOAD_F64(off=0):
    return bytes([OP_F64_LOAD]) + _uleb128(0) + _uleb128(off)

def _LOAD_U8(off=0):
    return bytes([OP_I32_LOAD8_U]) + _uleb128(0) + _uleb128(off)

_STACK_ADDR = (
    _GET_GLOBAL(0) +        # $sp
    _I32(VSLOT) +
    bytes([OP_I32_MUL]) +
    _I32(STACK_BASE) +
    bytes([OP_I32_ADD])
)


def push_instr(tag_expr, data_expr):
    """Genera WASM para pushear (tag, data) a la pila de valores. sp += 1"""
    return (
        _STACK_ADDR +
        _TEE_LOCAL(8) +     # $tmp = addr
        tag_expr +
        _STORE_I32(0) +     # tag at offset 0
        _GET_LOCAL(8) +
        data_expr +
        _STORE_F64(4) +     # data at offset 4
        _GET_GLOBAL(0) +
        _I32(1) +
        bytes([OP_I32_ADD]) +
        _SET_GLOBAL(0)      # sp++
    )


def pop_instr():
    """Genera WASM para hacer pop. Deja tag en local $t, data en local $d."""
    return (
        _GET_GLOBAL(0) +
        _I32(1) +
        bytes([OP_I32_SUB]) +
        _SET_GLOBAL(0) +    # sp--
        _STACK_ADDR +
        _TEE_LOCAL(8) +     # $tmp = addr
        _LOAD_I32(0) +
        _SET_LOCAL(3) +     # $t = tag
        _GET_LOCAL(8) +
        _LOAD_F64(4) +
        _SET_LOCAL(4)       # $d = data
    )


class WasmCompiler:
    """Compila Alvz bytecode a modulo WASM binario."""

    def __init__(self, bytecode, constants, functions, line_map=None):
        self.bc = bytecode
        self.consts = constants
        self.funcs = functions or []
        self.line_map = line_map or {}

    def _serialize_constants(self):
        """Serializa constantes a bytes.
        Cada constante: 12 bytes (tag i32 + data f64).
        Strings: data = float(offset_into_str_data).
        str_data tiene formato length-prefixed: [i32 len][bytes...]"""
        data = bytearray()
        str_data = bytearray()
        for idx, val in enumerate(self.consts):
            if val is None:
                data.extend(struct.pack('<i', TAG_NULL))
                data.extend(struct.pack('<d', 0.0))
            elif isinstance(val, bool):
                data.extend(struct.pack('<i', TAG_BOOL))
                data.extend(struct.pack('<d', 1.0 if val else 0.0))
            elif isinstance(val, (int, float)):
                data.extend(struct.pack('<i', TAG_NUM))
                data.extend(struct.pack('<d', float(val)))
            elif isinstance(val, str):
                sbytes = val.encode('utf-8')
                offset = len(str_data)  # byte offset into str_data
                data.extend(struct.pack('<i', TAG_STR))
                data.extend(struct.pack('<d', float(offset)))
                str_data.extend(struct.pack('<i', len(sbytes)))
                str_data.extend(sbytes)
            elif isinstance(val, dict):
                import json
                json_bytes = json.dumps(val, ensure_ascii=False).encode('utf-8')
                offset = len(str_data)
                data.extend(struct.pack('<i', TAG_DICT))
                data.extend(struct.pack('<d', float(offset)))
                str_data.extend(struct.pack('<i', len(json_bytes)))
                str_data.extend(json_bytes)
        pad = 0x1000 - (len(data) % 0x1000)
        if pad < 0x1000:
            data.extend(b'\x00' * pad)
        pad2 = 0x1000 - (len(str_data) % 0x1000)
        if pad2 < 0x1000:
            str_data.extend(b'\x00' * pad2)
        return bytes(data), bytes(str_data)

    def compile(self):
        """Retorna: bytes del modulo .wasm"""
        const_bytes, str_bytes = self._serialize_constants()
        m = WasmModule()

        # -- Tipos para funciones importadas --
        t_print_num = m.add_type(['f64'], [])
        t_print_bool = m.add_type(['i32'], [])
        t_print_str = m.add_type(['i32', 'i32'], [])
        t_random = m.add_type(['f64', 'f64'], ['f64'])
        t_input_num = m.add_type([], ['f64'])
        # 5: host_call(op, arg1, arg2, arg3, arg4) -> ()  (escribe resultado en HOST_BUF_BASE)
        t_host_call = m.add_type(['i32', 'i32', 'i32', 'i32', 'i32'], [])
        t_main = m.add_type([], [])

        # -- Importaciones --
        # 0: print_num, 1: print_bool, 2: print_str
        m.add_import_func('alvz', 'print_num', t_print_num)
        m.add_import_func('alvz', 'print_bool', t_print_bool)
        m.add_import_func('alvz', 'print_str', t_print_str)
        # 3: random_range, 4: input_num
        m.add_import_func('alvz', 'random_range', t_random)
        m.add_import_func('alvz', 'input_num', t_input_num)
        # 5: host_call(op, arg1, arg2, arg3, arg4) -> ()
        m.add_import_func('alvz_host', 'call', t_host_call)

        # -- Funcion principal --
        m.add_function(t_main)

        # -- Memoria (importada del host) --
        m.add_import_memory('alvz', 'memory', MEM_PAGES)

        # -- Globales --
        m.add_global('i32', True, _I32(0))  # 0: $sp
        m.add_global('i32', True, _I32(0))  # 1: $next_list_idx
        m.add_global('i32', True, _I32(0))  # 2: $next_heap_idx
        m.add_global('i32', True, _I32(0))  # 3: $call_sp

        # -- Exportaciones --
        m.add_export('memory', 'mem', 0)
        num_imported_funcs = sum(1 for imp in m._imports if imp[0] == 'func')
        m.add_export('main', 'func', num_imported_funcs)

        # ========== Cuerpo de la funcion main ==========
        body = bytearray()

        # $ip(0)=i32, $addr(1)=i32, $op(2)=i32, $t(3)=i32, $d(4)=f64,
        # $idx(5)=i32, $saved_tag(6)=i32, $saved_data(7)=f64,
        # $tmp_i32(8)=i32, $tmp_f64(9)=f64,
        # $arg_tag0(10)=i32, $arg_data0(11)=f64,
        # $arg_tag1(12)=i32, $arg_data1(13)=f64
        locals_decl = [
            (1, 'i32'),  # 0: $ip
            (1, 'i32'),  # 1: $addr
            (1, 'i32'),  # 2: $op
            (1, 'i32'),  # 3: $t
            (1, 'f64'),  # 4: $d
            (1, 'i32'),  # 5: $idx
            (1, 'i32'),  # 6: $saved_tag
            (1, 'f64'),  # 7: $saved_data
            (1, 'i32'),  # 8: $tmp_i32
            (1, 'f64'),  # 9: $tmp_f64
            (1, 'i32'),  # 10: $arg_tag
            (1, 'f64'),  # 11: $arg_data
            (1, 'i32'),  # 12: $arg_tag2
            (1, 'f64'),  # 13: $arg_data2
        ]

        # Inicializar $ip = 0
        body.extend(_I32(0) + _SET_LOCAL(0))

        # Loop principal
        body.extend(bytes([OP_BLOCK, 0x40]))  # block $done
        body.extend(bytes([OP_LOOP, 0x40]))   # loop $main

        # Cargar opcode en $op = bytecode[ip]
        body.extend(
            _GET_LOCAL(0) +
            _I32(BC_BASE) +
            bytes([OP_I32_ADD]) +
            _LOAD_U8(0) +
            _TEE_LOCAL(2)  # $op = opcode at $ip
        )

        # ==== Dispatch: if/else chain ====
        # OP_HALT = 27
        body.extend(self._check_op(OpCode.OP_HALT, bytes([OP_RETURN])))

        # OP_CONSTANT = 1
        body.extend(self._check_op(OpCode.OP_CONSTANT, self._compile_constant()))

        # OP_PRINT = 6
        body.extend(self._check_op(OpCode.OP_PRINT, self._compile_print()))

        # OP_ADD = 7, OP_SUB = 8, OP_MUL = 9, OP_DIV = 10
        body.extend(self._check_op(OpCode.OP_ADD, self._compile_binop(OP_F64_ADD)))
        body.extend(self._check_op(OpCode.OP_SUB, self._compile_binop(OP_F64_SUB)))
        body.extend(self._check_op(OpCode.OP_MUL, self._compile_binop(OP_F64_MUL)))
        body.extend(self._check_op(OpCode.OP_DIV, self._compile_binop(OP_F64_DIV)))

        # OP_EQ = 11 ... OP_LTE = 16
        body.extend(self._check_op(OpCode.OP_EQ, self._compile_binop(OP_F64_EQ, TAG_BOOL, OP_F64_CONVERT_I32_S)))
        body.extend(self._check_op(OpCode.OP_NE, self._compile_binop(OP_F64_NE, TAG_BOOL, OP_F64_CONVERT_I32_S)))
        body.extend(self._check_op(OpCode.OP_GT, self._compile_binop(OP_F64_GT, TAG_BOOL, OP_F64_CONVERT_I32_S)))
        body.extend(self._check_op(OpCode.OP_LT, self._compile_binop(OP_F64_LT, TAG_BOOL, OP_F64_CONVERT_I32_S)))
        body.extend(self._check_op(OpCode.OP_GTE, self._compile_binop(OP_F64_GE, TAG_BOOL, OP_F64_CONVERT_I32_S)))
        body.extend(self._check_op(OpCode.OP_LTE, self._compile_binop(OP_F64_LE, TAG_BOOL, OP_F64_CONVERT_I32_S)))

        # OP_AND = 17, OP_OR = 18
        body.extend(self._check_op(OpCode.OP_AND, self._compile_andor(OP_I32_AND)))
        body.extend(self._check_op(OpCode.OP_OR, self._compile_andor(OP_I32_OR)))

        # OP_JUMP = 19, OP_JUMP_IF_FALSE = 20, OP_JUMP_IF_TRUE = 66
        body.extend(self._check_op(OpCode.OP_JUMP, self._compile_jump(False)))
        body.extend(self._check_op(OpCode.OP_JUMP_IF_FALSE, self._compile_jump(True)))
        body.extend(self._check_op(OpCode.OP_JUMP_IF_TRUE, self._compile_jump_if_true()))

        # OP_INPUT = 21, OP_RANDOM = 22
        body.extend(self._check_op(OpCode.OP_INPUT, self._compile_input()))
        body.extend(self._check_op(OpCode.OP_RANDOM, self._compile_random()))

        # OP_CALL = 24, OP_RETURN = 25
        body.extend(self._check_op(OpCode.OP_CALL, self._compile_call()))
        body.extend(self._check_op(OpCode.OP_RETURN, self._compile_return()))

        # OP_POP = 26
        body.extend(self._check_op(OpCode.OP_POP, pop_instr()))

        # OP_MAKE_FUNC = 67
        body.extend(self._check_op(OpCode.OP_MAKE_FUNC, self._compile_make_func()))

        # OP_LIST = 28
        body.extend(self._check_op(OpCode.OP_LIST, self._compile_list_create()))

        # OP_GET_INDEX = 29, OP_SET_INDEX = 30
        body.extend(self._check_op(OpCode.OP_GET_INDEX, self._compile_get_index()))
        body.extend(self._check_op(OpCode.OP_SET_INDEX, self._compile_set_index()))

        # OP_LENGTH = 31
        body.extend(self._check_op(OpCode.OP_LENGTH, self._compile_length()))

        # OP_APPEND = 32
        body.extend(self._check_op(OpCode.OP_APPEND, self._compile_append()))

        # OP_MOD = 51
        body.extend(self._check_op(OpCode.OP_MOD, self._compile_mod()))

        # OP_SLICE = 64
        body.extend(self._check_op(OpCode.OP_SLICE, self._compile_slice()))

        # OP_DICT = 39
        body.extend(self._check_op(OpCode.OP_DICT, push_instr(_I32(TAG_DICT), _F64(0.0))))

        # OP_DICT_KEYS = 82
        body.extend(self._check_op(OpCode.OP_DICT_KEYS, self._compile_dict_keys()))

        # OP_NEGATE = 65
        body.extend(self._check_op(OpCode.OP_NEGATE, self._compile_negate()))

        # OP_NULL = 75
        body.extend(self._check_op(OpCode.OP_NULL, push_instr(_I32(TAG_NULL), _F64(0.0))))

        # OP_LOAD = 3, OP_STORE = 2, OP_LOAD_GLOBAL = 5, OP_STORE_GLOBAL = 4
        body.extend(self._check_op(OpCode.OP_LOAD, self._compile_load(False)))
        body.extend(self._check_op(OpCode.OP_STORE, self._compile_store(False)))
        body.extend(self._check_op(OpCode.OP_LOAD_GLOBAL, self._compile_load(True)))
        body.extend(self._check_op(OpCode.OP_STORE_GLOBAL, self._compile_store(True)))

        # ==== Opcodes faltantes ====

        # OP_CLEAR = 23
        body.extend(self._check_op(OpCode.OP_CLEAR, self._compile_clear()))

        # OP_WAIT = 33
        body.extend(self._check_op(OpCode.OP_WAIT, self._compile_wait()))

        # OP_WEB_SEND = 34
        body.extend(self._check_op(OpCode.OP_WEB_SEND, self._compile_web_send()))

        # OP_WRITE_FILE = 35
        body.extend(self._check_op(OpCode.OP_WRITE_FILE, self._compile_write_file()))

        # OP_LOWER = 36, OP_UPPER = 37
        body.extend(self._check_op(OpCode.OP_LOWER, self._compile_lower()))
        body.extend(self._check_op(OpCode.OP_UPPER, self._compile_upper()))

        # OP_GET_OUTPUT = 38
        body.extend(self._check_op(OpCode.OP_GET_OUTPUT, self._compile_get_output()))

        # OP_SUPABASE_INSERT = 40
        body.extend(self._check_op(OpCode.OP_SUPABASE_INSERT, self._compile_supabase_insert()))

        # OP_ROUND = 41, OP_POW = 42, OP_SQRT = 43
        body.extend(self._check_op(OpCode.OP_ROUND, self._compile_round()))
        body.extend(self._check_op(OpCode.OP_POW, self._compile_pow()))
        body.extend(self._check_op(OpCode.OP_SQRT, self._compile_sqrt()))

        # OP_TRY_PUSH = 44, OP_TRY_POP = 45, OP_THROW = 46, OP_ERROR_MSG = 52
        body.extend(self._check_op(OpCode.OP_TRY_PUSH, self._compile_try_push()))
        body.extend(self._check_op(OpCode.OP_TRY_POP, self._compile_try_pop()))
        body.extend(self._check_op(OpCode.OP_THROW, self._compile_throw()))
        body.extend(self._check_op(OpCode.OP_ERROR_MSG, self._compile_error_msg()))

        # OP_CLASS = 47, OP_NEW = 48, OP_GET_ATTR = 49, OP_SET_ATTR = 50
        body.extend(self._check_op(OpCode.OP_CLASS, self._compile_class()))
        body.extend(self._check_op(OpCode.OP_NEW, self._compile_new()))
        body.extend(self._check_op(OpCode.OP_GET_ATTR, self._compile_get_attr()))
        body.extend(self._check_op(OpCode.OP_SET_ATTR, self._compile_set_attr()))

        # OP_ABS = 61
        body.extend(self._check_op(OpCode.OP_ABS, self._compile_abs()))

        # OP_READ_FILE = 53
        body.extend(self._check_op(OpCode.OP_READ_FILE, self._compile_read_file()))

        # OP_SUPABASE_SELECT = 54
        body.extend(self._check_op(OpCode.OP_SUPABASE_SELECT, self._compile_supabase_select()))

        # OP_JSON_DECODE = 55, OP_JSON_ENCODE = 58
        body.extend(self._check_op(OpCode.OP_JSON_DECODE, self._compile_json_decode()))
        body.extend(self._check_op(OpCode.OP_JSON_ENCODE, self._compile_json_encode()))

        # OP_IMPORT = 56
        body.extend(self._check_op(OpCode.OP_IMPORT, self._compile_import()))

        # OP_TIME = 57
        body.extend(self._check_op(OpCode.OP_TIME, self._compile_time()))

        # OP_TYPE = 59
        body.extend(self._check_op(OpCode.OP_TYPE, self._compile_type()))

        # OP_REPLACE = 60
        body.extend(self._check_op(OpCode.OP_REPLACE, self._compile_replace()))

        # OP_INPUT_NUM = 62
        body.extend(self._check_op(OpCode.OP_INPUT_NUM, self._compile_input_num()))

        # OP_START_SERVER = 63
        body.extend(self._check_op(OpCode.OP_START_SERVER, self._compile_start_server()))

        # OP_SUPER_ATTR = 68, OP_INSTANCEOF = 69
        body.extend(self._check_op(OpCode.OP_SUPER_ATTR, self._compile_super_attr()))
        body.extend(self._check_op(OpCode.OP_INSTANCEOF, self._compile_instanceof()))

        # OP_DATE_FORMAT = 70, OP_STRING_SPLIT = 71, OP_STRING_JOIN = 72
        # OP_TO_NUMBER = 73, OP_REGEX_SEARCH = 74
        body.extend(self._check_op(OpCode.OP_DATE_FORMAT, self._compile_date_format()))
        body.extend(self._check_op(OpCode.OP_STRING_SPLIT, self._compile_string_split()))
        body.extend(self._check_op(OpCode.OP_STRING_JOIN, self._compile_string_join()))
        body.extend(self._check_op(OpCode.OP_TO_NUMBER, self._compile_to_number()))
        body.extend(self._check_op(OpCode.OP_REGEX_SEARCH, self._compile_regex_search()))

        # OP_ASYNC_CALL = 76, OP_AWAIT = 77
        body.extend(self._check_op(OpCode.OP_ASYNC_CALL, self._compile_async_call()))
        body.extend(self._check_op(OpCode.OP_AWAIT, self._compile_await()))

        # OP_SOLICITUD_HTTP = 81
        body.extend(self._check_op(OpCode.OP_SOLICITUD_HTTP, self._compile_solicitud_http()))

        # OP_SQLITE_ABRIR = 78, OP_SQLITE_EJECUTAR = 79, OP_SQLITE_CONSULTAR = 80
        body.extend(self._check_op(OpCode.OP_SQLITE_ABRIR, self._compile_sqlite_abrir()))
        body.extend(self._check_op(OpCode.OP_SQLITE_EJECUTAR, self._compile_sqlite_ejecutar()))
        body.extend(self._check_op(OpCode.OP_SQLITE_CONSULTAR, self._compile_sqlite_consultar()))

        # Default: advance ip by 1
        body.extend(
            _GET_LOCAL(0) + _I32(1) + bytes([OP_I32_ADD]) + _SET_LOCAL(0)
        )
        body.extend(bytes([OP_BR, 0x00]))  # br $main

        body.extend(bytes([OP_END]))  # end loop
        body.extend(bytes([OP_END]))  # end block
        body.extend(bytes([OP_END]))  # end function

        m.add_code(locals_decl, bytes(body))

        # Data segments
        bc_bytes = bytes(int(o) & 0xFF for o in self.bc)
        m.add_data(_I32(BC_BASE), bc_bytes)
        m.add_data(_I32(CONST_BASE), const_bytes)
        if str_bytes:
            m.add_data(_I32(STR_BASE), str_bytes)

        return m.to_bytes()

    # ====================================================================
    # Helper: check opcode
    # ====================================================================
    def _check_op(self, opcode, handler_bytes):
        """Genera: if ($op == opcode) { handler_bytes }"""
        return (
            _GET_LOCAL(2) +
            _I32(int(opcode)) +
            bytes([OP_I32_EQ]) +
            bytes([OP_IF, 0x40]) +
            handler_bytes +
            bytes([OP_END])
        )

    # ====================================================================
    # Constante
    # ====================================================================
    def _compile_constant(self):
        return (
            _GET_LOCAL(0) +
            _I32(1) +
            bytes([OP_I32_ADD]) +
            _I32(BC_BASE) +
            bytes([OP_I32_ADD]) +
            _LOAD_U8(0) +        # const_idx = bytecode[ip+1]
            _TEE_LOCAL(5) +       # $idx = const_idx
            _I32(12) +
            bytes([OP_I32_MUL]) +
            _I32(CONST_BASE) +
            bytes([OP_I32_ADD]) +
            _TEE_LOCAL(1) +       # $addr = CONST_BASE + const_idx * 12
            _LOAD_I32(0) +
            _SET_LOCAL(3) +       # $t = tag
            _GET_LOCAL(1) +
            _LOAD_F64(4) +
            _SET_LOCAL(4) +       # $d = data
            push_instr(
                _GET_LOCAL(3),
                _GET_LOCAL(4)
            ) +
            _GET_LOCAL(0) + _I32(2) + bytes([OP_I32_ADD]) + _SET_LOCAL(0) +
            bytes([OP_BR, 0x01])
        )

    # ====================================================================
    # Binop (ADD, SUB, MUL, DIV, EQ, NE, GT, LT, GTE, LTE)
    # ====================================================================
    def _compile_binop(self, wasm_op, result_tag=TAG_NUM, post_op=None):
        data_expr = (
            _GET_LOCAL(4) +         # a_data
            _GET_LOCAL(7) +         # b_data
            bytes([wasm_op])
        )
        if post_op is not None:
            data_expr += bytes([post_op])
        return (
            pop_instr() +              # pop b
            _GET_LOCAL(3) + _SET_LOCAL(6) +
            _GET_LOCAL(4) + _SET_LOCAL(7) +
            pop_instr() +              # pop a
            push_instr(
                _I32(result_tag),
                data_expr
            )
        )

    # ====================================================================
    # AND / OR
    # ====================================================================
    def _is_truthy(self):
        """Genera WASM que deja i32(0/1) en el stack: truthy del valor en ($t, $d)."""
        return (
            _GET_LOCAL(3) +  # tag
            _I32(TAG_BOOL) +
            bytes([OP_I32_EQ]) +
            bytes([OP_IF, 0x7F]) +
            _GET_LOCAL(4) +
            _F64(1.0) +
            bytes([OP_F64_EQ]) +
            bytes([OP_ELSE]) +
            _GET_LOCAL(3) +
            _I32(TAG_NUM) +
            bytes([OP_I32_EQ]) +
            bytes([OP_IF, 0x7F]) +
            _GET_LOCAL(4) +
            _F64(0.0) +
            bytes([OP_F64_NE]) +
            bytes([OP_ELSE]) +
            _GET_LOCAL(3) +
            _I32(TAG_NULL) +
            bytes([OP_I32_EQ]) +
            bytes([OP_IF, 0x7F]) +
            _I32(0) +
            bytes([OP_ELSE]) +
            _I32(1) +
            bytes([OP_END]) +
            bytes([OP_END]) +
            bytes([OP_END])
        )

    def _compile_andor(self, logical_op):
        return (
            pop_instr() +
            _GET_LOCAL(3) + _SET_LOCAL(6) +
            _GET_LOCAL(4) + _SET_LOCAL(7) +
            pop_instr() +
            self._is_truthy() +        # a_truthy -> i32 on stack
            _SET_LOCAL(8) +            # save a_truthy to $tmp_i32
            _GET_LOCAL(6) + _SET_LOCAL(3) +
            _GET_LOCAL(7) + _SET_LOCAL(4) +
            self._is_truthy() +        # b_truthy -> i32 on stack
            _SET_LOCAL(6) +            # save b_truthy to $saved_tag
            push_instr(
                _I32(TAG_BOOL),
                _GET_LOCAL(6) +
                _GET_LOCAL(8) +
                bytes([logical_op]) +
                bytes([OP_F64_CONVERT_I32_S])
            ) +
            _GET_LOCAL(0) + _I32(1) + bytes([OP_I32_ADD]) + _SET_LOCAL(0) +
            bytes([OP_BR, 0x01])
        )

    # ====================================================================
    # NEGATE
    # ====================================================================
    def _compile_negate(self):
        return (
            pop_instr() +
            push_instr(
                _I32(TAG_NUM),
                _GET_LOCAL(4) + bytes([OP_F64_NEG])
            )
        )

    # ====================================================================
    # PRINT
    # ====================================================================
    def _compile_print(self):
        return (
            pop_instr() +
            _GET_LOCAL(3) + _I32(TAG_NUM) + bytes([OP_I32_EQ]) +
            bytes([OP_IF, 0x40]) +
            _GET_LOCAL(4) + instr_call(0) +
            bytes([OP_END]) +
            _GET_LOCAL(3) + _I32(TAG_BOOL) + bytes([OP_I32_EQ]) +
            bytes([OP_IF, 0x40]) +
            _GET_LOCAL(4) + bytes([OP_I32_TRUNC_F64_S]) + instr_call(1) +
            bytes([OP_END]) +
            _GET_LOCAL(3) + _I32(TAG_STR) + bytes([OP_I32_EQ]) +
            bytes([OP_IF, 0x40]) +
            _GET_LOCAL(4) +
            bytes([OP_I32_TRUNC_F64_S]) +  # offset into str_data
            _I32(STR_BASE) +
            bytes([OP_I32_ADD]) +          # addr of length-prefixed string
            _TEE_LOCAL(1) +                 # $addr = base addr
            _LOAD_I32(0) +                  # length from [addr]
            _SET_LOCAL(5) +                 # $idx = length (temp)
            _GET_LOCAL(1) +
            _I32(4) +
            bytes([OP_I32_ADD]) +          # ptr = addr + 4
            _GET_LOCAL(5) +                 # length
            instr_call(2) +                 # print_str(ptr, len)
            bytes([OP_END])
        )

    # ====================================================================
    # LOAD / STORE (variables)
    # ====================================================================
    def _compile_load(self, is_global):
        var_base = 0x9000 if is_global else 0x8000
        return (
            _GET_LOCAL(0) +
            _I32(1) +
            bytes([OP_I32_ADD]) +
            _LOAD_U8(BC_BASE) +
            _TEE_LOCAL(5) +
            _I32(VSLOT) +
            bytes([OP_I32_MUL]) +
            _I32(var_base) +
            bytes([OP_I32_ADD]) +
            _TEE_LOCAL(1) +
            _LOAD_I32(0) +
            _SET_LOCAL(3) +
            _GET_LOCAL(1) +
            _LOAD_F64(4) +
            _SET_LOCAL(4) +
            push_instr(_GET_LOCAL(3), _GET_LOCAL(4)) +
            _GET_LOCAL(0) + _I32(2) + bytes([OP_I32_ADD]) + _SET_LOCAL(0) +
            bytes([OP_BR, 0x01])
        )

    def _compile_store(self, is_global):
        var_base = 0x9000 if is_global else 0x8000
        return (
            pop_instr() +
            _GET_LOCAL(0) +
            _I32(1) +
            bytes([OP_I32_ADD]) +
            _LOAD_U8(BC_BASE) +
            _TEE_LOCAL(5) +
            _I32(VSLOT) +
            bytes([OP_I32_MUL]) +
            _I32(var_base) +
            bytes([OP_I32_ADD]) +
            _TEE_LOCAL(1) +
            _GET_LOCAL(3) +
            _STORE_I32(0) +
            _GET_LOCAL(1) +
            _GET_LOCAL(4) +
            _STORE_F64(4) +
            _GET_LOCAL(0) + _I32(2) + bytes([OP_I32_ADD]) + _SET_LOCAL(0) +
            bytes([OP_BR, 0x01])
        )

    # ====================================================================
    # JUMP
    # ====================================================================
    def _compile_jump(self, conditional):
        if conditional:
            return (
                _GET_LOCAL(0) + _I32(1) + bytes([OP_I32_ADD]) +
                _LOAD_U8(BC_BASE) + _TEE_LOCAL(5) +
                pop_instr() +
                _GET_LOCAL(4) + _F64(0.0) + bytes([OP_F64_EQ]) +
                bytes([OP_IF, 0x40]) +
                _GET_LOCAL(5) + _SET_LOCAL(0) +
                bytes([OP_ELSE]) +
                _GET_LOCAL(0) + _I32(2) + bytes([OP_I32_ADD]) + _SET_LOCAL(0) +
                bytes([OP_END]) +
                bytes([OP_BR, 0x01])
            )
        else:
            return (
                _GET_LOCAL(0) + _I32(1) + bytes([OP_I32_ADD]) +
                _LOAD_U8(BC_BASE) + _SET_LOCAL(0) +
                bytes([OP_BR, 0x01])
            )

    # ====================================================================
    # INPUT / RANDOM
    # ====================================================================
    def _compile_input(self):
        return (
            instr_call(4) +             # input_num() -> f64 on stack
            _SET_LOCAL(9) +             # $tmp_f64 = result
            _STACK_ADDR +
            _TEE_LOCAL(2) +
            _I32(TAG_NUM) +
            _STORE_I32(0) +
            _GET_LOCAL(2) +
            _GET_LOCAL(9) +
            _STORE_F64(4) +
            _GET_GLOBAL(0) + _I32(1) + bytes([OP_I32_ADD]) + _SET_GLOBAL(0) +
            _GET_LOCAL(0) + _I32(1) + bytes([OP_I32_ADD]) + _SET_LOCAL(0) +
            bytes([OP_BR, 0x01])
        )

    def _compile_random(self):
        return (
            pop_instr() +               # pop max
            _GET_LOCAL(4) + _SET_LOCAL(7) +  # save max_data to $saved_data
            pop_instr() +               # pop min
            _GET_LOCAL(4) +             # min f64 on stack
            _GET_LOCAL(7) +             # max f64 on stack
            instr_call(3) +             # random_range(min, max) -> f64
            _SET_LOCAL(9) +             # $tmp_f64 = result
            _STACK_ADDR +
            _TEE_LOCAL(2) +
            _I32(TAG_NUM) +
            _STORE_I32(0) +
            _GET_LOCAL(2) +
            _GET_LOCAL(9) +
            _STORE_F64(4) +
            _GET_GLOBAL(0) + _I32(1) + bytes([OP_I32_ADD]) + _SET_GLOBAL(0) +
            _GET_LOCAL(0) + _I32(1) + bytes([OP_I32_ADD]) + _SET_LOCAL(0) +
            bytes([OP_BR, 0x01])
        )

    # ====================================================================
    # LIST operations
    # ====================================================================
    def _compile_list_create(self):
        """Crea lista vacia: (TAG_LIST, list_idx). Inicializa metadatos."""
        return (
            _GET_GLOBAL(1) +              # $next_list_idx
            _TEE_LOCAL(5) +               # $idx = list_idx
            # Inicializar metadata: count=0, heap_start=$next_heap_idx
            _I32(8) + bytes([OP_I32_MUL]) +
            _I32(LIST_META) +
            bytes([OP_I32_ADD]) +
            _TEE_LOCAL(1) +               # $addr = meta_addr
            _I32(0) +                     # count = 0
            _STORE_I32(0) +
            _GET_LOCAL(1) +
            _I32(4) + bytes([OP_I32_ADD]) +  # meta_addr + 4
            _GET_GLOBAL(2) +              # $next_heap_idx
            _STORE_I32(0) +              # heap_start = next_heap_idx
            # Incrementar $next_list_idx
            _GET_GLOBAL(1) + _I32(1) + bytes([OP_I32_ADD]) + _SET_GLOBAL(1) +
            push_instr(
                _I32(TAG_LIST),
                _GET_LOCAL(5) + bytes([OP_F64_CONVERT_I32_S])
            ) +
            _GET_LOCAL(0) + _I32(1) + bytes([OP_I32_ADD]) + _SET_LOCAL(0) +
            bytes([OP_BR, 0x01])
        )

    def _compile_append(self):
        """LIST_APPEND: pop value, pop list, agregar elemento."""
        return (
            pop_instr() +                 # pop value -> $t, $d
            _GET_LOCAL(3) + _SET_LOCAL(6) +  # save value tag
            _GET_LOCAL(4) + _SET_LOCAL(7) +  # save value data
            pop_instr() +                 # pop list
            # $d(4) = list_idx as f64
            _GET_LOCAL(4) +
            bytes([OP_I32_TRUNC_F64_S]) +  # list_idx as i32
            _TEE_LOCAL(5) +               # $idx = list_idx
            # Cargar metadata
            _I32(8) + bytes([OP_I32_MUL]) +
            _I32(LIST_META) +
            bytes([OP_I32_ADD]) +
            _TEE_LOCAL(1) +               # $addr = meta_addr
            _LOAD_I32(0) +                # count
            _SET_LOCAL(8) +               # $tmp_i32 = count
            # Calcular direccion del elemento en heap
            _GET_LOCAL(1) +               # meta_addr
            _I32(4) + bytes([OP_I32_ADD]) +
            _LOAD_I32(0) +                # heap_start
            _GET_LOCAL(8) +               # count
            bytes([OP_I32_ADD]) +         # heap_start + count
            _I32(VSLOT) +
            bytes([OP_I32_MUL]) +
            _I32(LIST_HEAP) +
            bytes([OP_I32_ADD]) +         # element addr
            _TEE_LOCAL(2) +               # $addr2 = element_addr
            _GET_LOCAL(6) +               # value tag
            _STORE_I32(0) +
            _GET_LOCAL(2) +
            _GET_LOCAL(7) +               # value data
            _STORE_F64(4) +
            # Incrementar count en metadata
            _GET_LOCAL(1) +               # meta_addr
            _GET_LOCAL(8) + _I32(1) + bytes([OP_I32_ADD]) +  # count + 1
            _STORE_I32(0) +
            _GET_LOCAL(0) + _I32(1) + bytes([OP_I32_ADD]) + _SET_LOCAL(0) +
            bytes([OP_BR, 0x01])
        )

    def _compile_get_index(self):
        """GET_INDEX: pop index, pop list, pushear elemento en indice."""
        return (
            pop_instr() +                 # pop index -> $t, $d
            _GET_LOCAL(4) +
            bytes([OP_I32_TRUNC_F64_S]) +  # index as i32
            _SET_LOCAL(8) +               # $tmp_i32 = index
            pop_instr() +                 # pop list
            _GET_LOCAL(4) +
            bytes([OP_I32_TRUNC_F64_S]) +  # list_idx as i32
            _TEE_LOCAL(5) +
            # Leer heap_start de metadata
            _I32(8) + bytes([OP_I32_MUL]) +
            _I32(LIST_META) +
            bytes([OP_I32_ADD]) +
            _I32(4) + bytes([OP_I32_ADD]) +  # meta_addr + 4 = heap_start
            _LOAD_I32(0) +                # heap_start
            _GET_LOCAL(8) +               # index
            bytes([OP_I32_ADD]) +         # heap_start + index
            _I32(VSLOT) +
            bytes([OP_I32_MUL]) +
            _I32(LIST_HEAP) +
            bytes([OP_I32_ADD]) +         # element_addr
            _TEE_LOCAL(1) +
            _LOAD_I32(0) +
            _SET_LOCAL(3) +               # $t = element tag
            _GET_LOCAL(1) +
            _LOAD_F64(4) +
            _SET_LOCAL(4) +               # $d = element data
            push_instr(_GET_LOCAL(3), _GET_LOCAL(4)) +
            _GET_LOCAL(0) + _I32(1) + bytes([OP_I32_ADD]) + _SET_LOCAL(0) +
            bytes([OP_BR, 0x01])
        )

    def _compile_set_index(self):
        """SET_INDEX: pop value, pop index, pop list, escribir elemento."""
        return (
            pop_instr() +                 # pop value -> $t, $d
            _GET_LOCAL(3) + _SET_LOCAL(6) +  # save value tag
            _GET_LOCAL(4) + _SET_LOCAL(7) +  # save value data
            pop_instr() +                 # pop index
            _GET_LOCAL(4) +
            bytes([OP_I32_TRUNC_F64_S]) +
            _SET_LOCAL(8) +               # $tmp_i32 = index
            pop_instr() +                 # pop list
            _GET_LOCAL(4) +
            bytes([OP_I32_TRUNC_F64_S]) +  # list_idx
            _TEE_LOCAL(5) +
            _I32(8) + bytes([OP_I32_MUL]) +
            _I32(LIST_META) +
            bytes([OP_I32_ADD]) +
            _I32(4) + bytes([OP_I32_ADD]) +
            _LOAD_I32(0) +               # heap_start
            _GET_LOCAL(8) +              # index
            bytes([OP_I32_ADD]) +
            _I32(VSLOT) +
            bytes([OP_I32_MUL]) +
            _I32(LIST_HEAP) +
            bytes([OP_I32_ADD]) +
            _TEE_LOCAL(1) +              # element addr
            _GET_LOCAL(6) +              # value tag
            _STORE_I32(0) +
            _GET_LOCAL(1) +
            _GET_LOCAL(7) +              # value data
            _STORE_F64(4) +
            _GET_LOCAL(0) + _I32(1) + bytes([OP_I32_ADD]) + _SET_LOCAL(0) +
            bytes([OP_BR, 0x01])
        )

    def _compile_length(self):
        """LENGTH: pop valor, pushear longitud (para listas)."""
        return (
            pop_instr() +
            _GET_LOCAL(3) + _I32(TAG_LIST) + bytes([OP_I32_EQ]) +
            bytes([OP_IF, 0x40]) +
            # Es lista: leer count de metadata
            _GET_LOCAL(4) +
            bytes([OP_I32_TRUNC_F64_S]) +
            _I32(8) + bytes([OP_I32_MUL]) +
            _I32(LIST_META) +
            bytes([OP_I32_ADD]) +
            _LOAD_I32(0) +               # count
            bytes([OP_F64_CONVERT_I32_S]) +  # count as f64
            _SET_LOCAL(9) +              # $tmp_f64 = count
            _STACK_ADDR +
            _TEE_LOCAL(2) +
            _I32(TAG_NUM) +
            _STORE_I32(0) +
            _GET_LOCAL(2) +
            _GET_LOCAL(9) +
            _STORE_F64(4) +
            _GET_GLOBAL(0) + _I32(1) + bytes([OP_I32_ADD]) + _SET_GLOBAL(0) +
            bytes([OP_ELSE]) +
            # No es lista: push 0
            push_instr(_I32(TAG_NUM), _F64(0.0)) +
            bytes([OP_END]) +
            _GET_LOCAL(0) + _I32(1) + bytes([OP_I32_ADD]) + _SET_LOCAL(0) +
            bytes([OP_BR, 0x01])
        )

    # ====================================================================
    # MOD
    # ====================================================================
    def _compile_mod(self):
        """MOD: pop b, pop a, push (a % b). WASM no tiene f64.mod, usamos a - b * trunc(a/b)."""
        return (
            pop_instr() +
            _GET_LOCAL(3) + _SET_LOCAL(6) +
            _GET_LOCAL(4) + _SET_LOCAL(7) +
            pop_instr() +
            push_instr(
                _I32(TAG_NUM),
                _GET_LOCAL(4) +         # a
                _GET_LOCAL(7) +         # b
                _GET_LOCAL(4) +         # a
                _GET_LOCAL(7) +         # b
                bytes([OP_F64_DIV]) +
                bytes([OP_F64_TRUNC]) +
                bytes([OP_F64_MUL]) +
                bytes([OP_F64_SUB])
            )
        )

    # ====================================================================
    # JUMP_IF_TRUE
    # ====================================================================
    def _compile_jump_if_true(self):
        """JUMP_IF_TRUE: pop valor, si truthy saltar a bytecode[ip+1], si no ip+=2."""
        return (
            _GET_LOCAL(0) + _I32(1) + bytes([OP_I32_ADD]) +
            _LOAD_U8(BC_BASE) + _TEE_LOCAL(5) +
            pop_instr() +
            self._is_truthy() +
            bytes([OP_IF, 0x40]) +
            _GET_LOCAL(5) + _SET_LOCAL(0) +
            bytes([OP_ELSE]) +
            _GET_LOCAL(0) + _I32(2) + bytes([OP_I32_ADD]) + _SET_LOCAL(0) +
            bytes([OP_END]) +
            bytes([OP_BR, 0x01])
        )

    # ====================================================================
    # MAKE_FUNC
    # ====================================================================
    def _compile_make_func(self):
        """MAKE_FUNC: leer func_addr y num_params de bytecode, pushear descriptor."""
        return (
            # Leer func_addr (bytecode[ip+1])
            _GET_LOCAL(0) + _I32(1) + bytes([OP_I32_ADD]) +
            _LOAD_U8(BC_BASE) +
            _SET_LOCAL(5) +              # $tmp_i32 = func_addr
            # Leer num_params (bytecode[ip+2])
            _GET_LOCAL(0) + _I32(2) + bytes([OP_I32_ADD]) +
            _LOAD_U8(BC_BASE) +
            _SET_LOCAL(6) +              # $tmp_i32_2 = num_params
            # Avanzar ip en 3 (opcode + addr + nparams)
            _GET_LOCAL(0) + _I32(3) + bytes([OP_I32_ADD]) + _SET_LOCAL(0) +
            # Pushear descriptor (TAG_FUNC, func_addr como f64)
            push_instr(
                _I32(TAG_FUNC),
                _GET_LOCAL(5) + bytes([OP_F64_CONVERT_I32_S])
            ) +
            bytes([OP_BR, 0x01])
        )

    # ====================================================================
    # SLICE
    # ====================================================================
    def _compile_slice(self):
        """SLICE: pop fin, pop inicio, pop obj, push obj[inicio:fin].
        Los valores salvados deben coincidir con las posiciones que _host_call
        espera: $3/4=obj, $8/9=inicio, $10/11=fin.
        BR depths: TAG_LIST if está a depth 3 desde el loop, TAG_STR if a depth 4.
        BR 0x02 desde TAG_LIST, BR 0x03 desde TAG_STR/other llegan al loop."""
        return (
            pop_instr() +                 # pop fin -> $t, $d
            _GET_LOCAL(3) + _SET_LOCAL(10) + # save fin_tag a $10
            _GET_LOCAL(4) + _SET_LOCAL(11) + # save fin_data a $11
            pop_instr() +                 # pop inicio -> $t, $d
            _GET_LOCAL(3) + _SET_LOCAL(8) +  # save inicio_tag a $8
            _GET_LOCAL(4) + _SET_LOCAL(9) +  # save inicio_data a $9
            pop_instr() +                 # pop obj
            _GET_LOCAL(3) + _I32(TAG_LIST) + bytes([OP_I32_EQ]) +
            bytes([OP_IF, 0x40]) +
            # Es lista: crear lista nueva con elementos [inicio:fin]
            self._emit_list_slice() +
            _GET_LOCAL(0) + _I32(1) + bytes([OP_I32_ADD]) + _SET_LOCAL(0) +
            bytes([OP_BR, 0x02]) +
            bytes([OP_ELSE]) +
            _GET_LOCAL(3) + _I32(TAG_STR) + bytes([OP_I32_EQ]) +
            bytes([OP_IF, 0x40]) +
            # Es string: delegar a host_call(HOST_SLICE, 3, br_depth=3)
            self._host_call(HOST_SLICE, 3, br_depth=3) +
            bytes([OP_ELSE]) +
            # Otro tipo: push obj de vuelta
            push_instr(_GET_LOCAL(3), _GET_LOCAL(4)) +
            _GET_LOCAL(0) + _I32(1) + bytes([OP_I32_ADD]) + _SET_LOCAL(0) +
            bytes([OP_BR, 0x03]) +
            bytes([OP_END]) +
            bytes([OP_END])
        )

    def _emit_list_slice(self):
        """Helper: crear lista nueva copiando elementos [inicio:fin] de obj_lista.
        La lista obj esta en ($t=$3, $d=$4), inicio en ($8, $9), fin en ($6, $7)."""
        buf = bytearray()
        list_idx_local = 5
        count_local = 8
        # Leer metadata de la lista original
        buf.extend(
            _GET_LOCAL(4) +
            bytes([OP_I32_TRUNC_F64_S]) +
            _TEE_LOCAL(list_idx_local) +
            _I32(8) + bytes([OP_I32_MUL]) +
            _I32(LIST_META) +
            bytes([OP_I32_ADD]) +
            _TEE_LOCAL(1) +
            _LOAD_I32(0) +
            _SET_LOCAL(count_local) +
            _GET_LOCAL(1) + _I32(4) + bytes([OP_I32_ADD]) +
            _LOAD_I32(0) +
            _SET_LOCAL(1)
        )
        # inicio real: si null -> 0, si no -> int(data)
        buf.extend(
            _GET_LOCAL(8) +
            _I32(TAG_NULL) +
            bytes([OP_I32_EQ]) +
            bytes([OP_IF, 0x7F]) +
            _I32(0) +
            bytes([OP_ELSE]) +
            _GET_LOCAL(9) +
            bytes([OP_I32_TRUNC_F64_S]) +
            bytes([OP_END]) +
            _SET_LOCAL(8)
        )
        # fin real: si null -> count, si no -> int(data)
        buf.extend(
            _GET_LOCAL(6) +
            _I32(TAG_NULL) +
            bytes([OP_I32_EQ]) +
            bytes([OP_IF, 0x7F]) +
            _GET_LOCAL(count_local) +
            bytes([OP_ELSE]) +
            _GET_LOCAL(7) +
            bytes([OP_I32_TRUNC_F64_S]) +
            bytes([OP_END]) +
            _SET_LOCAL(6)
        )
        # Crear nueva lista
        buf.extend(
            _GET_GLOBAL(1) +
            _TEE_LOCAL(list_idx_local) +
            _I32(8) + bytes([OP_I32_MUL]) +
            _I32(LIST_META) +
            bytes([OP_I32_ADD]) +
            _TEE_LOCAL(2) +
            _I32(0) +
            _STORE_I32(0) +
            _GET_LOCAL(2) + _I32(4) + bytes([OP_I32_ADD]) +
            _GET_GLOBAL(2) +
            _STORE_I32(0) +
            _GET_GLOBAL(1) + _I32(1) + bytes([OP_I32_ADD]) + _SET_GLOBAL(1)
        )
        # Loop copiar elementos
        buf.extend(bytes([OP_BLOCK, 0x40]))
        buf.extend(bytes([OP_LOOP, 0x40]))
        buf.extend(
            _GET_LOCAL(8) +
            _GET_LOCAL(6) +
            bytes([OP_I32_GE_S]) +
            bytes([OP_BR_IF, 0x01]) +
            # Leer elemento original
            _GET_LOCAL(1) +
            _GET_LOCAL(8) +
            bytes([OP_I32_ADD]) +
            _I32(VSLOT) +
            bytes([OP_I32_MUL]) +
            _I32(LIST_HEAP) +
            bytes([OP_I32_ADD]) +
            _TEE_LOCAL(2) +
            _LOAD_I32(0) +
            _SET_LOCAL(3) +
            _GET_LOCAL(2) +
            _LOAD_F64(4) +
            _SET_LOCAL(4) +
            # Escribir en nueva lista
            _GET_LOCAL(list_idx_local) +
            _I32(8) + bytes([OP_I32_MUL]) +
            _I32(LIST_META) +
            bytes([OP_I32_ADD]) +
            _TEE_LOCAL(2) +
            _LOAD_I32(0) +
            _TEE_LOCAL(list_idx_local) +
            _GET_LOCAL(2) + _I32(4) + bytes([OP_I32_ADD]) +
            _LOAD_I32(0) +
            bytes([OP_I32_ADD]) +
            _I32(VSLOT) +
            bytes([OP_I32_MUL]) +
            _I32(LIST_HEAP) +
            bytes([OP_I32_ADD]) +
            _TEE_LOCAL(2) +
            _GET_LOCAL(3) +
            _STORE_I32(0) +
            _GET_LOCAL(2) +
            _GET_LOCAL(4) +
            _STORE_F64(4) +
            # Incrementar count
            _GET_LOCAL(list_idx_local) +
            _I32(8) + bytes([OP_I32_MUL]) +
            _I32(LIST_META) +
            _TEE_LOCAL(2) +
            _GET_LOCAL(list_idx_local) +
            _I32(1) + bytes([OP_I32_ADD]) +
            _STORE_I32(0) +
            # i++
            _GET_LOCAL(8) + _I32(1) + bytes([OP_I32_ADD]) + _SET_LOCAL(8) +
            bytes([OP_BR, 0x00])
        )
        buf.extend(bytes([OP_END]))
        buf.extend(bytes([OP_END]))
        # Pushear nueva lista
        buf.extend(
            push_instr(
                _I32(TAG_LIST),
                _GET_LOCAL(list_idx_local) + bytes([OP_F64_CONVERT_I32_S])
            )
        )
        return bytes(buf)

    # ====================================================================
    # DICT_KEYS
    # ====================================================================
    def _compile_dict_keys(self):
        """DICT_KEYS: pop valor, si es dict pushear lista vacia, si no pushear valor."""
        return (
            pop_instr() +
            _GET_LOCAL(3) + _I32(TAG_DICT) + bytes([OP_I32_EQ]) +
            bytes([OP_IF, 0x40]) +
            # Es dict: push lista vacia (stub)
            push_instr(_I32(TAG_LIST), _F64(0.0)) +
            bytes([OP_ELSE]) +
            # No es dict: push valor de vuelta
            push_instr(_GET_LOCAL(3), _GET_LOCAL(4)) +
            bytes([OP_END]) +
            _GET_LOCAL(0) + _I32(1) + bytes([OP_I32_ADD]) + _SET_LOCAL(0) +
            bytes([OP_BR, 0x01])
        )

    # ====================================================================
    # CALL / RETURN
    # ====================================================================
    def _compile_call(self):
        """CALL: leer func_addr de bytecode[ip+1], guardar frame, saltar."""
        VAL_I32 = 0x7F
        return (
            # Leer func_addr (bytecode[ip+1])
            _GET_LOCAL(0) + _I32(1) + bytes([OP_I32_ADD]) +
            _LOAD_U8(BC_BASE) +           # func_addr
            _TEE_LOCAL(8) +               # $tmp_i32 = func_addr
            # Si func_addr == 0, obtener desde descriptor en pila
            bytes([OP_IF, VAL_I32]) +     # if i32 produce i32
            # func_addr != 0: usar directamente
            _GET_LOCAL(8) +
            bytes([OP_ELSE]) +
            # func_addr == 0: pop descriptor de la pila de valores
            pop_instr() +
            _GET_LOCAL(4) +               # data (func_addr como f64)
            bytes([OP_I32_TRUNC_F64_S]) + # convertir a i32
            _SET_LOCAL(8) +               # $tmp_i32 = func_addr
            _GET_LOCAL(8) +
            bytes([OP_END]) +
            _SET_LOCAL(8) +               # asegurar $tmp_i32
            # Guardar frame en call stack
            _GET_GLOBAL(3) +              # $call_sp
            _I32(8) + bytes([OP_I32_MUL]) +
            _I32(CALL_STACK) + bytes([OP_I32_ADD]) +
            _TEE_LOCAL(1) +               # $addr = frame_addr
            # return_ip = $ip + 2
            _GET_LOCAL(0) + _I32(2) + bytes([OP_I32_ADD]) +
            _STORE_I32(0) +               # frame[0] = return_ip
            _GET_LOCAL(1) + _I32(4) + bytes([OP_I32_ADD]) +  # frame_addr + 4
            _GET_GLOBAL(0) +              # $sp
            _STORE_I32(0) +               # frame[4] = saved_sp
            # $call_sp++
            _GET_GLOBAL(3) + _I32(1) + bytes([OP_I32_ADD]) + _SET_GLOBAL(3) +
            # Saltar a funcion
            _GET_LOCAL(8) + _SET_LOCAL(0) +
            bytes([OP_BR, 0x01])
        )

    def _compile_return(self):
        """RETURN: pop return value, restaurar frame, continuar."""
        return (
            pop_instr() +                 # pop return value
            _GET_LOCAL(3) + _SET_LOCAL(6) +  # save return tag
            _GET_LOCAL(4) + _SET_LOCAL(7) +  # save return data
            # $call_sp--
            _GET_GLOBAL(3) + _I32(1) + bytes([OP_I32_SUB]) + _SET_GLOBAL(3) +
            # Leer frame
            _GET_GLOBAL(3) +
            _I32(8) + bytes([OP_I32_MUL]) +
            _I32(CALL_STACK) + bytes([OP_I32_ADD]) +
            _TEE_LOCAL(1) +               # $addr = frame_addr
            _LOAD_I32(0) +                # return_ip
            _SET_LOCAL(0) +               # $ip = return_ip
            _GET_LOCAL(1) + _I32(4) + bytes([OP_I32_ADD]) +
            _LOAD_I32(0) +                # saved_sp
            _SET_LOCAL(8) +               # $tmp_i32 = saved_sp
            # Restaurar sp
            _GET_LOCAL(8) + _SET_GLOBAL(0) +
            # Pushear return value de vuelta
            push_instr(
                _GET_LOCAL(6),            # return tag
                _GET_LOCAL(7)             # return data
            ) +
            bytes([OP_BR, 0x01])
        )


    # ====================================================================
    # Helpers: host call
    # ====================================================================

    def _pop_n_values(self, n):
        """Pop n Alvz values from stack into locals. Values stored in ($t0..$tn-1, $d0..$dn-1).
        For n>2, uses saved_tag* and saved_data* locals.
        Returns WASM bytes that leave tag0 in $3, data0 in $4 when n>=1, etc."""
        buf = bytearray()
        for i in range(n):
            if i > 0:
                buf.extend(_GET_LOCAL(3) + _SET_LOCAL(6 + i * 2))
                buf.extend(_GET_LOCAL(4) + _SET_LOCAL(7 + i * 2))
            buf.extend(pop_instr())
        return bytes(buf)

    def _host_call(self, op_id, nargs, extra_bytes=b'', br_depth=1):
        """Genera WASM para llamar alvz_host.call.
        Escribe nargs valores del Alvz stack a HOST_BUF_BASE.
        Pasa (op_id, nargs, ip, 0, 0) al host.
        Lee resultado (tag, data, advance_ip) de HOST_BUF_BASE.
        Avanza ip segun advance_ip (0 = default 1) y hace br al loop."""
        buf = bytearray()
        # Escribir nargs
        buf.extend(_I32(nargs) + _I32(HOST_BUF_BASE) + _STORE_I32(0))
        for i in range(nargs):
            off = 8 + i * 16
            tag_src = 6 + i * 2
            data_src = 7 + i * 2
            if i == 0:
                tag_src = 3
                data_src = 4
            # WASM store expects (addr, value) on stack: addr first, value on top
            buf.extend(
                _I32(HOST_BUF_BASE + off) +
                _GET_LOCAL(tag_src) +
                _STORE_I32(0)
            )
            buf.extend(
                _I32(HOST_BUF_BASE + off + 8) +
                _GET_LOCAL(data_src) +
                _STORE_F64(0)
            )
        buf.extend(extra_bytes)
        # Call host: (op_id, nargs, ip, 0, 0)
        buf.extend(
            _I32(op_id) +
            _I32(nargs) +
            _GET_LOCAL(0) +  # current ip for bytecode reads
            _I32(0) +
            _I32(0) +
            instr_call(5)
        )
        # Leer resultado tag + data
        buf.extend(
            _I32(HOST_BUF_BASE) + _LOAD_I32(0) + _SET_LOCAL(3) +
            _I32(HOST_BUF_BASE + 8) + _LOAD_F64(0) + _SET_LOCAL(4)
        )
        # Push resultado al stack
        buf.extend(push_instr(_GET_LOCAL(3), _GET_LOCAL(4)))
        # Leer advance_ip, default a 1 si es 0
        buf.extend(
            _I32(HOST_BUF_BASE + 16) + _LOAD_I32(0) +
            bytes([OP_I32_EQZ]) +
            bytes([OP_IF, 0x7F]) +
            _I32(1) +
            bytes([OP_ELSE]) +
            _I32(HOST_BUF_BASE + 16) + _LOAD_I32(0) +
            bytes([OP_END]) +
            _GET_LOCAL(0) + bytes([OP_I32_ADD]) + _SET_LOCAL(0) +
            bytes([OP_BR, br_depth])
        )
        return bytes(buf)

    # ====================================================================
    # CLEAR
    # ====================================================================
    def _compile_clear(self):
        return self._host_call(HOST_CLEAR, 0)

    # ====================================================================
    # WAIT
    # ====================================================================
    def _compile_wait(self):
        return (
            self._pop_n_values(1) +
            self._host_call(HOST_WAIT, 1)
        )

    # ====================================================================
    # WEB_SEND
    # ====================================================================
    def _compile_web_send(self):
        return (
            self._pop_n_values(2) +
            self._host_call(HOST_WEB_SEND, 2)
        )

    # ====================================================================
    # WRITE_FILE
    # ====================================================================
    def _compile_write_file(self):
        return (
            self._pop_n_values(2) +
            self._host_call(HOST_WRITE_FILE, 2)
        )

    # ====================================================================
    # READ_FILE
    # ====================================================================
    def _compile_read_file(self):
        return (
            self._pop_n_values(1) +
            self._host_call(HOST_READ_FILE, 1)
        )

    # ====================================================================
    # LOWER / UPPER
    # ====================================================================
    def _compile_lower(self):
        return (
            self._pop_n_values(1) +
            self._host_call(HOST_LOWER, 1)
        )

    def _compile_upper(self):
        return (
            self._pop_n_values(1) +
            self._host_call(HOST_UPPER, 1)
        )

    # ====================================================================
    # GET_OUTPUT
    # ====================================================================
    def _compile_get_output(self):
        return self._host_call(HOST_GET_OUTPUT, 0)

    # ====================================================================
    # SUPABASE_INSERT / SUPABASE_SELECT
    # ====================================================================
    def _compile_supabase_insert(self):
        return (
            self._pop_n_values(4) +
            self._host_call(HOST_SUPABASE_INSERT, 4)
        )

    def _compile_supabase_select(self):
        return (
            self._pop_n_values(3) +
            self._host_call(HOST_SUPABASE_SELECT, 3)
        )

    # ====================================================================
    # ROUND / POW / SQRT / ABS
    # ====================================================================
    def _compile_round(self):
        return (
            self._pop_n_values(1) +
            self._host_call(HOST_ROUND, 1)
        )

    def _compile_pow(self):
        return (
            self._pop_n_values(2) +
            self._host_call(HOST_POW, 2)
        )

    def _compile_sqrt(self):
        """SQRT: pop valor, push raiz cuadrada via host."""
        return (
            self._pop_n_values(1) +
            self._host_call(HOST_SQRT, 1)
        )

    def _compile_abs(self):
        """ABS: pop valor, push valor absoluto via host."""
        return (
            self._pop_n_values(1) +
            self._host_call(HOST_ABS, 1)
        )

    # ====================================================================
    # TRY / THROW / ERROR_MSG
    # ====================================================================
    def _compile_try_push(self):
        return self._host_call(HOST_TRY_PUSH, 0)

    def _compile_try_pop(self):
        return self._host_call(HOST_TRY_POP, 0)

    def _compile_throw(self):
        return (
            self._pop_n_values(1) +
            self._host_call(HOST_THROW, 1)
        )

    def _compile_error_msg(self):
        return self._host_call(HOST_ERROR_MSG, 0)

    # ====================================================================
    # CLASS / NEW / GET_ATTR / SET_ATTR / SUPER_ATTR / INSTANCEOF
    # ====================================================================
    def _compile_class(self):
        return self._host_call(HOST_CLASS, 0)

    def _compile_new(self):
        return (
            self._pop_n_values(1) +
            self._host_call(HOST_NEW, 1)
        )

    def _compile_get_attr(self):
        return (
            self._pop_n_values(2) +
            self._host_call(HOST_GET_ATTR, 2)
        )

    def _compile_set_attr(self):
        return (
            self._pop_n_values(3) +
            self._host_call(HOST_SET_ATTR, 3)
        )

    def _compile_super_attr(self):
        return (
            self._pop_n_values(3) +
            self._host_call(HOST_SUPER_ATTR, 3)
        )

    def _compile_instanceof(self):
        return (
            self._pop_n_values(2) +
            self._host_call(HOST_INSTANCEOF, 2)
        )

    # ====================================================================
    # JSON
    # ====================================================================
    def _compile_json_encode(self):
        return (
            self._pop_n_values(1) +
            self._host_call(HOST_JSON_ENCODE, 1)
        )

    def _compile_json_decode(self):
        return (
            self._pop_n_values(1) +
            self._host_call(HOST_JSON_DECODE, 1)
        )

    # ====================================================================
    # IMPORT
    # ====================================================================
    def _compile_import(self):
        return (
            self._pop_n_values(1) +
            self._host_call(HOST_IMPORT, 1)
        )

    # ====================================================================
    # TIME
    # ====================================================================
    def _compile_time(self):
        return self._host_call(HOST_TIME, 0)

    # ====================================================================
    # TYPE
    # ====================================================================
    def _compile_type(self):
        return (
            self._pop_n_values(1) +
            self._host_call(HOST_TYPE_OF, 1)
        )

    # ====================================================================
    # REPLACE
    # ====================================================================
    def _compile_replace(self):
        return (
            self._pop_n_values(3) +
            self._host_call(HOST_REPLACE, 3)
        )

    # ====================================================================
    # INPUT_NUM
    # ====================================================================
    def _compile_input_num(self):
        return self._host_call(HOST_INPUT_NUM, 0)

    # ====================================================================
    # START_SERVER
    # ====================================================================
    def _compile_start_server(self):
        """START_SERVER: no-op en WASM (no soporta servidores HTTP)."""
        return (
            self._pop_n_values(2) +
            push_instr(_I32(TAG_NULL), _F64(0.0))
        )

    # ====================================================================
    # DATE_FORMAT
    # ====================================================================
    def _compile_date_format(self):
        return (
            self._pop_n_values(1) +
            self._host_call(HOST_DATE_FORMAT, 1)
        )

    # ====================================================================
    # STRING_SPLIT / STRING_JOIN / TO_NUMBER / REGEX_SEARCH
    # ====================================================================
    def _compile_string_split(self):
        return (
            self._pop_n_values(2) +
            self._host_call(HOST_STRING_SPLIT, 2)
        )

    def _compile_string_join(self):
        return (
            self._pop_n_values(2) +
            self._host_call(HOST_STRING_JOIN, 2)
        )

    def _compile_to_number(self):
        return (
            self._pop_n_values(1) +
            self._host_call(HOST_TO_NUMBER, 1)
        )

    def _compile_regex_search(self):
        return (
            self._pop_n_values(2) +
            self._host_call(HOST_REGEX_SEARCH, 2)
        )

    # ====================================================================
    # ASYNC_CALL / AWAIT
    # ====================================================================
    def _compile_async_call(self):
        return self._host_call(HOST_ASYNC_CALL, 0)

    def _compile_await(self):
        return (
            self._pop_n_values(1) +
            self._host_call(HOST_AWAIT, 1)
        )

    # ====================================================================
    # SOLICITUD_HTTP
    # ====================================================================
    def _compile_solicitud_http(self):
        return (
            self._pop_n_values(3) +
            self._host_call(HOST_HTTP_REQUEST, 3)
        )

    # ====================================================================
    # SQLITE
    # ====================================================================
    def _compile_sqlite_abrir(self):
        return (
            self._pop_n_values(1) +
            self._host_call(HOST_SQLITE_OPEN, 1)
        )

    def _compile_sqlite_ejecutar(self):
        return (
            self._pop_n_values(2) +
            self._host_call(HOST_SQLITE_EXEC, 2)
        )

    def _compile_sqlite_consultar(self):
        return (
            self._pop_n_values(2) +
            self._host_call(HOST_SQLITE_QUERY, 2)
        )


def compile_wasm(bytecode, constants, functions, line_map=None):
    compiler = WasmCompiler(bytecode, constants, functions, line_map)
    return compiler.compile()
