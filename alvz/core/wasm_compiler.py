"""
Compilador WASM para Alvz - traduce bytecode a modulo WASM binario.

Arquitectura: maquina virtual de bytecode implementada en WASM.
- Pila de valores en memoria lineal (cada entrada: tag i32 + data f64 = 16 bytes)
- Bytecode y constantes embebidos como data segments
- Loop de dispatch con cadena if/else
- Funciones host importadas para I/O (print, input, etc.)
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

# Constantes de layout
MEM_PAGES = 1
VSLOT = 16          # bytes por entrada en pila de valores
STACK_BASE = 0      # offset inicio pila de valores
BC_BASE = 0x4000    # offset bytecode en memoria lineal
CONST_BASE = 0x5000 # offset constantes
STR_BASE = 0x6000   # offset datos de strings

# Tags de tipos Alvz
TAG_NUM = 0
TAG_BOOL = 1
TAG_STR = 2
TAG_NULL = 3
TAG_LIST = 4

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
OP_LOCAL_GET = 0x20
OP_LOCAL_SET = 0x21
OP_LOCAL_TEE = 0x22
OP_GLOBAL_GET = 0x23
OP_GLOBAL_SET = 0x24
OP_I32_LOAD = 0x28
OP_F64_LOAD = 0x2B
OP_I32_STORE = 0x36
OP_F64_STORE = 0x39
OP_I32_CONST = 0x41
OP_F64_CONST = 0x44
OP_I32_LOAD8_U = 0x2D
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
OP_I32_AND = 0x71
OP_I32_OR = 0x72


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
        self.funcs = functions
        self.line_map = line_map or {}

    def _serialize_constants(self):
        """Serializa constantes a bytes. Cada constante: 12 bytes (tag i32 + data f64)."""
        data = bytearray()
        str_data = bytearray()
        str_off = STR_BASE
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
                data.extend(struct.pack('<i', TAG_STR))
                data.extend(struct.pack('<d', float(len(sbytes))))
                str_data.extend(sbytes)
        # Padding
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

        # Tipos
        t_print_num = m.add_type(['f64'], [])
        t_print_bool = m.add_type(['i32'], [])
        t_print_str = m.add_type(['i32', 'i32'], [])
        t_main = m.add_type([], [])

        # Importaciones
        m.add_import_func('alvz', 'print_num', t_print_num)
        m.add_import_func('alvz', 'print_bool', t_print_bool)
        m.add_import_func('alvz', 'print_str', t_print_str)

        # Funcion
        m.add_function(t_main)

        # Memoria
        m.add_memory(MEM_PAGES)

        # Global: $sp (0)
        m.add_global('i32', True, _I32(0))

        # Exportaciones
        m.add_export('memory', 'mem', 0)
        m.add_export('main', 'func', len(m._imports))  # skip import funcs

        # === Codigo de la funcion main ===
        body = bytearray()

        # Locales: $ip(0), $addr(1), $op(2), $t(3), $d(4), $idx(5)
        # Usaremos locals via get/set con indices
        # locals: 0=$ip, 1=$addr, 2=$op, 3=$t, 4=$d, 5=$idx

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

        # === Dispatch: if/else chain ===
        # Cada handler verifica si el opcode coincide y ejecuta
        # Los handlers que no avanzan ip ellos mismos caen al default advance

        # OP_HALT = 27
        body.extend(self._check_op(OpCode.OP_HALT, bytes([OP_RETURN])))

        # OP_CONSTANT = 1 - leer indice de constante desde bytecode[ip+1]
        const_handler = (
            _GET_LOCAL(0) +
            _I32(1) +
            bytes([OP_I32_ADD]) +
            _I32(BC_BASE) +
            bytes([OP_I32_ADD]) +
            _LOAD_U8(0) +        # const_idx = bytecode[ip+1] (1 byte)
            _TEE_LOCAL(5) +       # $idx = const_idx
            _I32(12) +             # cada constante: 12 bytes
            bytes([OP_I32_MUL]) +
            _I32(CONST_BASE) +
            bytes([OP_I32_ADD]) +
            _TEE_LOCAL(1) +       # $addr = CONST_BASE + const_idx * 12
            _LOAD_I32(0) +        # load tag → pushes i32
            _SET_LOCAL(3) +       # $t = tag (consume from stack)
            _GET_LOCAL(1) +
            _LOAD_F64(4) +        # load data → pushes f64
            _SET_LOCAL(4) +       # $d = data (consume from stack)
            push_instr(
                _GET_LOCAL(3),    # tag from $t
                _GET_LOCAL(4)     # data from $d
            ) +
            _GET_LOCAL(0) + _I32(2) + bytes([OP_I32_ADD]) + _SET_LOCAL(0) +  # ip += 2
            bytes([OP_BR, 0x01])  # br $main
        )
        body.extend(self._check_op(OpCode.OP_CONSTANT, const_handler))

        # OP_PRINT = 6
        body.extend(self._check_op(OpCode.OP_PRINT, self._compile_print()))

        # OP_ADD = 7
        body.extend(self._check_op(OpCode.OP_ADD, self._compile_binop(OP_F64_ADD)))

        # OP_SUB = 8
        body.extend(self._check_op(OpCode.OP_SUB, self._compile_binop(OP_F64_SUB)))

        # OP_MUL = 9
        body.extend(self._check_op(OpCode.OP_MUL, self._compile_binop(OP_F64_MUL)))

        # OP_DIV = 10
        body.extend(self._check_op(OpCode.OP_DIV, self._compile_binop(OP_F64_DIV)))

        # OP_EQ = 11
        body.extend(self._check_op(OpCode.OP_EQ, self._compile_binop(OP_F64_EQ, TAG_BOOL, OP_F64_CONVERT_I32_S)))

        # OP_NE = 12
        body.extend(self._check_op(OpCode.OP_NE, self._compile_binop(OP_F64_NE, TAG_BOOL, OP_F64_CONVERT_I32_S)))

        # OP_GT = 13
        body.extend(self._check_op(OpCode.OP_GT, self._compile_binop(OP_F64_GT, TAG_BOOL, OP_F64_CONVERT_I32_S)))

        # OP_LT = 14
        body.extend(self._check_op(OpCode.OP_LT, self._compile_binop(OP_F64_LT, TAG_BOOL, OP_F64_CONVERT_I32_S)))

        # OP_GTE = 15
        body.extend(self._check_op(OpCode.OP_GTE, self._compile_binop(OP_F64_GE, TAG_BOOL, OP_F64_CONVERT_I32_S)))

        # OP_LTE = 16
        body.extend(self._check_op(OpCode.OP_LTE, self._compile_binop(OP_F64_LE, TAG_BOOL, OP_F64_CONVERT_I32_S)))

        # OP_NEGATE = 65
        body.extend(self._check_op(OpCode.OP_NEGATE, self._compile_negate()))

        # OP_POP = 26
        body.extend(self._check_op(OpCode.OP_POP, self._compile_pop_drop()))

        # OP_NULL = 75
        body.extend(self._check_op(OpCode.OP_NULL, push_instr(_I32(TAG_NULL), _F64(0.0))))

        # OP_LOAD = 3
        body.extend(self._check_op(OpCode.OP_LOAD, self._compile_load(False)))

        # OP_STORE = 2
        body.extend(self._check_op(OpCode.OP_STORE, self._compile_store(False)))

        # OP_LOAD_GLOBAL = 5
        body.extend(self._check_op(OpCode.OP_LOAD_GLOBAL, self._compile_load(True)))

        # OP_STORE_GLOBAL = 4
        body.extend(self._check_op(OpCode.OP_STORE_GLOBAL, self._compile_store(True)))

        # OP_JUMP = 19
        body.extend(self._check_op(OpCode.OP_JUMP, self._compile_jump(False)))

        # OP_JUMP_IF_FALSE = 20
        body.extend(self._check_op(OpCode.OP_JUMP_IF_FALSE, self._compile_jump(True)))

        # OP_LIST = 28
        body.extend(self._check_op(OpCode.OP_LIST, self._compile_list_create()))

        # OP_LENGTH = 31
        body.extend(self._check_op(OpCode.OP_LENGTH, self._compile_length()))

        # Default: advance ip by 1
        body.extend(
            _GET_LOCAL(0) + _I32(1) + bytes([OP_I32_ADD]) + _SET_LOCAL(0)  # ip += 1
        )
        body.extend(bytes([OP_BR, 0x00]))  # br $main

        body.extend(bytes([OP_END]))  # end loop
        body.extend(bytes([OP_END]))  # end block
        body.extend(bytes([OP_END]))  # end function

        m.add_code([(1, 'i32'), (1, 'i32'), (1, 'i32'), (1, 'i32'), (1, 'f64'), (1, 'i32'), (1, 'i32'), (1, 'f64')], bytes(body))

        # Datos: store bytecodes as individual bytes (each opcode/arg fits in 1 byte)
        bc_bytes = bytes(int(o) & 0xFF for o in self.bc)
        m.add_data(_I32(BC_BASE), bc_bytes)
        m.add_data(_I32(CONST_BASE), const_bytes)
        if str_bytes:
            m.add_data(_I32(STR_BASE), str_bytes)

        return m.to_bytes()

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

    def _compile_binop(self, wasm_op, result_tag=TAG_NUM, post_op=None):
        """Compila operacion binaria: pop b, pop a, push (tag, a op b)."""
        data_expr = (
            _GET_LOCAL(4) +         # a_data
            _GET_LOCAL(7) +         # b_data
            bytes([wasm_op])        # f64.op (result: f64 for arithmetic, i32 for comparisons)
        )
        if post_op is not None:
            data_expr += bytes([post_op])  # convert i32→f64 if needed
        return (
            pop_instr() +              # pop b: $t(3)=b_tag, $d(4)=b_data
            _GET_LOCAL(3) + _SET_LOCAL(6) +  # $saved_tag = b_tag
            _GET_LOCAL(4) + _SET_LOCAL(7) +  # $saved_data = b_data
            pop_instr() +              # pop a: $t(3)=a_tag, $d(4)=a_data
            push_instr(
                _I32(result_tag),
                data_expr
            )
        )

    def _compile_negate(self):
        return (
            pop_instr() +  # pop: $t=tag, $d=data
            push_instr(
                _I32(TAG_NUM),
                _GET_LOCAL(4) +
                bytes([OP_F64_NEG])
            )
        )

    def _compile_pop_drop(self):
        return pop_instr()  # pop_instr already decrements sp, no need for drop

    def _compile_print(self):
        return (
            pop_instr() +
            # if num: print_num(f64)
            _GET_LOCAL(3) +
            _I32(TAG_NUM) +
            bytes([OP_I32_EQ]) +
            bytes([OP_IF, 0x40]) +
            _GET_LOCAL(4) +
            instr_call(0) +
            bytes([OP_END]) +
            # else if bool: print_bool(i32)
            _GET_LOCAL(3) +
            _I32(TAG_BOOL) +
            bytes([OP_I32_EQ]) +
            bytes([OP_IF, 0x40]) +
            _GET_LOCAL(4) +
            bytes([OP_I32_TRUNC_F64_S]) +
            instr_call(1) +
            bytes([OP_END]) +
            # else if str: print_str(ptr i32, len i32)
            _GET_LOCAL(3) +
            _I32(TAG_STR) +
            bytes([OP_I32_EQ]) +
            bytes([OP_IF, 0x40]) +
            _GET_LOCAL(4) +
            bytes([OP_I32_TRUNC_F64_S]) +
            _I32(0) +
            instr_call(2) +
            bytes([OP_END])
        )

    def _compile_load(self, is_global):
        var_base = 0x8000
        return (
            _GET_LOCAL(0) +
            _I32(1) +
            bytes([OP_I32_ADD]) +
            _LOAD_U8(BC_BASE) +  # var index from bytecode[ip+1] (1 byte)
            _TEE_LOCAL(5) +       # $idx = var index
            _I32(VSLOT) +
            bytes([OP_I32_MUL]) +
            _I32(var_base) +
            bytes([OP_I32_ADD]) +
            _TEE_LOCAL(1) +      # $addr
            _LOAD_I32(0) +       # load tag → pushes i32
            _SET_LOCAL(3) +      # $t = tag
            _GET_LOCAL(1) +
            _LOAD_F64(4) +       # load data → pushes f64
            _SET_LOCAL(4) +      # $d = data
            push_instr(_GET_LOCAL(3), _GET_LOCAL(4)) +
            # advance ip by 2 and br $main
            _GET_LOCAL(0) + _I32(2) + bytes([OP_I32_ADD]) + _SET_LOCAL(0) +
            bytes([OP_BR, 0x01])
        )

    def _compile_store(self, is_global):
        var_base = 0x8000
        return (
            pop_instr() +  # $t, $d = value to store
            _GET_LOCAL(0) +
            _I32(1) +
            bytes([OP_I32_ADD]) +
            _LOAD_U8(BC_BASE) +  # var index from bytecode[ip+1] (1 byte)
            _TEE_LOCAL(5) +
            _I32(VSLOT) +
            bytes([OP_I32_MUL]) +
            _I32(var_base) +
            bytes([OP_I32_ADD]) +
            _TEE_LOCAL(1) +       # $addr
            _GET_LOCAL(3) +
            _STORE_I32(0) +        # store tag
            _GET_LOCAL(1) +
            _GET_LOCAL(4) +
            _STORE_F64(4) +        # store data
            # advance ip by 2 and br $main
            _GET_LOCAL(0) + _I32(2) + bytes([OP_I32_ADD]) + _SET_LOCAL(0) +
            bytes([OP_BR, 0x01])
        )

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

    def _compile_list_create(self):
        return push_instr(_I32(TAG_LIST), _F64(0.0))

    def _compile_length(self):
        return self._compile_pop_drop() + push_instr(_I32(TAG_NUM), _F64(0.0))


def compile_wasm(bytecode, constants, functions, line_map=None):
    compiler = WasmCompiler(bytecode, constants, functions, line_map)
    return compiler.compile()
