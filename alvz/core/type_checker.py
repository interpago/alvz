"""Type checker para Alvz.

Camina el bytecode y verifica consistencia de tipos usando
anotaciones del parser e inferencia de tipos literales.
"""

from .bytecode import OpCode
from .types import Tipo, tipo_desde_valor, tipo_compatible


class TypeErrorAlvz(Exception):
    pass


def _tipo_desde_nombre(nombre):
    m = {
        "numero": Tipo.NUMERO,
        "texto": Tipo.TEXTO,
        "booleano": Tipo.BOOLEANO,
        "nulo": Tipo.NULO,
        "lista": Tipo.LISTA,
        "diccionario": Tipo.DICCIONARIO,
        "funcion": Tipo.FUNCION,
        "cualquiera": Tipo.CUALQUIERA,
    }
    return m.get(nombre, Tipo.CUALQUIERA)


def _extraer_funciones(bytecode, functions):
    """Extract function body boundaries from bytecode."""
    func_bodies = {}
    for name, (addr, nparams, params, is_async) in functions.items():
        ip = addr
        while ip < len(bytecode):
            op = bytecode[ip]
            if op == OpCode.OP_RETURN:
                # Found end of function (after return is OP_MAKE_FUNC addr nparams)
                func_bodies[name] = (addr, ip + 1)
                break
            ip += 1
        else:
            func_bodies[name] = (addr, len(bytecode))
    return func_bodies


class TypeChecker:
    def __init__(self, bytecode, constants, line_map, functions,
                 var_types=None, func_types=None,
                 global_symbols=None):
        self.bytecode = bytecode
        self.constants = constants
        self.line_map = line_map
        self.functions = functions
        self.var_types = var_types or {}
        self.func_types = func_types or {}
        self.global_symbols = global_symbols or {}
        self.ip = 0
        self.type_stack = []
        self.errors = []
        self._locals = {}

    def check(self):
        self.errors = []
        self._check_global_scope()
        for func_name, (start, end) in _extraer_funciones(self.bytecode, self.functions).items():
            self._check_function(func_name, start, end)
        return self.errors

    def _check_global_scope(self):
        self.ip = 0
        self.type_stack = []
        self._locals = {}

        while self.ip < len(self.bytecode):
            current_ip = self.ip
            op = self.bytecode[self.ip]
            self.ip += 1

            try:
                if op == OpCode.OP_CONSTANT:
                    idx = self.bytecode[self.ip]
                    self.ip += 1
                    val = self.constants[idx]
                    self.type_stack.append(tipo_desde_valor(val))

                elif op == OpCode.OP_STORE_GLOBAL:
                    var_idx = self.bytecode[self.ip]
                    self.ip += 1
                    val_type = self._pop_type()
                    self._check_global_type(var_idx, val_type, current_ip)
                    self._locals[var_idx] = val_type

                elif op == OpCode.OP_LOAD_GLOBAL:
                    var_idx = self.bytecode[self.ip]
                    self.ip += 1
                    self.type_stack.append(self._locals.get(var_idx, Tipo.CUALQUIERA))

                elif op == OpCode.OP_STORE:
                    var_idx = self.bytecode[self.ip]
                    self.ip += 1
                    val_type = self._pop_type()
                    self._locals[var_idx] = val_type

                elif op == OpCode.OP_LOAD:
                    var_idx = self.bytecode[self.ip]
                    self.ip += 1
                    self.type_stack.append(self._locals.get(var_idx, Tipo.CUALQUIERA))

                elif op in (OpCode.OP_NEGATE,):
                    val = self._pop_type()
                    self._require(val, Tipo.NUMERO, "negacion")
                    self.type_stack.append(Tipo.NUMERO)

                elif op in (OpCode.OP_ADD, OpCode.OP_SUB, OpCode.OP_MUL,
                            OpCode.OP_DIV, OpCode.OP_MOD):
                    b = self._pop_type()
                    a = self._pop_type()
                    if op == OpCode.OP_ADD and (a == Tipo.TEXTO or b == Tipo.TEXTO):
                        result = Tipo.TEXTO
                    elif a == Tipo.NUMERO or b == Tipo.NUMERO:
                        result = Tipo.NUMERO
                    else:
                        result = Tipo.NUMERO
                    self.type_stack.append(result)

                elif op in (OpCode.OP_EQ, OpCode.OP_NE, OpCode.OP_GT,
                            OpCode.OP_LT, OpCode.OP_GTE, OpCode.OP_LTE):
                    self._pop_type()
                    self._pop_type()
                    self.type_stack.append(Tipo.BOOLEANO)

                elif op in (OpCode.OP_AND, OpCode.OP_OR):
                    self._pop_type()
                    self._pop_type()
                    self.type_stack.append(Tipo.BOOLEANO)

                elif op == OpCode.OP_JUMP:
                    target = self.bytecode[self.ip]
                    self.ip = target
                    continue

                elif op == OpCode.OP_JUMP_IF_FALSE:
                    target = self.bytecode[self.ip]
                    self.ip += 1
                    self._pop_type()

                elif op == OpCode.OP_PRINT:
                    if self.type_stack:
                        self._pop_type()

                elif op == OpCode.OP_POP:
                    if self.type_stack:
                        self.type_stack.pop()

                elif op == OpCode.OP_CALL:
                    func_addr = self.bytecode[self.ip]
                    num_args = self.bytecode[self.ip + 1]
                    self.ip += 3
                    self._check_call_target(func_addr, num_args, current_ip)

                elif op == OpCode.OP_ASYNC_CALL:
                    func_addr = self.bytecode[self.ip]
                    num_args = self.bytecode[self.ip + 1]
                    self.ip += 3
                    self._check_call_target(func_addr, num_args, current_ip)

                elif op == OpCode.OP_AWAIT:
                    val_type = self._pop_type()
                    self.type_stack.append(val_type)

                elif op == OpCode.OP_RETURN:
                    # Global scope return (halt for program)
                    break

                elif op == OpCode.OP_NULL:
                    self.type_stack.append(Tipo.NULO)

                elif op == OpCode.OP_LIST:
                    num = self.bytecode[self.ip]
                    self.ip += 1
                    for _ in range(num):
                        self._pop_type()
                    self.type_stack.append(Tipo.LISTA)

                elif op == OpCode.OP_DICT:
                    num = self.bytecode[self.ip]
                    self.ip += 1
                    for _ in range(num * 2):
                        self._pop_type()
                    self.type_stack.append(Tipo.DICCIONARIO)

                elif op == OpCode.OP_GET_INDEX:
                    self._pop_type()
                    self._pop_type()
                    self.type_stack.append(Tipo.CUALQUIERA)

                elif op == OpCode.OP_SET_INDEX:
                    self._pop_type()
                    self._pop_type()
                    self._pop_type()

                elif op == OpCode.OP_LENGTH:
                    self._pop_type()
                    self.type_stack.append(Tipo.NUMERO)

                elif op == OpCode.OP_APPEND:
                    self._pop_type()
                    self._pop_type()
                    self.type_stack.append(Tipo.LISTA)

                elif op == OpCode.OP_TYPE:
                    self._pop_type()
                    self.type_stack.append(Tipo.TEXTO)

                elif op == OpCode.OP_CLASS:
                    self.ip += 2

                elif op == OpCode.OP_NEW:
                    num_args = self.bytecode[self.ip]
                    self.ip += 1
                    self._pop_type()
                    for _ in range(num_args):
                        self._pop_type()
                    self.type_stack.append(Tipo.DICCIONARIO)

                elif op == OpCode.OP_GET_ATTR:
                    self._pop_type()
                    self._pop_type()
                    self.type_stack.append(Tipo.CUALQUIERA)

                elif op == OpCode.OP_SET_ATTR:
                    self._pop_type()
                    self._pop_type()
                    self._pop_type()

                elif op == OpCode.OP_MAKE_FUNC:
                    self.ip += 2
                    self.type_stack.append(Tipo.FUNCION)

                elif op == OpCode.OP_HALT:
                    break

            except TypeErrorAlvz as e:
                line = self.line_map.get(current_ip, '?')
                self.errors.append(f"Error de tipo (linea {line}): {e}")

    def _check_function(self, func_name, start, end):
        self.ip = start
        self.type_stack = []

        _, nparams, params, _ = self.functions[func_name]
        param_types, return_type = self.func_types.get(func_name, ([], None))

        # Initialize locals with parameter types
        local_types = {}
        for i, pname in enumerate(params):
            if i < len(param_types) and param_types[i] is not None:
                local_types[i] = _tipo_desde_nombre(param_types[i])
            else:
                local_types[i] = Tipo.CUALQUIERA

        self._locals = local_types

        while self.ip < end:
            current_ip = self.ip
            op = self.bytecode[self.ip]
            self.ip += 1

            try:
                if op == OpCode.OP_CONSTANT:
                    idx = self.bytecode[self.ip]
                    self.ip += 1
                    val = self.constants[idx]
                    self.type_stack.append(tipo_desde_valor(val))

                elif op == OpCode.OP_STORE:
                    var_idx = self.bytecode[self.ip]
                    self.ip += 1
                    val_type = self._pop_type()
                    self._check_var_type(func_name, var_idx, val_type, current_ip)
                    self._locals[var_idx] = val_type

                elif op == OpCode.OP_LOAD:
                    var_idx = self.bytecode[self.ip]
                    self.ip += 1
                    self.type_stack.append(self._locals.get(var_idx, Tipo.CUALQUIERA))

                elif op == OpCode.OP_STORE_GLOBAL:
                    var_idx = self.bytecode[self.ip]
                    self.ip += 1
                    val_type = self._pop_type()
                    self._check_global_type(var_idx, val_type, current_ip)
                    self._locals[var_idx] = val_type

                elif op == OpCode.OP_LOAD_GLOBAL:
                    var_idx = self.bytecode[self.ip]
                    self.ip += 1
                    self.type_stack.append(Tipo.CUALQUIERA)

                elif op in (OpCode.OP_NEGATE,):
                    val = self._pop_type()
                    self._require(val, Tipo.NUMERO, "negacion")
                    self.type_stack.append(Tipo.NUMERO)

                elif op in (OpCode.OP_ADD, OpCode.OP_SUB, OpCode.OP_MUL,
                            OpCode.OP_DIV, OpCode.OP_MOD):
                    b = self._pop_type()
                    a = self._pop_type()
                    if op == OpCode.OP_ADD and (a == Tipo.TEXTO or b == Tipo.TEXTO):
                        result = Tipo.TEXTO
                    elif a == Tipo.NUMERO or b == Tipo.NUMERO:
                        result = Tipo.NUMERO
                    else:
                        result = Tipo.NUMERO
                    self.type_stack.append(result)

                elif op in (OpCode.OP_EQ, OpCode.OP_NE, OpCode.OP_GT,
                            OpCode.OP_LT, OpCode.OP_GTE, OpCode.OP_LTE):
                    self._pop_type()
                    self._pop_type()
                    self.type_stack.append(Tipo.BOOLEANO)

                elif op in (OpCode.OP_AND, OpCode.OP_OR):
                    self._pop_type()
                    self._pop_type()
                    self.type_stack.append(Tipo.BOOLEANO)

                elif op == OpCode.OP_JUMP:
                    target = self.bytecode[self.ip]
                    if target < start or target >= end:
                        break
                    self.ip = target
                    continue

                elif op == OpCode.OP_JUMP_IF_FALSE:
                    target = self.bytecode[self.ip]
                    self.ip += 1
                    self._pop_type()

                elif op == OpCode.OP_PRINT:
                    if self.type_stack:
                        self._pop_type()

                elif op == OpCode.OP_POP:
                    if self.type_stack:
                        self.type_stack.pop()

                elif op == OpCode.OP_CALL:
                    func_addr = self.bytecode[self.ip]
                    num_args = self.bytecode[self.ip + 1]
                    self.ip += 3
                    self._check_call_target(func_addr, num_args, current_ip)

                elif op == OpCode.OP_ASYNC_CALL:
                    func_addr = self.bytecode[self.ip]
                    num_args = self.bytecode[self.ip + 1]
                    self.ip += 3
                    self._check_call_target(func_addr, num_args, current_ip)

                elif op == OpCode.OP_AWAIT:
                    val_type = self._pop_type()
                    self.type_stack.append(val_type)

                elif op == OpCode.OP_RETURN:
                    ret_type = self._pop_type() if self.type_stack else Tipo.NULO
                    self._check_return_type(func_name, ret_type, return_type, current_ip)
                    break

                elif op == OpCode.OP_NULL:
                    self.type_stack.append(Tipo.NULO)

                elif op == OpCode.OP_LIST:
                    num = self.bytecode[self.ip]
                    self.ip += 1
                    for _ in range(num):
                        self._pop_type()
                    self.type_stack.append(Tipo.LISTA)

                elif op == OpCode.OP_DICT:
                    num = self.bytecode[self.ip]
                    self.ip += 1
                    for _ in range(num * 2):
                        self._pop_type()
                    self.type_stack.append(Tipo.DICCIONARIO)

                elif op == OpCode.OP_GET_INDEX:
                    self._pop_type()
                    self._pop_type()
                    self.type_stack.append(Tipo.CUALQUIERA)

                elif op == OpCode.OP_SET_INDEX:
                    self._pop_type()
                    self._pop_type()
                    self._pop_type()

                elif op == OpCode.OP_LENGTH:
                    self._pop_type()
                    self.type_stack.append(Tipo.NUMERO)

                elif op == OpCode.OP_APPEND:
                    self._pop_type()
                    self._pop_type()
                    self.type_stack.append(Tipo.LISTA)

                elif op == OpCode.OP_TYPE:
                    self._pop_type()
                    self.type_stack.append(Tipo.TEXTO)

                elif op == OpCode.OP_CLASS:
                    self.ip += 2

                elif op == OpCode.OP_NEW:
                    num_args = self.bytecode[self.ip]
                    self.ip += 1
                    self._pop_type()
                    for _ in range(num_args):
                        self._pop_type()
                    self.type_stack.append(Tipo.DICCIONARIO)

                elif op == OpCode.OP_GET_ATTR:
                    self._pop_type()
                    self._pop_type()
                    self.type_stack.append(Tipo.CUALQUIERA)

                elif op == OpCode.OP_SET_ATTR:
                    self._pop_type()
                    self._pop_type()
                    self._pop_type()

                elif op == OpCode.OP_MAKE_FUNC:
                    self.ip += 2
                    self.type_stack.append(Tipo.FUNCION)

                elif op == OpCode.OP_HALT:
                    break

            except TypeErrorAlvz as e:
                line = self.line_map.get(current_ip, '?')
                self.errors.append(f"Error de tipo (linea {line}): {e}")

    def _pop_type(self):
        if self.type_stack:
            return self.type_stack.pop()
        return Tipo.CUALQUIERA

    def _require(self, actual, expected, context="operacion"):
        if actual != Tipo.CUALQUIERA and actual != expected:
            raise TypeErrorAlvz(
                f"Se esperaba tipo '{expected}' para {context}, "
                f"pero se encontro '{actual}'"
            )

    def _check_global_type(self, var_idx, val_type, ip):
        name = None
        for n, idx in self.global_symbols.items():
            if idx == var_idx:
                name = n
                break
        if name and name in self.var_types:
            expected = _tipo_desde_nombre(self.var_types[name])
            if not tipo_compatible(val_type, expected):
                line = self.line_map.get(ip, '?')
                raise TypeErrorAlvz(
                    f"Se esperaba tipo '{self.var_types[name]}' para variable "
                    f"'{name}', pero se encontro '{self._nombre_tipo(val_type)}'"
                )

    def _check_var_type(self, func_name, var_idx, val_type, ip):
        _, _, params, _ = self.functions[func_name]
        if var_idx < len(params):
            pname = params[var_idx]
            if pname in self.var_types:
                expected = _tipo_desde_nombre(self.var_types[pname])
                if not tipo_compatible(val_type, expected):
                    line = self.line_map.get(ip, '?')
                    raise TypeErrorAlvz(
                        f"Se esperaba tipo '{self.var_types[pname]}' para "
                        f"parametro '{pname}', pero se encontro "
                        f"'{self._nombre_tipo(val_type)}'"
                    )

    def _check_call_target(self, func_addr, num_args, ip):
        func_name = None
        for name, (addr, nparams, params, is_async) in self.functions.items():
            if addr == func_addr:
                func_name = name
                break

        arg_types = []
        for _ in range(num_args):
            arg_types.insert(0, self._pop_type())

        self.type_stack.append(Tipo.CUALQUIERA)

        if func_name and func_name in self.func_types:
            param_types, return_type = self.func_types[func_name]
            expected_return = _tipo_desde_nombre(return_type) if return_type else Tipo.CUALQUIERA
            self.type_stack[-1] = expected_return

            line = self.line_map.get(ip, '?')
            if len(arg_types) != len(param_types):
                raise TypeErrorAlvz(
                    f"La funcion '{func_name}' esperaba {len(param_types)} argumentos, "
                    f"pero recibio {len(arg_types)}"
                )
            for i, (arg, expected_name) in enumerate(zip(arg_types, param_types)):
                if expected_name is not None:
                    expected = _tipo_desde_nombre(expected_name)
                    if not tipo_compatible(arg, expected):
                        raise TypeErrorAlvz(
                            f"Argumento {i+1} de '{func_name}' esperaba tipo "
                            f"'{expected_name}', pero se encontro "
                            f"'{self._nombre_tipo(arg)}'"
                        )

    def _check_return_type(self, func_name, actual, return_type_name, ip):
        if return_type_name is None:
            return
        expected = _tipo_desde_nombre(return_type_name)
        if not tipo_compatible(actual, expected):
            line = self.line_map.get(ip, '?')
            raise TypeErrorAlvz(
                f"La funcion '{func_name}' debe retornar tipo '{return_type_name}', "
                f"pero se encontro '{self._nombre_tipo(actual)}'"
            )

    def _nombre_tipo(self, tipo_val):
        for name, val in vars(Tipo).items():
            if val == tipo_val:
                return name.lower()
        return str(tipo_val)
