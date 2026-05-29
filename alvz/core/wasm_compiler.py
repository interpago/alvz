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
    instr_i32_const, instr_f64_const,
    instr_local_get, instr_local_set, instr_local_tee,
    instr_global_get, instr_global_set,
    instr_call, instr_return, instr_drop,
    VALTYPE
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
OP_I32_TRUNC_F64_S = 0xAA
OP_F64_CONVERT_I32_S = 0xB7


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
        _TEE_LOCAL(2) +     # $addr
        tag_expr +
        _STORE_I32(0) +     # tag at offset 0
        _GET_LOCAL(2) +
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
        _TEE_LOCAL(2) +     # $addr
        _LOAD_I32(0) +
        _SET_LOCAL(3) +     # $t = tag
        _GET_LOCAL(2) +
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
        t_main = m.add_type([], [])

        # -- Importaciones --
        # 0: print_num, 1: print_bool, 2: print_str
        m.add_import_func('alvz', 'print_num', t_print_num)
        m.add_import_func('alvz', 'print_bool', t_print_bool)
        m.add_import_func('alvz', 'print_str', t_print_str)
        # 3: random_range, 4: input_num
        m.add_import_func('alvz', 'random_range', t_random)
        m.add_import_func('alvz', 'input_num', t_input_num)

        # -- Funcion principal --
        m.add_function(t_main)

        # -- Memoria --
        m.add_memory(MEM_PAGES)

        # -- Globales --
        m.add_global('i32', True, _I32(0))  # 0: $sp
        m.add_global('i32', True, _I32(0))  # 1: $next_list_idx
        m.add_global('i32', True, _I32(0))  # 2: $next_heap_idx
        m.add_global('i32', True, _I32(0))  # 3: $call_sp

        # -- Exportaciones --
        m.add_export('memory', 'mem', 0)
        m.add_export('main', 'func', len(m._imports))

        # ========== Cuerpo de la funcion main ==========
        body = bytearray()

        # $ip(0)=i32, $addr(1)=i32, $op(2)=i32, $t(3)=i32, $d(4)=f64,
        # $idx(5)=i32, $saved_tag(6)=i32, $saved_data(7)=f64,
        # $tmp_i32(8)=i32, $tmp_f64(9)=f64
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

        # OP_JUMP = 19, OP_JUMP_IF_FALSE = 20
        body.extend(self._check_op(OpCode.OP_JUMP, self._compile_jump(False)))
        body.extend(self._check_op(OpCode.OP_JUMP_IF_FALSE, self._compile_jump(True)))

        # OP_INPUT = 21, OP_RANDOM = 22
        body.extend(self._check_op(OpCode.OP_INPUT, self._compile_input()))
        body.extend(self._check_op(OpCode.OP_RANDOM, self._compile_random()))

        # OP_CALL = 24, OP_RETURN = 25
        body.extend(self._check_op(OpCode.OP_CALL, self._compile_call()))
        body.extend(self._check_op(OpCode.OP_RETURN, self._compile_return()))

        # OP_POP = 26
        body.extend(self._check_op(OpCode.OP_POP, pop_instr()))

        # OP_LIST = 28
        body.extend(self._check_op(OpCode.OP_LIST, self._compile_list_create()))

        # OP_GET_INDEX = 29, OP_SET_INDEX = 30
        body.extend(self._check_op(OpCode.OP_GET_INDEX, self._compile_get_index()))
        body.extend(self._check_op(OpCode.OP_SET_INDEX, self._compile_set_index()))

        # OP_LENGTH = 31
        body.extend(self._check_op(OpCode.OP_LENGTH, self._compile_length()))

        # OP_APPEND = 32
        body.extend(self._check_op(OpCode.OP_APPEND, self._compile_append()))

        # OP_DICT = 39
        body.extend(self._check_op(OpCode.OP_DICT, push_instr(_I32(TAG_DICT), _F64(0.0))))

        # OP_NEGATE = 65
        body.extend(self._check_op(OpCode.OP_NEGATE, self._compile_negate()))

        # OP_NULL = 75
        body.extend(self._check_op(OpCode.OP_NULL, push_instr(_I32(TAG_NULL), _F64(0.0))))

        # OP_LOAD = 3, OP_STORE = 2, OP_LOAD_GLOBAL = 5, OP_STORE_GLOBAL = 4
        body.extend(self._check_op(OpCode.OP_LOAD, self._compile_load(False)))
        body.extend(self._check_op(OpCode.OP_STORE, self._compile_store(False)))
        body.extend(self._check_op(OpCode.OP_LOAD_GLOBAL, self._compile_load(True)))
        body.extend(self._check_op(OpCode.OP_STORE_GLOBAL, self._compile_store(True)))

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
            _GET_LOCAL(8) +
            bytes([logical_op]) +      # result = a OP b as i32
            bytes([OP_F64_CONVERT_I32_S]) +  # f64(result)
            _STACK_ADDR +
            _TEE_LOCAL(2) +
            _I32(TAG_BOOL) +
            _STORE_I32(0) +
            _GET_LOCAL(2) +
            _STORE_F64(4) +
            _GET_GLOBAL(0) + _I32(1) + bytes([OP_I32_ADD]) + _SET_GLOBAL(0) +
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
        var_base = 0x8000
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
        var_base = 0x8000
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
            _TEE_LOCAL(8) +               # $tmp_i32 = count
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
    # CALL / RETURN
    # ====================================================================
    def _compile_call(self):
        """CALL: leer func_addr de bytecode[ip+1], guardar frame, saltar."""
        return (
            # Leer func_addr (bytecode[ip+1] contiene la direccion absoluta)
            _GET_LOCAL(0) + _I32(1) + bytes([OP_I32_ADD]) +
            _LOAD_U8(BC_BASE) +           # func_addr
            _SET_LOCAL(8) +               # $tmp_i32 = func_addr
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


def compile_wasm(bytecode, constants, functions, line_map=None):
    compiler = WasmCompiler(bytecode, constants, functions, line_map)
    return compiler.compile()
