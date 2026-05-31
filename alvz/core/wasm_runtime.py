"""
Runtime WASM para Alvz - ejecuta modulos .wasm con host functions completas.
Uso: wasm_runtime.run("archivo.wasm")
"""

import struct
import math
import time
import os
import json
import re
import sqlite3
import ctypes
from datetime import datetime

try:
    import wasmtime
except ImportError:
    wasmtime = None


# Layouts (deben coincidir con wasm_compiler.py)
HOST_BUF_BASE = 0x500
BC_BASE = 0x4000
CONST_BASE = 0x5000
STR_BASE = 0x6000
VAR_BASE = 0x8000
LIST_META = 0xA000
LIST_HEAP = 0xC000
CALL_STACK = 0xE000

TAG_NUM = 0
TAG_BOOL = 1
TAG_STR = 2
TAG_NULL = 3
TAG_LIST = 4
TAG_DICT = 5
TAG_FUNC = 6

# Host opcodes (deben coincidir con wasm_compiler.py)
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


def _read_tag(mem, addr):
    return int.from_bytes(mem[addr:addr+4], 'little', signed=True)

def _read_f64(mem, addr):
    return struct.unpack('<d', mem[addr:addr+8])[0]

def _read_i32(mem, addr):
    return int.from_bytes(mem[addr:addr+4], 'little', signed=True)

def _write_tag(mem, addr, val):
    mem[addr:addr+4] = struct.pack('<i', val)

def _write_f64(mem, addr, val):
    mem[addr:addr+8] = struct.pack('<d', val)

def _write_i32(mem, addr, val):
    mem[addr:addr+4] = struct.pack('<i', val)

def _read_str(mem, offset):
    """Lee string desde STR_BASE: [i32 len][bytes...]"""
    addr = STR_BASE + int(offset)
    length = _read_i32(mem, addr)
    return mem[addr+4:addr+4+length].decode('utf-8', errors='replace')

def _write_str(mem, s):
    """Escribe string a STR_BASE, retorna offset donde se escribio."""
    b = s.encode('utf-8')
    offset = 0
    while offset + 4 + len(b) < 0x2000:
        addr = STR_BASE + offset
        if _read_i32(mem, addr) == 0:
            _write_i32(mem, addr, len(b))
            mem[addr+4:addr+4+len(b)] = b
            return float(offset)
        offset += 1
    return 0.0

def _read_value(mem, buf_addr):
    """Lee (tag, data) desde HOST_BUF_BASE+buf_addr"""
    tag = _read_tag(mem, buf_addr)
    data = _read_f64(mem, buf_addr + 8)
    return tag, data

def _tag_name(tag):
    return {0: 'numero', 1: 'booleano', 2: 'texto', 3: 'nulo', 4: 'lista', 5: 'diccionario'}.get(tag, 'desconocido')


class _MemWrapper:
    """Wrapper que hace que un array ctypes se comporte como bytearray (lectura)."""
    def __init__(self, arr):
        self._arr = arr
    def __getitem__(self, idx):
        if isinstance(idx, slice):
            return bytes(self._arr[idx])
        return self._arr[idx]
    def __setitem__(self, idx, val):
        if isinstance(idx, slice):
            self._arr[idx] = val
        else:
            self._arr[idx] = val


def _get_mem(memory, store):
    """Retorna un wrapper sobre la memoria WASM."""
    if store is None:
        ptr = memory.data_ptr()
    else:
        ptr = memory.data_ptr(store)
    addr = ctypes.cast(ptr, ctypes.c_void_p).value
    arr = (ctypes.c_ubyte * 0x20000).from_address(addr)
    return _MemWrapper(arr)


def make_host_call(memory, output_buffer, store=None):
    """Retorna funcion host_call(i32, i32, i32, i32, i32) -> None"""
    mem = _get_mem(memory, store)

    _output = output_buffer

    # Estado para runtime: clases, instancias, try_stack, etc
    classes = {}
    instances = {}
    next_inst_id = 0

    def read_mem(addr, size):
        return bytes(mem[addr:addr+size])

    def host_call(op_id, nargs, ip, _a3, _a4):
        nonlocal next_inst_id

        # Leer valores de argumento desde HOST_BUF_BASE
        args = []
        for i in range(nargs):
            off = 8 + i * 16
            tag = _read_tag(mem, HOST_BUF_BASE + off)
            data = _read_f64(mem, HOST_BUF_BASE + off + 8)
            args.append((tag, data))

        result_tag = TAG_NULL
        result_data = 0.0
        advance_ip = 0  # 0 = default 1

        raw_ip = ip

        if op_id == HOST_CLEAR:
            advance_ip = 1

        elif op_id == HOST_WAIT:
            time.sleep(args[0][1])
            advance_ip = 1

        elif op_id == HOST_TIME:
            result_tag = TAG_NUM
            result_data = time.time()
            advance_ip = 1

        elif op_id == HOST_ROUND:
            result_tag = TAG_NUM
            result_data = float(round(args[0][1]))
            advance_ip = 1

        elif op_id == HOST_POW:
            result_tag = TAG_NUM
            base, exp = args[0][1], args[1][1]
            result_data = base ** exp
            advance_ip = 1

        elif op_id == HOST_LOWER:
            s = _read_str(mem, args[0][1])
            offset = _write_str(mem, s.lower())
            result_tag = TAG_STR
            result_data = offset
            advance_ip = 1

        elif op_id == HOST_UPPER:
            s = _read_str(mem, args[0][1])
            offset = _write_str(mem, s.upper())
            result_tag = TAG_STR
            result_data = offset
            advance_ip = 1

        elif op_id == HOST_REPLACE:
            texto = _read_str(mem, args[0][1])
            viejo = _read_str(mem, args[1][1])
            nuevo = _read_str(mem, args[2][1])
            offset = _write_str(mem, texto.replace(viejo, nuevo))
            result_tag = TAG_STR
            result_data = offset
            advance_ip = 1

        elif op_id == HOST_TYPE_OF:
            tag, data = args[0]
            type_str = _tag_name(tag)
            offset = _write_str(mem, type_str)
            result_tag = TAG_STR
            result_data = offset
            advance_ip = 1

        elif op_id == HOST_FILE_READ or op_id == HOST_READ_FILE:
            nombre = _read_str(mem, args[0][1])
            try:
                with open(nombre, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                offset = _write_str(mem, contenido)
                result_tag = TAG_STR
                result_data = offset
            except Exception:
                result_tag = TAG_BOOL
                result_data = 0.0
            advance_ip = 1

        elif op_id == HOST_FILE_WRITE or op_id == HOST_WRITE_FILE:
            nombre = _read_str(mem, args[1][1]) if op_id == HOST_WRITE_FILE else _read_str(mem, args[0][1])
            contenido = str(args[0][1]) if op_id == HOST_WRITE_FILE else _read_str(mem, args[1][1])
            try:
                with open(nombre, 'w', encoding='utf-8') as f:
                    f.write(contenido)
                result_tag = TAG_BOOL
                result_data = 1.0
            except Exception:
                result_tag = TAG_BOOL
                result_data = 0.0
            advance_ip = 1

        elif op_id == HOST_WEB_SEND:
            url_tag, url_data = args[1] if len(args) > 1 else (TAG_NULL, 0.0)
            datos_tag, datos_data = args[0]
            url = _read_str(mem, url_data) if url_tag == TAG_STR else str(url_data)
            try:
                import requests
                payload = {"data": datos_data} if datos_tag != TAG_LIST else []
                response = requests.post(url, json=payload, timeout=10)
                result_tag = TAG_NUM
                result_data = float(response.status_code)
            except Exception:
                result_tag = TAG_NUM
                result_data = 0.0
            advance_ip = 1

        elif op_id == HOST_HTTP_REQUEST:
            metodo_tag, metodo_data = args[0]
            url_tag, url_data = args[1]
            datos_tag, datos_data = args[2]
            metodo = _read_str(mem, metodo_data) if metodo_tag == TAG_STR else str(metodo_data)
            url = _read_str(mem, url_data) if url_tag == TAG_STR else str(url_data)
            try:
                import requests
                metodo = metodo.upper()
                if metodo == "GET":
                    resp = requests.get(url, timeout=30)
                elif metodo == "POST":
                    resp = requests.post(url, json={"data": datos_data}, timeout=30)
                elif metodo == "PUT":
                    resp = requests.put(url, json={"data": datos_data}, timeout=30)
                elif metodo == "DELETE":
                    resp = requests.delete(url, timeout=30)
                else:
                    resp = None
                if resp is not None:
                    result_dict = json.dumps({"codigo": resp.status_code, "cuerpo": resp.text})
                    offset = _write_str(mem, result_dict)
                    result_tag = TAG_STR
                    result_data = offset
                else:
                    result_tag = TAG_STR
                    result_data = _write_str(mem, json.dumps({"codigo": 0, "cuerpo": "", "error": f"Metodo no soportado: {metodo}"}))
            except Exception as e:
                result_tag = TAG_STR
                result_data = _write_str(mem, json.dumps({"codigo": 0, "cuerpo": "", "error": str(e)}))
            advance_ip = 1

        elif op_id == HOST_JSON_ENCODE:
            val = args[0][1]
            try:
                offset = _write_str(mem, json.dumps(val))
            except Exception:
                offset = _write_str(mem, "null")
            result_tag = TAG_STR
            result_data = offset
            advance_ip = 1

        elif op_id == HOST_JSON_DECODE:
            s = _read_str(mem, args[0][1])
            try:
                decoded = json.loads(s)
                if isinstance(decoded, bool):
                    result_tag = TAG_BOOL
                    result_data = 1.0 if decoded else 0.0
                elif isinstance(decoded, (int, float)):
                    result_tag = TAG_NUM
                    result_data = float(decoded)
                elif isinstance(decoded, str):
                    result_tag = TAG_STR
                    result_data = _write_str(mem, decoded)
                elif isinstance(decoded, (list, dict)):
                    offset = _write_str(mem, json.dumps(decoded))
                    result_tag = TAG_STR
                    result_data = offset
                else:
                    result_tag = TAG_NULL
                    result_data = 0.0
            except Exception:
                result_tag = TAG_NULL
                result_data = 0.0
            advance_ip = 1

        elif op_id == HOST_SQLITE_OPEN:
            ruta = _read_str(mem, args[0][1])
            try:
                conn_id = next_inst_id
                next_inst_id += 1
                instances[str(conn_id)] = sqlite3.connect(ruta)
                result_tag = TAG_NUM
                result_data = float(conn_id)
            except Exception as e:
                result_tag = TAG_STR
                result_data = _write_str(mem, json.dumps({"error": str(e)}))
            advance_ip = 1

        elif op_id == HOST_SQLITE_EXEC:
            conn_id = int(args[1][1]) if len(args) > 1 else 0
            sql = _read_str(mem, args[0][1])
            conn = instances.get(str(conn_id))
            if conn is None:
                result_tag = TAG_NUM
                result_data = 0.0
            else:
                try:
                    cursor = conn.execute(sql)
                    conn.commit()
                    result_tag = TAG_NUM
                    result_data = float(cursor.rowcount)
                except Exception as e:
                    result_tag = TAG_NUM
                    result_data = 0.0
            advance_ip = 1

        elif op_id == HOST_SQLITE_QUERY:
            conn_id = int(args[1][1]) if len(args) > 1 else 0
            sql = _read_str(mem, args[0][1])
            conn = instances.get(str(conn_id))
            if conn is None:
                result_tag = TAG_STR
                result_data = _write_str(mem, "[]")
            else:
                try:
                    cursor = conn.execute(sql)
                    cols = [desc[0] for desc in cursor.description]
                    rows = [dict(zip(cols, row)) for row in cursor.fetchall()]
                    offset = _write_str(mem, json.dumps(rows))
                    result_tag = TAG_STR
                    result_data = offset
                except Exception:
                    result_tag = TAG_STR
                    result_data = _write_str(mem, "[]")
            advance_ip = 1

        elif op_id == HOST_SUPABASE_INSERT:
            url = _read_str(mem, args[3][1]) if args[3][0] == TAG_STR else str(args[3][1])
            key = _read_str(mem, args[2][1]) if args[2][0] == TAG_STR else str(args[2][1])
            tabla = _read_str(mem, args[1][1]) if args[1][0] == TAG_STR else str(args[1][1])
            datos = args[0][1]
            try:
                import requests
                full_url = f"{url}/rest/v1/{tabla}"
                headers = {
                    "apikey": key,
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal",
                }
                payload = [datos] if isinstance(datos, dict) else datos
                response = requests.post(full_url, headers=headers, json=payload, timeout=10)
                result_tag = TAG_NUM
                result_data = float(response.status_code)
            except Exception:
                result_tag = TAG_NUM
                result_data = 0.0
            advance_ip = 1

        elif op_id == HOST_SUPABASE_SELECT:
            url = _read_str(mem, args[2][1]) if args[2][0] == TAG_STR else str(args[2][1])
            key = _read_str(mem, args[1][1]) if args[1][0] == TAG_STR else str(args[1][1])
            tabla = _read_str(mem, args[0][1]) if args[0][0] == TAG_STR else str(args[0][1])
            try:
                import requests
                full_url = f"{url}/rest/v1/{tabla}"
                headers = {
                    "apikey": key,
                    "Authorization": f"Bearer {key}",
                }
                response = requests.get(full_url, headers=headers, timeout=10)
                offset = _write_str(mem, json.dumps(response.json()))
                result_tag = TAG_STR
                result_data = offset
            except Exception:
                result_tag = TAG_STR
                result_data = _write_str(mem, "[]")
            advance_ip = 1

        elif op_id == HOST_DATE_FORMAT:
            fmt = _read_str(mem, args[0][1]) if args[0][0] == TAG_STR else str(args[0][1])
            try:
                offset = _write_str(mem, datetime.now().strftime(fmt))
            except Exception:
                offset = _write_str(mem, str(datetime.now()))
            result_tag = TAG_STR
            result_data = offset
            advance_ip = 1

        elif op_id == HOST_STRING_SPLIT:
            texto = _read_str(mem, args[1][1]) if args[1][0] == TAG_STR else str(args[1][1])
            sep = _read_str(mem, args[0][1]) if args[0][0] == TAG_STR else str(args[0][1])
            parts = texto.split(sep)
            offset = _write_str(mem, json.dumps(parts))
            result_tag = TAG_STR
            result_data = offset
            advance_ip = 1

        elif op_id == HOST_STRING_JOIN:
            lst_str = _read_str(mem, args[1][1]) if args[1][0] == TAG_STR else str(args[1][1])
            sep = _read_str(mem, args[0][1]) if args[0][0] == TAG_STR else str(args[0][1])
            try:
                lst = json.loads(lst_str)
                joined = sep.join(str(x) for x in lst)
            except Exception:
                joined = ""
            offset = _write_str(mem, joined)
            result_tag = TAG_STR
            result_data = offset
            advance_ip = 1

        elif op_id == HOST_TO_NUMBER:
            tag, data = args[0]
            if tag in (TAG_NUM, TAG_BOOL):
                result_tag = TAG_NUM
                result_data = data
            elif tag == TAG_STR:
                s = _read_str(mem, data)
                try:
                    result_tag = TAG_NUM
                    result_data = float(s) if '.' in s else int(s)
                except ValueError:
                    result_tag = TAG_NULL
                    result_data = 0.0
            else:
                result_tag = TAG_NULL
                result_data = 0.0
            advance_ip = 1

        elif op_id == HOST_REGEX_SEARCH:
            texto = _read_str(mem, args[1][1]) if args[1][0] == TAG_STR else str(args[1][1])
            patron = _read_str(mem, args[0][1]) if args[0][0] == TAG_STR else str(args[0][1])
            matches = re.findall(patron, texto)
            offset = _write_str(mem, json.dumps(matches))
            result_tag = TAG_STR
            result_data = offset
            advance_ip = 1

        elif op_id == HOST_GET_OUTPUT:
            joined = "\n".join(_output)
            offset = _write_str(mem, joined)
            result_tag = TAG_STR
            result_data = offset
            advance_ip = 1

        elif op_id == HOST_INPUT_NUM:
            try:
                val = float(input("> "))
                result_tag = TAG_NUM
                result_data = val
            except ValueError:
                result_tag = TAG_NULL
                result_data = 0.0
            advance_ip = 1

        elif op_id == HOST_IMPORT:
            advance_ip = 1

        elif op_id == HOST_CLASS:
            # Leer constantes del bytecode
            const_name_idx = _read_i32(mem, BC_BASE + raw_ip + 1)
            # Leer constantes desde CONST_BASE
            name_tag = _read_tag(mem, CONST_BASE + const_name_idx * 12)
            name_data = _read_f64(mem, CONST_BASE + const_name_idx * 12)
            class_name = _read_str(mem, name_data) if name_tag == TAG_STR else str(name_data)
            classes[class_name] = True
            result_tag = TAG_NULL
            result_data = 0.0
            advance_ip = 3

        elif op_id == HOST_NEW:
            class_name_tag, class_name_data = args[0]
            class_name = _read_str(mem, class_name_data) if class_name_tag == TAG_STR else str(class_name_data)
            inst_id = next_inst_id
            next_inst_id += 1
            instances[str(inst_id)] = {"_clase": class_name}
            result_tag = TAG_NUM
            result_data = float(inst_id)
            advance_ip = 2

        elif op_id == HOST_GET_ATTR:
            prop_tag, prop_data = args[0]
            obj_tag, obj_data = args[1]
            prop_name = _read_str(mem, prop_data) if prop_tag == TAG_STR else str(prop_data)
            inst = instances.get(str(int(obj_data)))
            if inst and isinstance(inst, dict) and prop_name in inst:
                val = inst[prop_name]
                if isinstance(val, str):
                    result_tag = TAG_STR
                    result_data = _write_str(mem, val)
                elif isinstance(val, bool):
                    result_tag = TAG_BOOL
                    result_data = 1.0 if val else 0.0
                elif isinstance(val, (int, float)):
                    result_tag = TAG_NUM
                    result_data = float(val)
                else:
                    result_tag = TAG_NULL
                    result_data = 0.0
            else:
                result_tag = TAG_NULL
                result_data = 0.0
            advance_ip = 1

        elif op_id == HOST_SET_ATTR:
            prop_tag, prop_data = args[0]
            val_tag, val_data = args[1]
            obj_tag, obj_data = args[2]
            prop_name = _read_str(mem, prop_data) if prop_tag == TAG_STR else str(prop_data)
            inst = instances.get(str(int(obj_data)))
            if inst and isinstance(inst, dict):
                if val_tag == TAG_STR:
                    inst[prop_name] = _read_str(mem, val_data)
                elif val_tag == TAG_BOOL:
                    inst[prop_name] = bool(val_data)
                elif val_tag == TAG_NUM:
                    inst[prop_name] = val_data
                else:
                    inst[prop_name] = None
            advance_ip = 1

        elif op_id == HOST_SUPER_ATTR:
            advance_ip = 1
            result_tag = TAG_NULL
            result_data = 0.0

        elif op_id == HOST_INSTANCEOF:
            result_tag = TAG_BOOL
            result_data = 0.0
            advance_ip = 1

        elif op_id == HOST_TRY_PUSH:
            advance_ip = 2

        elif op_id == HOST_TRY_POP:
            advance_ip = 1

        elif op_id == HOST_THROW:
            advance_ip = 1
            result_tag = TAG_NULL
            result_data = 0.0

        elif op_id == HOST_ERROR_MSG:
            result_tag = TAG_STR
            result_data = _write_str(mem, "")
            advance_ip = 1

        elif op_id == HOST_ASYNC_CALL:
            advance_ip = 3
            result_tag = TAG_NULL
            result_data = 0.0

        elif op_id == HOST_AWAIT:
            advance_ip = 1
            result_tag = TAG_NULL
            result_data = 0.0

        elif op_id == HOST_SQRT:
            result_tag = TAG_NUM
            result_data = math.sqrt(args[0][1])
            advance_ip = 1

        elif op_id == HOST_ABS:
            result_tag = TAG_NUM
            result_data = abs(args[0][1])
            advance_ip = 1

        # Escribir resultado al buffer
        _write_tag(mem, HOST_BUF_BASE, result_tag)
        _write_f64(mem, HOST_BUF_BASE + 8, result_data)
        _write_i32(mem, HOST_BUF_BASE + 16, advance_ip)

    return host_call


def run(wasm_path, output_buffer=None):
    """Ejecuta un modulo .wasm de Alvz con wasmtime.
    
    Args:
        wasm_path: Ruta al archivo .wasm
        output_buffer: Lista opcional para capturar salida de print
    
    Returns: True si la ejecucion fue exitosa
    """
    if wasmtime is None:
        print("Error: wasmtime no instalado. pip install wasmtime")
        return False

    if output_buffer is None:
        output_buffer = []

    with open(wasm_path, 'rb') as f:
        wasm_bytes = f.read()

    engine = wasmtime.Engine()
    module = wasmtime.Module(engine, wasm_bytes)
    linker = wasmtime.Linker(engine)
    store = wasmtime.Store(engine)

    # Crear memoria
    memory = wasmtime.Memory(store, wasmtime.MemoryType(wasmtime.Limits(2, None)))
    linker.define(store, 'alvz', 'memory', memory)

    # Host functions
    def print_num(val):
        output_buffer.append(str(val))
    def print_bool(val):
        output_buffer.append("verdadero" if val else "falso")
    def print_str(ptr, length):
        mem = _get_mem(memory, store)
        s = bytes(mem[ptr:ptr+length]).decode('utf-8', errors='replace')
        output_buffer.append(s)
    def random_range(min_val, max_val):
        import random
        return random.uniform(min_val, max_val)
    def input_num():
        try:
            return float(input("> "))
        except ValueError:
            return 0.0

    host_call = make_host_call(memory, output_buffer, store)

    linker.define(store, 'alvz', 'print_num', wasmtime.Func(store, wasmtime.FuncType([wasmtime.ValType.f64()], []), print_num))
    linker.define(store, 'alvz', 'print_bool', wasmtime.Func(store, wasmtime.FuncType([wasmtime.ValType.i32()], []), print_bool))
    linker.define(store, 'alvz', 'print_str', wasmtime.Func(store, wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32()], []), print_str))
    linker.define(store, 'alvz', 'random_range', wasmtime.Func(store, wasmtime.FuncType([wasmtime.ValType.f64(), wasmtime.ValType.f64()], [wasmtime.ValType.f64()]), random_range))
    linker.define(store, 'alvz', 'input_num', wasmtime.Func(store, wasmtime.FuncType([], [wasmtime.ValType.f64()]), input_num))
    linker.define(store, 'alvz_host', 'call', wasmtime.Func(store, wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32(), wasmtime.ValType.i32()], []), host_call))

    instance = linker.instantiate(store, module)
    main_func = instance.exports(store)['main']
    main_func(store)

    return True
