"""
Maquina Virtual de Alvz - Ejecutor de bytecode basado en pila.
"""

import random
import os
import time
import threading
import concurrent.futures
import requests
import json
import sqlite3

from .bytecode import OpCode

try:
    from fastapi import FastAPI, Request
    import uvicorn
except ImportError:
    FastAPI = None
    Request = None
    uvicorn = None


class Coroutine:
    def __init__(self, func_addr, args, vm=None, name='<coro>'):
        self.func_addr = func_addr
        self.args = args
        self.vm = vm
        self.name = name
        self.result = None
        self.state = 'pending'
        self.exception = None
        self._future = None


class EventLoop:
    def __init__(self):
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=8)
        self._futures = []

    def start_coroutine(self, coro, bytecode, constants, line_map, functions, globals_data, classes_data, output_buffer):
        def _run():
            try:
                vm = VM(bytecode, constants, line_map, functions)
                vm.globals = globals_data
                vm.classes = classes_data
                vm.frames = [{'return_ip': len(vm.bytecode), 'locals': {i: v for i, v in enumerate(coro.args)}}]
                vm.ip = coro.func_addr
                vm.run(output_buffer=output_buffer)
                coro.result = vm.stack[-1] if vm.stack else None
                coro.state = 'completed'
            except Exception as e:
                coro.exception = e
                coro.state = 'completed'

        coro._future = self._executor.submit(_run)
        self._futures.append(coro._future)
        return coro._future

    def await_coroutine(self, coro):
        if coro._future is None or not coro._future.running():
            for f in concurrent.futures.as_completed([coro._future]):
                pass
        else:
            coro._future.result()
        if coro.exception:
            raise coro.exception
        return coro.result

    def shutdown(self):
        self._executor.shutdown(wait=False)


class VM:
    """Motor de ejecucion basado en pila."""

    def __init__(self, bytecode, constants, line_map=None, functions=None, source_lines=None):
        self.bytecode = bytecode
        self.constants = constants
        self.line_map = line_map or {}
        self.source_lines = source_lines or []
        self.functions = functions or {}
        self.stack = []
        self.globals = {}
        self.frames = []
        self.ip = 0
        self.output_buffer = []
        self.exception_stack = []
        self.classes = {}
        self.last_error = ""

        self._print_lock = threading.Lock()
        self.classes = {}
        self.last_error = ""

    def _build_stack_trace(self, current_ip):
        lines = []
        frames_rev = list(reversed(self.frames))
        for i, frame in enumerate(frames_rev):
            func_name = frame.get('func_name', '<modulo principal>')
            if i == 0:
                ip = current_ip
            elif 'call_ip' in frame:
                ip = frame['call_ip']
            else:
                ip = frame.get('return_ip', current_ip)
            linea = self.line_map.get(ip, '?') if ip >= 0 else '?'
            src = ""
            if isinstance(linea, int) and linea > 0 and linea <= len(self.source_lines):
                src_line = self.source_lines[linea - 1].strip()
                if src_line:
                    src = f"  └─ {src_line}"
            lines.append(f"  {i+1}. {func_name} (linea {linea})")
            if src:
                lines.append(src)
        return '\n'.join(lines)

    def _find_getter(self, class_name, prop_name, visited=None):
        if visited is None:
            visited = set()
        if class_name in visited:
            return None
        visited.add(class_name)
        if class_name not in self.classes:
            return None
        c_info = self.classes[class_name]
        if prop_name in c_info.get('getters', {}):
            return c_info['getters'][prop_name]
        if c_info.get('parent'):
            return self._find_getter(c_info['parent'], prop_name, visited)
        return None

    def _find_setter(self, class_name, prop_name, visited=None):
        if visited is None:
            visited = set()
        if class_name in visited:
            return None
        visited.add(class_name)
        if class_name not in self.classes:
            return None
        c_info = self.classes[class_name]
        if prop_name in c_info.get('setters', {}):
            return c_info['setters'][prop_name]
        if c_info.get('parent'):
            return self._find_setter(c_info['parent'], prop_name, visited)
        return None

    @staticmethod
    def _tipo_str(val):
        if val is None:
            return "nulo"
        if isinstance(val, bool):
            return "booleano"
        if isinstance(val, (int, float)):
            return "numero"
        if isinstance(val, str):
            return "texto"
        if isinstance(val, list):
            return "lista"
        if isinstance(val, dict):
            return "diccionario"
        if isinstance(val, tuple):
            return "funcion"
        return type(val).__name__

    def _check_numeric(self, val, op_name="operacion"):
        if not isinstance(val, (int, float)):
            raise RuntimeError(
                f"Error de tipo: Se esperaba un numero para {op_name}, "
                f"pero se encontro {self._tipo_str(val)}"
            )

    def _check_string(self, val, op_name="operacion"):
        if not isinstance(val, str):
            raise RuntimeError(
                f"Error de tipo: Se esperaba un texto para {op_name}, "
                f"pero se encontro {self._tipo_str(val)}"
            )

    def _check_two_numeric(self, a, b, op_name="operacion"):
        self._check_numeric(a, op_name)
        self._check_numeric(b, op_name)

    def _import_file(self, filename):
        from alvz.core.lexer import Lexer
        from alvz.core.parser import Parser

        import os

        paths_to_try = [filename]
        if not filename.endswith('.alvz'):
            paths_to_try.append(filename + '.alvz')
        stdlib_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'stdlib')
        paths_to_try.append(os.path.join(stdlib_dir, filename))
        if not filename.endswith('.alvz'):
            paths_to_try.append(os.path.join(stdlib_dir, filename + '.alvz'))

        # Search installed packages
        try:
            from alvz.core.package_manager import PACKAGES_DIR
            pkg_entry = os.path.join(PACKAGES_DIR, filename, f"{filename}.alvz")
            paths_to_try.append(pkg_entry)
        except Exception:
            pass

        imported_code = None
        for p in paths_to_try:
            try:
                with open(p, 'r', encoding='utf-8-sig') as f:
                    imported_code = f.read()
                    break
            except Exception:
                continue

        if imported_code is None:
            raise RuntimeError(f"Error al importar '{filename}': archivo no encontrado")

        lexer = Lexer(imported_code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        parser.functions = self.functions
        parser.global_symbols = self.globals
        parser.symbols = parser.global_symbols
        parser.constants = self.constants

        bytecode, constants, line_map, funcs = parser.compile()

        if bytecode and bytecode[-1] == OpCode.OP_HALT:
            bytecode = bytecode[:-1]

        if not bytecode:
            return

        # Registrar funciones
        for name, finfo in funcs.items():
            if len(finfo) >= 4:
                addr, nargs, params, is_async = finfo
            else:
                addr, nargs, params = finfo
            self.functions[name] = (addr, nargs, params)

        # Ejecutar bytecode inline con save/restore
        old_ip = self.ip
        old_bytecode = self.bytecode
        old_line_map = self.line_map
        old_frames = self.frames[:]
        old_stack = self.stack[:]

        self.frames = [{'return_ip': -1, 'locals': {}}]
        self.stack = []
        self.bytecode = bytecode
        self.line_map = line_map
        self.ip = 0

        try:
            self.run()
        finally:
            self.ip = old_ip
            self.bytecode = old_bytecode
            self.line_map = old_line_map
            self.frames = old_frames
            self.stack = old_stack

    def run(self, output_buffer=None):
        if output_buffer is not None:
            self.output_buffer = output_buffer
        else:
            self.output_buffer = []
        self.exception_stack = []
        if not self.frames:
            self.frames.append({'return_ip': -1, 'locals': {}})

        while self.ip < len(self.bytecode):
            current_ip = self.ip
            if hasattr(self, '_debug_hook') and self._debug_hook:
                self._debug_hook(current_ip, self)
            try:
                op = self.bytecode[self.ip]
                self.ip += 1

                frame = self.frames[-1]
                locals = frame['locals']

                if op == OpCode.OP_CONSTANT:
                    idx = self.bytecode[self.ip]
                    self.ip += 1
                    self.stack.append(self.constants[idx])

                elif op == OpCode.OP_STORE:
                    var_idx = self.bytecode[self.ip]
                    self.ip += 1
                    val = self.stack.pop() if self.stack else False
                    locals[var_idx] = val

                elif op == OpCode.OP_LOAD:
                    var_idx = self.bytecode[self.ip]
                    self.ip += 1
                    self.stack.append(locals.get(var_idx, False))

                elif op == OpCode.OP_STORE_GLOBAL:
                    var_idx = self.bytecode[self.ip]
                    self.ip += 1
                    val = self.stack.pop() if self.stack else False
                    self.globals[var_idx] = val

                elif op == OpCode.OP_LOAD_GLOBAL:
                    var_idx = self.bytecode[self.ip]
                    self.ip += 1
                    self.stack.append(self.globals.get(var_idx, False))

                elif op == OpCode.OP_CALL:
                    func_addr = self.bytecode[self.ip]
                    num_args = self.bytecode[self.ip + 1]

                    new_locals = {}
                    args_values = []
                    for _ in range(num_args):
                        args_values.append(self.stack.pop())
                    args_values.reverse()

                    target_addr = func_addr

                    if func_addr == 0 and self.stack:
                        target = self.stack.pop()
                        if isinstance(target, tuple):
                            if target[0] == 'METODO':
                                _, method_addr, expected_params, instance = target
                                target_addr = method_addr
                                args_values.insert(0, instance)
                            elif target[0] == 'FUNC':
                                _, target_addr, _ = target
                            elif target[0] == 'FUNC_NAME':
                                fname = target[1]
                                if fname in self.functions:
                                    target_addr = self.functions[fname][0]
                                else:
                                    raise RuntimeError(f"Error: La funcion '{fname}' no existe")

                    for i, val in enumerate(args_values):
                        new_locals[i] = val

                    # call_ip es la direccion del OP_CALL (actual ip - 1 porque ip ya avanzo)
                    call_ip = self.ip - 1

                    self.ip += 3

                    # Buscar nombre de funcion para stack trace
                    func_name = '<anonimo>'
                    for fname, finfo in self.functions.items():
                        addr = finfo[0]
                        if addr == target_addr:
                            func_name = fname
                            break

                    self.frames.append({
                        'return_ip': self.ip,
                        'locals': new_locals,
                        'func_name': func_name,
                        'call_ip': call_ip,
                    })
                    self.ip = target_addr

                elif op == OpCode.OP_RETURN:
                    if len(self.frames) > 1:
                        last_frame = self.frames.pop()
                        self.ip = last_frame['return_ip']
                        if last_frame.get('_is_constructor'):
                            pending = getattr(self, '_pending_instance', None)
                            if pending is not None:
                                self.stack.append(pending)
                                self._pending_instance = None
                        if hasattr(self, '_init_chain') and self._init_chain:
                            inst = self._init_chain['instance']
                            args = self._init_chain['args']
                            cn = self._init_chain['class_name']
                            addr = self._init_chain['next_addr']
                            self._init_chain = None
                            new_locals = {0: inst}
                            for i, val in enumerate(args):
                                new_locals[i + 1] = val
                            self.frames.append({
                                'return_ip': self.ip,
                                'locals': new_locals,
                                'func_name': f'{cn}.inicializar',
                                'call_ip': self.ip - 1,
                            })
                            self.ip = addr
                    else:
                        break

                elif op == OpCode.OP_PRINT:
                    if self.stack:
                        value = self.stack.pop()
                        output = str(value) if value is not None else "nulo"
                        if not hasattr(self, '_print_lock'):
                            self._print_lock = threading.Lock()
                        with self._print_lock:
                            self.output_buffer.append(output)
                            print(output)
                    else:
                        print("Error: Intento de imprimir desde pila vacia")

                elif op == OpCode.OP_ADD:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    if isinstance(a, str) or isinstance(b, str):
                        self.stack.append(str(a) + str(b))
                    else:
                        self.stack.append(a + b)

                elif op == OpCode.OP_SUB:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self._check_two_numeric(a, b, "resta")
                    self.stack.append(a - b)

                elif op == OpCode.OP_MUL:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self._check_two_numeric(a, b, "multiplicacion")
                    self.stack.append(a * b)

                elif op == OpCode.OP_DIV:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self._check_two_numeric(a, b, "division")
                    if b == 0:
                        raise RuntimeError("Division por cero")
                    self.stack.append(a / b)

                elif op == OpCode.OP_MOD:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self._check_two_numeric(a, b, "modulo")
                    self.stack.append(a % b)

                elif op == OpCode.OP_EQ:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self.stack.append(a == b)

                elif op == OpCode.OP_NE:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self.stack.append(a != b)

                elif op == OpCode.OP_GT:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    if isinstance(a, str) and isinstance(b, str):
                        self.stack.append(a > b)
                    else:
                        self._check_two_numeric(a, b, "comparacion mayor")
                        self.stack.append(a > b)

                elif op == OpCode.OP_LT:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    if isinstance(a, str) and isinstance(b, str):
                        self.stack.append(a < b)
                    else:
                        self._check_two_numeric(a, b, "comparacion menor")
                        self.stack.append(a < b)

                elif op == OpCode.OP_GTE:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    if isinstance(a, str) and isinstance(b, str):
                        self.stack.append(a >= b)
                    else:
                        self._check_two_numeric(a, b, "comparacion mayor o igual")
                        self.stack.append(a >= b)

                elif op == OpCode.OP_LTE:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    if isinstance(a, str) and isinstance(b, str):
                        self.stack.append(a <= b)
                    else:
                        self._check_two_numeric(a, b, "comparacion menor o igual")
                        self.stack.append(a <= b)

                elif op == OpCode.OP_AND:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self.stack.append(bool(a) and bool(b))

                elif op == OpCode.OP_OR:
                    b = self.stack.pop()
                    a = self.stack.pop()
                    self.stack.append(bool(a) or bool(b))

                elif op == OpCode.OP_JUMP:
                    target = self.bytecode[self.ip]
                    self.ip = target

                elif op == OpCode.OP_JUMP_IF_FALSE:
                    target = self.bytecode[self.ip]
                    self.ip += 1
                    condition = self.stack.pop()
                    if not condition:
                        self.ip = target

                elif op == OpCode.OP_INPUT:
                    user_input = input("> ")
                    try:
                        if '.' in user_input:
                            value = float(user_input)
                        else:
                            value = int(user_input)
                    except ValueError:
                        value = user_input
                    self.stack.append(value)

                elif op == OpCode.OP_INPUT_NUM:
                    while True:
                        user_input = input("> ")
                        try:
                            if '.' in user_input:
                                value = float(user_input)
                            else:
                                value = int(user_input)
                            self.stack.append(value)
                            break
                        except ValueError:
                            print("Error: Por favor, ingresa un numero valido.")

                elif op == OpCode.OP_RANDOM:
                    max_val = self.stack.pop()
                    min_val = self.stack.pop()
                    self.stack.append(random.randint(int(min_val), int(max_val)))

                elif op == OpCode.OP_CLEAR:
                    os.system('cls' if os.name == 'nt' else 'clear')

                elif op == OpCode.OP_NEGATE:
                    val = self.stack.pop()
                    self._check_numeric(val, "negacion")
                    self.stack.append(-val)

                elif op == OpCode.OP_MAKE_FUNC:
                    func_addr = self.bytecode[self.ip]
                    num_params = self.bytecode[self.ip + 1]
                    self.ip += 2
                    self.stack.append(('FUNC', func_addr, num_params))

                elif op == OpCode.OP_POP:
                    if self.stack:
                        self.stack.pop()

                elif op == OpCode.OP_LIST:
                    num_elements = self.bytecode[self.ip]
                    self.ip += 1
                    elements = []
                    for _ in range(num_elements):
                        elements.append(self.stack.pop())
                    elements.reverse()
                    self.stack.append(elements)

                elif op == OpCode.OP_GET_INDEX:
                    index = self.stack.pop()
                    obj = self.stack.pop()
                    if isinstance(obj, dict):
                        try:
                            self.stack.append(obj[index])
                        except KeyError:
                            self.stack.append(None)
                    elif isinstance(obj, (list, str)):
                        try:
                            self.stack.append(obj[int(index)])
                        except IndexError:
                            raise RuntimeError(f"Indice {index} fuera de rango")
                    else:
                        raise RuntimeError(
                            f"Se esperaba una lista, texto o diccionario, pero se encontro {type(obj).__name__}"
                        )

                elif op == OpCode.OP_SET_INDEX:
                    val = self.stack.pop()
                    index = self.stack.pop()
                    obj = self.stack.pop()
                    if isinstance(obj, dict):
                        obj[index] = val
                    elif isinstance(obj, list):
                        try:
                            obj[int(index)] = val
                        except IndexError:
                            raise RuntimeError(f"Indice {index} fuera de rango")
                    else:
                        raise RuntimeError(
                            f"Se esperaba una lista o diccionario, pero se encontro {type(obj).__name__}"
                        )

                elif op == OpCode.OP_LENGTH:
                    lst = self.stack.pop()
                    if not isinstance(lst, (list, str, dict)):
                        raise RuntimeError("'longitud' solo funciona con listas, textos o diccionarios")
                    self.stack.append(len(lst))

                elif op == OpCode.OP_APPEND:
                    val = self.stack.pop()
                    lst = self.stack.pop()
                    if not isinstance(lst, list):
                        raise RuntimeError("'agregar' solo funciona con listas")
                    lst.append(val)
                    self.stack.append(lst)

                elif op == OpCode.OP_WAIT:
                    segundos = self.stack.pop()
                    time.sleep(float(segundos))

                elif op == OpCode.OP_WEB_SEND:
                    datos_val = self.stack.pop()
                    url_val = self.stack.pop()
                    try:
                        payload = (
                            {"data": datos_val}
                            if not isinstance(datos_val, list)
                            else datos_val
                        )
                        response = requests.post(url_val, json=payload, timeout=10)
                        self.stack.append(response.status_code)
                    except Exception:
                        self.stack.append(0)

                elif op == OpCode.OP_READ_FILE:
                    nombre = self.stack.pop()
                    try:
                        with open(nombre, 'r', encoding='utf-8') as f:
                            contenido = f.read()
                        self.stack.append(contenido)
                    except Exception:
                        self.stack.append(False)

                elif op == OpCode.OP_WRITE_FILE:
                    contenido = self.stack.pop()
                    nombre = self.stack.pop()
                    try:
                        with open(nombre, 'w', encoding='utf-8') as f:
                            f.write(str(contenido))
                        self.stack.append(True)
                    except Exception:
                        self.stack.append(False)

                elif op == OpCode.OP_LOWER:
                    val = self.stack.pop()
                    self._check_string(val, "minusculas")
                    self.stack.append(val.lower())

                elif op == OpCode.OP_UPPER:
                    val = self.stack.pop()
                    self._check_string(val, "mayusculas")
                    self.stack.append(val.upper())

                elif op == OpCode.OP_GET_OUTPUT:
                    self.stack.append("\n".join(self.output_buffer))

                elif op == OpCode.OP_DICT:
                    num_pairs = self.bytecode[self.ip]
                    self.ip += 1
                    d = {}
                    pairs = []
                    for _ in range(num_pairs):
                        val = self.stack.pop()
                        key = self.stack.pop()
                        pairs.append((key, val))
                    pairs.reverse()
                    for k, v in pairs:
                        d[k] = v
                    self.stack.append(d)

                elif op == OpCode.OP_SUPABASE_INSERT:
                    datos = self.stack.pop()
                    tabla = self.stack.pop()
                    key = self.stack.pop()
                    url = self.stack.pop()
                    full_url = f"{url}/rest/v1/{tabla}"
                    headers = {
                        "apikey": key,
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json",
                        "Prefer": "return=minimal",
                    }
                    try:
                        payload = [datos] if isinstance(datos, dict) else datos
                        response = requests.post(full_url, headers=headers, json=payload, timeout=10)
                        self.stack.append(response.status_code)
                    except Exception:
                        self.stack.append(0)

                elif op == OpCode.OP_ROUND:
                    val = self.stack.pop()
                    self._check_numeric(val, "redondear")
                    self.stack.append(round(val))

                elif op == OpCode.OP_POW:
                    exp = self.stack.pop()
                    base = self.stack.pop()
                    self._check_two_numeric(base, exp, "potencia")
                    self.stack.append(base ** exp)

                elif op == OpCode.OP_SQRT:
                    val = self.stack.pop()
                    self._check_numeric(val, "raiz")
                    self.stack.append(val ** 0.5)

                elif op == OpCode.OP_TIME:
                    self.stack.append(time.time())

                elif op == OpCode.OP_JSON_ENCODE:
                    val = self.stack.pop()
                    self.stack.append(json.dumps(val))

                elif op == OpCode.OP_JSON_DECODE:
                    val = self.stack.pop()
                    self.stack.append(json.loads(str(val)))

                elif op == OpCode.OP_TYPE:
                    val = self.stack.pop()
                    if val is None:
                        self.stack.append("nulo")
                    elif isinstance(val, bool):
                        self.stack.append("booleano")
                    elif isinstance(val, (int, float)):
                        self.stack.append("numero")
                    elif isinstance(val, str):
                        self.stack.append("texto")
                    elif isinstance(val, list):
                        self.stack.append("lista")
                    elif isinstance(val, dict):
                        self.stack.append("diccionario")
                    else:
                        self.stack.append("desconocido")

                elif op == OpCode.OP_REPLACE:
                    nuevo = self.stack.pop()
                    viejo = self.stack.pop()
                    texto = self.stack.pop()
                    self._check_string(texto, "reemplazar")
                    self._check_string(viejo, "reemplazar")
                    self._check_string(nuevo, "reemplazar")
                    self.stack.append(texto.replace(viejo, nuevo))

                elif op == OpCode.OP_ABS:
                    val = self.stack.pop()
                    self._check_numeric(val, "absoluto")
                    self.stack.append(abs(val))

                elif op == OpCode.OP_DATE_FORMAT:
                    fmt = self.stack.pop()
                    from datetime import datetime
                    try:
                        self.stack.append(datetime.now().strftime(str(fmt)))
                    except Exception:
                        self.stack.append(str(datetime.now()))

                elif op == OpCode.OP_STRING_SPLIT:
                    sep = self.stack.pop()
                    texto = self.stack.pop()
                    self._check_string(texto, "dividir")
                    self._check_string(sep, "dividir")
                    self.stack.append(texto.split(sep))

                elif op == OpCode.OP_STRING_JOIN:
                    sep = self.stack.pop()
                    lst = self.stack.pop()
                    if not isinstance(lst, list):
                        raise RuntimeError(
                            f"'unir' solo funciona con listas, se encontro {self._tipo_str(lst)}"
                        )
                    self.stack.append(sep.join(str(x) for x in lst))

                elif op == OpCode.OP_TO_NUMBER:
                    val = self.stack.pop()
                    if isinstance(val, (int, float)):
                        self.stack.append(val)
                    elif isinstance(val, str):
                        try:
                            if '.' in val:
                                self.stack.append(float(val))
                            else:
                                self.stack.append(int(val))
                        except ValueError:
                            raise RuntimeError(
                                f"No se pudo convertir '{val}' a numero"
                            )
                    else:
                        raise RuntimeError(
                            f"'a_numero' esperaba un texto, se encontro {self._tipo_str(val)}"
                        )

                elif op == OpCode.OP_REGEX_SEARCH:
                    patron = self.stack.pop()
                    texto = self.stack.pop()
                    self._check_string(texto, "regex_buscar")
                    self._check_string(patron, "regex_buscar")
                    import re
                    matches = re.findall(patron, texto)
                    self.stack.append(matches)

                elif op == OpCode.OP_TRY_PUSH:
                    handler_addr = self.bytecode[self.ip]
                    self.ip += 1
                    self.exception_stack.append({
                        'handler': handler_addr,
                        'frame_depth': len(self.frames),
                        'stack_depth': len(self.stack),
                    })

                elif op == OpCode.OP_TRY_POP:
                    if self.exception_stack:
                        self.exception_stack.pop()

                elif op == OpCode.OP_THROW:
                    msg = self.stack.pop()
                    raise RuntimeError(str(msg))

                elif op == OpCode.OP_ERROR_MSG:
                    self.stack.append(self.last_error)

                elif op == OpCode.OP_CLASS:
                    class_name = self.constants[self.bytecode[self.ip]]
                    class_data = self.constants[self.bytecode[self.ip + 1]]
                    self.ip += 2
                    self.classes[class_name] = class_data

                elif op == OpCode.OP_NEW:
                    num_args = self.bytecode[self.ip]
                    self.ip += 1
                    class_name = self.stack.pop()

                    if class_name not in self.classes:
                        raise RuntimeError(f"La clase '{class_name}' no existe")

                    args_values = []
                    for _ in range(num_args):
                        args_values.append(self.stack.pop())
                    args_values.reverse()

                    class_info = self.classes[class_name]
                    all_props = {}

                    def collect_props(c_name):
                        c_info = self.classes[c_name]
                        if c_info['parent']:
                            collect_props(c_info['parent'])
                        all_props.update(c_info['props'])

                    collect_props(class_name)

                    instance = all_props.copy()
                    instance['_clase'] = class_name

                    def find_method(c_name, m_name):
                        c_info = self.classes[c_name]
                        if m_name in c_info['methods']:
                            return c_info['methods'][m_name]
                        if c_info['parent']:
                            return find_method(c_info['parent'], m_name)
                        return None

                    init_props = find_method(class_name, '__init_props')
                    constructor = find_method(class_name, 'inicializar')

                    if init_props:
                        if constructor:
                            self._init_chain = {
                                'instance': instance,
                                'args': args_values,
                                'class_name': class_name,
                                'next_addr': constructor[0],
                            }
                        else:
                            self._init_chain = None
                        method_addr, _ = init_props
                        self.frames.append({
                            'return_ip': self.ip,
                            'locals': {0: instance},
                            'func_name': f'{class_name}.__init_props',
                            'call_ip': self.ip - 1,
                        })
                        self.ip = method_addr
                        self.stack.append(instance)
                    elif constructor:
                        method_addr, _ = constructor
                        new_locals = {0: instance}
                        for i, val in enumerate(args_values):
                            new_locals[i + 1] = val
                        self.frames.append({
                            'return_ip': self.ip,
                            'locals': new_locals,
                            'func_name': f'{class_name}.inicializar',
                            'call_ip': self.ip - 1,
                            '_is_constructor': True,
                        })
                        self._pending_instance = instance
                        self.ip = method_addr
                    else:
                        self.stack.append(instance)

                elif op == OpCode.OP_GET_ATTR:
                    prop_name = self.stack.pop()
                    obj = self.stack.pop()

                    if isinstance(obj, dict):
                        if prop_name in obj:
                            self.stack.append(obj[prop_name])
                        elif '_clase' in obj:
                            getter = self._find_getter(obj['_clase'], prop_name)
                            if getter:
                                method_addr, _ = getter
                                self.frames.append({
                                    'return_ip': self.ip,
                                    'locals': {0: obj},
                                    'func_name': f'{obj["_clase"]}.getter.{prop_name}',
                                    'call_ip': self.ip - 1,
                                })
                                self.ip = method_addr
                                self.stack.append(obj)
                                continue

                            def find_method_recursive(c_name, m_name):
                                if c_name not in self.classes:
                                    return None
                                c_info = self.classes[c_name]
                                if m_name in c_info['methods']:
                                    return c_info['methods'][m_name]
                                if c_info['parent']:
                                    return find_method_recursive(c_info['parent'], m_name)
                                return None

                            method = find_method_recursive(obj['_clase'], prop_name)
                            if method:
                                method_addr, num_params = method
                                self.stack.append(('METODO', method_addr, num_params, obj))
                            else:
                                raise RuntimeError(
                                    f"El objeto no tiene la propiedad o metodo '{prop_name}'"
                                )
                        else:
                            raise RuntimeError(
                                f"El objeto no tiene la propiedad '{prop_name}'"
                            )
                    else:
                        raise RuntimeError(
                            "No se puede obtener propiedad de un valor que no es objeto"
                        )

                elif op == OpCode.OP_SET_ATTR:
                    prop_name = self.stack.pop()
                    val = self.stack.pop()
                    obj = self.stack.pop()
                    if isinstance(obj, dict):
                        if '_clase' in obj:
                            setter = self._find_setter(obj['_clase'], prop_name)
                            if setter:
                                method_addr, _ = setter
                                self.frames.append({
                                    'return_ip': self.ip,
                                    'locals': {0: obj, 1: val},
                                    'func_name': f'{obj["_clase"]}.setter.{prop_name}',
                                    'call_ip': self.ip - 1,
                                })
                                self.ip = method_addr
                                continue
                        obj[prop_name] = val
                    else:
                        raise RuntimeError(
                            "No se puede establecer propiedad en un valor que no es objeto"
                        )

                elif op == OpCode.OP_SUPER_ATTR:
                    parent_name = self.stack.pop()
                    method_name = self.stack.pop()
                    instance = self.stack.pop()

                    def find_in_class(c_name, m_name):
                        if c_name not in self.classes:
                            return None
                        c_info = self.classes[c_name]
                        if m_name in c_info['methods']:
                            return c_info['methods'][m_name]
                        if c_info['parent']:
                            return find_in_class(c_info['parent'], m_name)
                        return None

                    method = find_in_class(parent_name, method_name)
                    if method:
                        method_addr, num_params = method
                        self.stack.append(('METODO', method_addr, num_params, instance))
                    else:
                        raise RuntimeError(
                            f"La clase padre '{parent_name}' no tiene el metodo '{method_name}'"
                        )

                elif op == OpCode.OP_INSTANCEOF:
                    class_name = self.stack.pop()
                    obj = self.stack.pop()
                    if not isinstance(obj, dict) or '_clase' not in obj:
                        self.stack.append(False)
                    else:
                        def walk_parents(c_name):
                            if c_name == class_name:
                                return True
                            if c_name not in self.classes:
                                return False
                            parent = self.classes[c_name].get('parent')
                            if parent:
                                return walk_parents(parent)
                            return False
                        self.stack.append(walk_parents(obj['_clase']))

                elif op == OpCode.OP_START_SERVER:
                    rutas = self.stack.pop()
                    puerto = self.stack.pop()

                    if FastAPI is None or uvicorn is None:
                        raise RuntimeError(
                            "FastAPI o Uvicorn no estan instalados. "
                            "Usa 'pip install fastapi uvicorn'"
                        )

                    app = FastAPI()

                    for path, config in rutas.items():
                        method = "GET"
                        func_name = ""

                        if isinstance(config, str):
                            func_name = config
                        elif isinstance(config, dict):
                            func_name = config.get("funcion", "")
                            method = config.get("metodo", "GET").upper()

                        if func_name not in self.functions:
                            raise RuntimeError(
                                f"La funcion '{func_name}' no existe"
                            )

                        finfo = self.functions[func_name]
                        addr = finfo[0]
                        num_params = finfo[1]
                        params_names = finfo[2]

                        def create_handler(target_addr, expected_params_count, param_names):
                            async def handler(request: Request):
                                body_data = {}
                                if request.method in ["POST", "PUT", "PATCH"]:
                                    try:
                                        body_data = await request.json()
                                    except Exception:
                                        body_data = {}

                                query_params = dict(request.query_params)
                                path_params = request.path_params

                                combined_data = {
                                    **query_params,
                                    **body_data,
                                    **path_params,
                                }

                                old_ip = self.ip
                                old_frames = self.frames[:]

                                args_to_push = []
                                for p_name in param_names:
                                    args_to_push.append(
                                        combined_data.get(p_name, None)
                                    )

                                new_locals = {
                                    i: val for i, val in enumerate(args_to_push)
                                }
                                self.frames = [
                                    {'return_ip': -1, 'locals': new_locals}
                                ]
                                self.ip = target_addr

                                try:
                                    old_stack = self.stack[:]
                                    self.stack = []
                                    self.run()
                                    result = self.stack.pop() if self.stack else None
                                    self.stack = old_stack
                                    return result
                                finally:
                                    self.ip = old_ip
                                    self.frames = old_frames

                            return handler

                        app.add_api_route(
                            path,
                            create_handler(addr, num_params, params_names),
                            methods=[method],
                        )

                    print(
                        f"Iniciando servidor Alvz (Full FastAPI Support) "
                        f"en http://localhost:{puerto}"
                    )
                    uvicorn.run(app, host="0.0.0.0", port=int(puerto))

                elif op == OpCode.OP_SLICE:
                    fin = self.stack.pop()
                    inicio = self.stack.pop()
                    obj = self.stack.pop()

                    if isinstance(obj, (list, str)):
                        real_inicio = int(inicio) if inicio is not None else 0
                        real_fin = int(fin) if fin is not None else len(obj)
                        self.stack.append(obj[real_inicio:real_fin])
                    else:
                        raise RuntimeError(
                            f"No se puede hacer slicing en un valor de tipo "
                            f"{type(obj).__name__}"
                        )

                elif op == OpCode.OP_SOLICITUD_HTTP:
                    metodo = self.stack.pop()
                    datos = self.stack.pop()
                    url = self.stack.pop()
                    import requests as req
                    try:
                        metodo = str(metodo).upper()
                        if metodo == "GET":
                            resp = req.get(url, params=datos if isinstance(datos, dict) else None, timeout=30)
                        elif metodo == "POST":
                            resp = req.post(url, json=datos if isinstance(datos, (dict, list)) else {"data": datos}, timeout=30)
                        elif metodo == "PUT":
                            resp = req.put(url, json=datos if isinstance(datos, (dict, list)) else {"data": datos}, timeout=30)
                        elif metodo == "DELETE":
                            resp = req.delete(url, timeout=30)
                        else:
                            self.stack.append({"codigo": 0, "cuerpo": "", "error": f"Metodo no soportado: {metodo}"})
                            continue
                        self.stack.append({
                            "codigo": resp.status_code,
                            "cuerpo": resp.text,
                            "json": resp.json() if resp.text else None
                        })
                    except Exception as e:
                        self.stack.append({"codigo": 0, "cuerpo": "", "error": str(e)})

                elif op == OpCode.OP_SQLITE_ABRIR:
                    ruta = self.stack.pop()
                    try:
                        conn = sqlite3.connect(str(ruta))
                        self.stack.append(conn)
                    except Exception as e:
                        self.stack.append({"error": str(e)})

                elif op == OpCode.OP_SQLITE_EJECUTAR:
                    sql = self.stack.pop()
                    conn = self.stack.pop()
                    if not isinstance(conn, sqlite3.Connection):
                        raise RuntimeError("Error: 'sqlite_ejecutar' requiere una conexion valida")
                    try:
                        cursor = conn.execute(str(sql))
                        conn.commit()
                        self.stack.append(cursor.rowcount)
                    except Exception as e:
                        raise RuntimeError(f"Error SQL: {e}")

                elif op == OpCode.OP_SQLITE_CONSULTAR:
                    sql = self.stack.pop()
                    conn = self.stack.pop()
                    if not isinstance(conn, sqlite3.Connection):
                        raise RuntimeError("Error: 'sqlite_consultar' requiere una conexion valida")
                    try:
                        cursor = conn.execute(str(sql))
                        columnas = [desc[0] for desc in cursor.description]
                        filas = cursor.fetchall()
                        resultados = []
                        for fila in filas:
                            row = {}
                            for i, col in enumerate(columnas):
                                row[col] = fila[i]
                            resultados.append(row)
                        self.stack.append(resultados)
                    except Exception as e:
                        raise RuntimeError(f"Error SQL: {e}")

                elif op == OpCode.OP_HALT:
                    break

                elif op == OpCode.OP_IMPORT:
                    filename = self.stack.pop()
                    self._import_file(filename)

                elif op == OpCode.OP_DICT_KEYS:
                    val = self.stack.pop()
                    if isinstance(val, dict):
                        self.stack.append(list(val.keys()))
                    else:
                        self.stack.append(val)

                elif op == OpCode.OP_NULL:
                    self.stack.append(None)

                elif op == OpCode.OP_ASYNC_CALL:
                    func_addr = self.bytecode[self.ip]
                    num_args = self.bytecode[self.ip + 1]
                    self.ip += 3

                    args_values = []
                    for _ in range(num_args):
                        args_values.append(self.stack.pop())
                    args_values.reverse()

                    coro = Coroutine(func_addr, args_values)
                    coro.name = 'coro'
                    for fname, finfo in self.functions.items():
                        if finfo[0] == func_addr:
                            coro.name = fname
                            break

                    if not hasattr(self, '_event_loop') or self._event_loop is None:
                        self._event_loop = EventLoop()

                    inner_vm = VM(
                        list(self.bytecode), list(self.constants),
                        dict(self.line_map), dict(self.functions)
                    )
                    inner_vm.globals = self.globals
                    inner_vm.classes = self.classes
                    coro.vm = inner_vm
                    coro.state = 'running'
                    self._event_loop.start_coroutine(
                        coro, inner_vm.bytecode, inner_vm.constants,
                        inner_vm.line_map, inner_vm.functions,
                        inner_vm.globals, inner_vm.classes,
                        self.output_buffer
                    )
                    self.stack.append(coro)

                elif op == OpCode.OP_AWAIT:
                    coro = self.stack.pop()
                    if not isinstance(coro, Coroutine):
                        raise RuntimeError("Error: 'aguardar' solo puede usarse con corutinas")
                    if coro.state == 'completed':
                        self.stack.append(coro.result if coro.result is not None else False)
                        continue

                    result = self._event_loop.await_coroutine(coro)
                    self.stack.append(result if result is not None else False)

            except Exception as e:
                self.last_error = str(e)
                linea_err = self.line_map.get(current_ip, "desconocida")
                stack_trace = self._build_stack_trace(current_ip)

                if self.exception_stack:
                    handler_info = self.exception_stack.pop()
                    while len(self.frames) > handler_info['frame_depth']:
                        self.frames.pop()
                    while len(self.stack) > handler_info['stack_depth']:
                        self.stack.pop()
                    self.ip = handler_info['handler']
                else:
                    raise RuntimeError(
                        f"Error en tiempo de ejecucion (linea {linea_err}): {e}\n"
                        f"Pila de llamadas:\n{stack_trace}"
                    ) from None
