"""
Parser/Compilador para Alvz Language.

Analiza tokens y genera bytecode ejecutable por la VM.
"""

from .bytecode import OpCode
from .errors import obtener_sugerencia, KEYWORDS_ALVZ
from .lexer import Token as BaseToken
from .optimizer import optimize as optimize_bytecode

# Alias para la compatibilidad (Token es el Lexer Token)
Token = BaseToken

# Nombres legibles para mensajes de error
_NOMBRES = {
    Token.NULO: "'nulo'",
    Token.VARIABLE: "'variable'",
    Token.IDENTIFICADOR: "un nombre",
    Token.ASIGNACION: "'='",
    Token.PAREN_IZQ: "'('",
    Token.PAREN_DER: "')'",
    Token.LLAVE_IZQ: "'{'",
    Token.LLAVE_DER: "'}'",
    Token.COMA: "','",
    Token.NUMERO: "un numero",
    Token.STRING: "un texto",
    Token.STRING_TRIPLE: "un texto",
    Token.SI: "'si'",
    Token.SINO: "'sino'",
    Token.MIENTRAS: "'mientras'",
    Token.PARA: "'para'",
    Token.FUNCION: "'funcion'",
    Token.RETORNAR: "'retornar'",
    Token.EN: "'en'",
    Token.DE: "'de'",
    Token.A: "'a'",
    Token.IMPORTAR: "'importar'",
    Token.INTENTAR: "'intentar'",
    Token.CAPTURAR: "'capturar'",
    Token.LANZAR: "'lanzar'",
    Token.CLASE: "'clase'",
    Token.NUEVO: "'nuevo'",
    Token.SUPER: "'super'",
    Token.INSTANCIA: "'instancia'",
    Token.ESTATICO: "'estatico'",
    Token.PROPIEDAD: "'propiedad'",
    Token.OBTENER: "'obtener'",
    Token.ESTABLECER: "'establecer'",
    Token.CORCHETE_IZQ: "'['",
    Token.CORCHETE_DER: "']'",
    Token.DOS_PUNTOS: "':'",
    Token.ROMPER: "'romper'",
    Token.CONTINUAR: "'continuar'",
    Token.ASYNC: "'async'",
    Token.AGUARDAR: "'aguardar'",
    Token.MAS_IGUAL: "'+='",
    Token.MENOS_IGUAL: "'-='",
    Token.POR_IGUAL: "'*='",
    Token.ENTRE_IGUAL: "'/='",
    Token.MOD_IGUAL: "'%='",
    Token.GLOBAL: "'global'",
}

# Tokens de palabras clave que pueden usarse como identificadores
_IDENT_KEYWORDS = {Token.A, Token.Y, Token.O, Token.EN, Token.DE, Token.OBTENER, Token.ESTABLECER, Token.PROPIEDAD}

# Tokens de funciones built-in que tambien pueden usarse como nombres
_IDENT_CALLABLE_KEYWORDS = {
    Token.LONGITUD, Token.AGREGAR, Token.AZAR, Token.ESPERAR, Token.LIMPIAR,
    Token.LEER, Token.LEER_NUMERO, Token.ENVIAR_WEB, Token.ESCRIBIR_ARCHIVO,
    Token.MINUSCULAS, Token.MAYUSCULAS, Token.OBTENER_SALIDA,
    Token.IMPRIMIR, Token.RETORNAR, Token.TIEMPO, Token.TIPO_KW,
    Token.JSON_CODIFICAR, Token.JSON_DECODIFICAR,
    Token.REEMPLAZAR, Token.ABSOLUTO, Token.REDONDEAR, Token.POTENCIA, Token.RAIZ,
    Token.FECHA_ACTUAL, Token.DIVIDIR, Token.UNIR, Token.A_NUMERO,
    Token.REGEX_BUSCAR, Token.INICIAR_SERVIDOR, Token.LEER_ARCHIVO,
    Token.SUPABASE_CONSULTAR, Token.SUPABASE_INSERTAR,
    Token.SOLICITUD_HTTP, Token.SQLITE_ABRIR, Token.SQLITE_EJECUTAR, Token.SQLITE_CONSULTAR,
    Token.IMPORTAR, Token.GLOBAL, Token.LANZAR, Token.CAPTURAR,
    Token.ROMPER, Token.CONTINUAR, Token.ESTATICO,
    Token.INTENTAR, Token.ASYNC, Token.AGUARDAR,
}


class Parser:
    """Analiza tokens y genera bytecode para la VM."""

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.bytecode = []
        self.constants = []
        self.line_map = {}
        self.global_symbols = {}
        self.symbols = self.global_symbols
        self.functions = {}
        self.defined_classes = {}
        self._loop_stack = []
        self._global_vars = set()

    # ---------------------------------------------------------------
    # Utilidades
    # ---------------------------------------------------------------

    def current_token(self):
        return self.tokens[self.pos]

    def consume(self, expected_type):
        token_type, value, line = self.current_token()
        if token_type == expected_type:
            self.pos += 1
            return value

        nombres = _NOMBRES
        # Intentar sugerencia si es un error de palabra clave
        sugerencia = ""
        if token_type == Token.IDENTIFICADOR:
            palabra_cercana = obtener_sugerencia(value)
            if palabra_cercana:
                sugerencia = f'. Quisiste decir "{palabra_cercana}"?'

        esperado = nombres.get(expected_type, str(expected_type))
        encontrado = nombres.get(token_type, str(token_type))
        raise RuntimeError(
            f"Error de sintaxis (linea {line}): Se esperaba {esperado}, "
            f"pero se encontro {encontrado}{sugerencia}"
        )

    def _consume_identifier(self):
        """Consume un identificador, aceptando tambien keywords que pueden ser nombres de variable."""
        token_type, value, line = self.current_token()
        if token_type == Token.IDENTIFICADOR or token_type in _IDENT_KEYWORDS or token_type in _IDENT_CALLABLE_KEYWORDS:
            self.pos += 1
            return value

        nombres = _NOMBRES
        sugerencia = ""
        if token_type == Token.IDENTIFICADOR:
            palabra_cercana = obtener_sugerencia(value)
            if palabra_cercana:
                sugerencia = f'. Quisiste decir "{palabra_cercana}"?'

        esperado = nombres.get(Token.IDENTIFICADOR, "un nombre")
        encontrado = nombres.get(token_type, str(token_type))
        raise RuntimeError(
            f"Error de sintaxis (linea {line}): Se esperaba {esperado}, "
            f"pero se encontro {encontrado}{sugerencia}"
        )

    def emit(self, opcode):
        self.bytecode.append(opcode)
        _, _, line = self.current_token()
        self.line_map[len(self.bytecode) - 1] = line
        return len(self.bytecode) - 1

    def patch(self, index, value):
        self.bytecode[index] = value

    # ---------------------------------------------------------------
    # Compilacion general
    # ---------------------------------------------------------------

    def _pre_scan_functions(self):
        """Pre-scan para recolectar nombres de funciones (soporte forward references)."""
        pos_backup = self.pos
        while self.pos < len(self.tokens):
            t_type, value, _ = self.current_token()
            if t_type == Token.FUNCION:
                scan_pos = self.pos + 1
                if scan_pos < len(self.tokens) and self.tokens[scan_pos][0] == Token.ASYNC:
                    scan_pos += 1
                if scan_pos < len(self.tokens) and self.tokens[scan_pos][0] == Token.IDENTIFICADOR:
                    fname = self.tokens[scan_pos][1]
                    if fname not in self.functions:
                        self.functions[fname] = (0, 0, [], False)
            self.pos += 1
        self.pos = pos_backup

    def compile(self, optimize=False, check_types=False):
        self._pre_scan_functions()
        while self.current_token()[0] != Token.EOF:
            self.compile_statement()
        self.emit(OpCode.OP_HALT)
        result = (self.bytecode, self.constants, self.line_map, self.functions)

        if check_types:
            from .type_checker import TypeChecker
            var_types = getattr(self, 'var_types', {})
            func_types = getattr(self, 'func_types', {})
            tc = TypeChecker(
                self.bytecode, self.constants, self.line_map, self.functions,
                var_types, func_types, self.global_symbols
            )
            errors = tc.check()
            if errors:
                raise RuntimeError("\n".join(errors))

        if optimize:
            bc, consts, funcs = optimize_bytecode(self.bytecode, self.constants, self.functions)
            result = (bc, consts, self.line_map, funcs)
        return result

    def compile_statement(self):
        token_type, value, line = self.current_token()

        dispatch = {
            Token.VARIABLE: self.compile_assignment,
            Token.IMPRIMIR: self.compile_print,
            Token.SI: self.compile_if,
            Token.MIENTRAS: self.compile_while,
            Token.PARA: self.compile_for,
            Token.LIMPIAR: self.compile_clear,
            Token.AGREGAR: self.compile_agregar_statement,
            Token.LONGITUD: self.compile_longitud_statement,
            Token.ESPERAR: self.compile_esperar_statement,
            Token.ENVIAR_WEB: self.compile_enviar_web_statement,
            Token.ESCRIBIR_ARCHIVO: self.compile_escribir_archivo_statement,
            Token.OBTENER_SALIDA: self._compile_pop_factor,
            Token.SUPABASE_INSERTAR: self._compile_pop_factor,
            Token.LEER_ARCHIVO: self._compile_pop_factor,
            Token.SUPABASE_CONSULTAR: self._compile_pop_factor,
            Token.JSON_DECODIFICAR: self._compile_pop_factor,
            Token.INICIAR_SERVIDOR: self._compile_pop_factor,
            Token.IMPORTAR: self.compile_import,
            Token.INTENTAR: self.compile_try_catch,
            Token.LANZAR: self._compile_throw,
            Token.CLASE: self.compile_class_definition,
            Token.FUNCION: self.compile_function_definition,
            Token.SUPER: self._compile_pop_factor,
            Token.RETORNAR: self.compile_return,
            Token.ROMPER: self.compile_break,
            Token.CONTINUAR: self.compile_continue,
            Token.FECHA_ACTUAL: self._compile_pop_factor,
            Token.DIVIDIR: self._compile_pop_factor,
            Token.UNIR: self._compile_pop_factor,
            Token.A_NUMERO: self._compile_pop_factor,
            Token.REGEX_BUSCAR: self._compile_pop_factor,
        Token.AGUARDAR: self._compile_pop_factor,
        Token.SOLICITUD_HTTP: self._compile_pop_factor,
        Token.SQLITE_ABRIR: self._compile_pop_factor,
        Token.SQLITE_EJECUTAR: self._compile_pop_factor,
        Token.SQLITE_CONSULTAR: self._compile_pop_factor,
        Token.IDENTIFICADOR: self.compile_identifier_statement,
        Token.A: self.compile_identifier_statement,
        Token.Y: self.compile_identifier_statement,
        Token.O: self.compile_identifier_statement,
        Token.EN: self.compile_identifier_statement,
        Token.DE: self.compile_identifier_statement,
        Token.OBTENER: self.compile_identifier_statement,
        Token.ESTABLECER: self.compile_identifier_statement,
        Token.PROPIEDAD: self.compile_identifier_statement,
        Token.CADA: self.compile_for_each,
        Token.GLOBAL: self.compile_global,
        }
        handler = dispatch.get(token_type)
        if handler:
            handler()
        else:
            self.pos += 1  # Ignorar tokens desconocidos por ahora

    # ---------------------------------------------------------------
    # Helpers para sentencias que necesitan factor + pop
    # ---------------------------------------------------------------

    def _compile_pop_factor(self):
        self.factor()
        self.emit(OpCode.OP_POP)

    def _compile_throw(self):
        self.pos += 1
        self.expression()
        self.emit(OpCode.OP_THROW)

    def compile_break(self):
        if not self._loop_stack:
            raise RuntimeError("Error: 'romper' solo puede usarse dentro de un bucle")
        self.consume(Token.ROMPER)
        loop_info = self._loop_stack[-1]
        self.emit(OpCode.OP_JUMP)
        idx = self.emit(0)
        loop_info['breaks'].append(idx)

    def compile_continue(self):
        if not self._loop_stack:
            raise RuntimeError("Error: 'continuar' solo puede usarse dentro de un bucle")
        self.consume(Token.CONTINUAR)
        loop_info = self._loop_stack[-1]
        self.emit(OpCode.OP_JUMP)
        idx = self.emit(0)
        loop_info['continues'].append(idx)

    # ---------------------------------------------------------------
    # Sentencia identificador (reasignacion, llamada, acceso lista)
    # ---------------------------------------------------------------

    _COMPOUND_OPS = {
        Token.MAS_IGUAL: OpCode.OP_ADD,
        Token.MENOS_IGUAL: OpCode.OP_SUB,
        Token.POR_IGUAL: OpCode.OP_MUL,
        Token.ENTRE_IGUAL: OpCode.OP_DIV,
        Token.MOD_IGUAL: OpCode.OP_MOD,
    }

    def compile_identifier_statement(self):
        var_name = self._consume_identifier()
        next_type = self.current_token()[0]

        if next_type == Token.ASIGNACION:
            self._compile_reassignment(var_name)
        elif next_type in self._COMPOUND_OPS:
            self._compile_compound_assignment(var_name, next_type)
        elif next_type == Token.CORCHETE_IZQ:
            self._compile_list_assignment(var_name)
        elif next_type == Token.PUNTO:
            self._compile_property_statement(var_name)
        elif next_type == Token.PAREN_IZQ:
            self._compile_function_call(var_name)
        else:
            raise RuntimeError(f"Sentencia incompleta o invalida: {var_name}")

    # Casos internos de sentencia identificador
    # .................................................

    def _compile_compound_assignment(self, var_name, token_type):
        op = self._COMPOUND_OPS[token_type]
        self.pos += 1  # consume the compound operator
        self._load_var(var_name)
        self.expression()
        self.emit(op)

        if var_name in self._global_vars and var_name in self.global_symbols:
            self.emit(OpCode.OP_STORE_GLOBAL)
            self.emit(self.global_symbols[var_name])
        elif var_name in self.symbols:
            store_op = OpCode.OP_STORE_GLOBAL if self.symbols is self.global_symbols else OpCode.OP_STORE
            self.emit(store_op)
            self.emit(self.symbols[var_name])
        elif var_name in self.global_symbols:
            self.emit(OpCode.OP_STORE_GLOBAL)
            self.emit(self.global_symbols[var_name])
        else:
            self.symbols[var_name] = len(self.symbols)
            if self.symbols is self.global_symbols:
                self.global_symbols[var_name] = self.symbols[var_name]
            if self.symbols is self.global_symbols:
                self.emit(OpCode.OP_STORE_GLOBAL)
            else:
                self.emit(OpCode.OP_STORE)
            self.emit(self.symbols[var_name])

    def _compile_reassignment(self, var_name):
        self.consume(Token.ASIGNACION)
        self.expression()

        if var_name in self._global_vars and var_name in self.global_symbols:
            self.emit(OpCode.OP_STORE_GLOBAL)
            self.emit(self.global_symbols[var_name])
        elif var_name in self.symbols:
            opc = OpCode.OP_STORE_GLOBAL if self.symbols is self.global_symbols else OpCode.OP_STORE
            self.emit(opc)
            self.emit(self.symbols[var_name])
        elif var_name in self.global_symbols:
            self.emit(OpCode.OP_STORE_GLOBAL)
            self.emit(self.global_symbols[var_name])
        else:
            # Crear nueva variable en scope actual
            self.symbols[var_name] = len(self.symbols)
            if self.symbols is self.global_symbols:
                self.global_symbols[var_name] = self.symbols[var_name]
            if self.symbols is self.global_symbols:
                self.emit(OpCode.OP_STORE_GLOBAL)
            else:
                self.emit(OpCode.OP_STORE)
            self.emit(self.symbols[var_name])

    def _compile_list_assignment(self, var_name):
        self._load_var(var_name)
        self.consume(Token.CORCHETE_IZQ)
        self.expression()
        self.consume(Token.CORCHETE_DER)
        self.consume(Token.ASIGNACION)
        self.expression()
        self.emit(OpCode.OP_SET_INDEX)

    def _var_exists(self, var_name):
        """Verifica si una variable existe en el scope actual o global."""
        return var_name in self.symbols or var_name in self.global_symbols

    def _load_var(self, var_name):
        """Emite la instruccion de carga correcta para una variable."""
        if var_name in self._global_vars and var_name in self.global_symbols:
            self.emit(OpCode.OP_LOAD_GLOBAL)
            self.emit(self.global_symbols[var_name])
        elif var_name in self.symbols:
            opc = OpCode.OP_LOAD_GLOBAL if self.symbols is self.global_symbols else OpCode.OP_LOAD
            self.emit(opc)
            self.emit(self.symbols[var_name])
        elif var_name in self.global_symbols:
            self.emit(OpCode.OP_LOAD_GLOBAL)
            self.emit(self.global_symbols[var_name])
        else:
            opciones = (list(self.symbols.keys()) + list(self.global_symbols.keys()) + KEYWORDS_ALVZ)
            sugerencia = obtener_sugerencia(var_name, opciones)
            mensaje = f"Error: La variable '{var_name}' no existe"
            if sugerencia:
                mensaje += f". Quisiste decir '{sugerencia}'?"
            raise RuntimeError(mensaje)

    def _compile_property_statement(self, var_name):
        self._load_var(var_name)
        while self.current_token()[0] in (Token.PUNTO, Token.CORCHETE_IZQ):
            if self.current_token()[0] == Token.CORCHETE_IZQ:
                self.pos += 1
                if self.current_token()[0] == Token.DOS_PUNTOS:
                    const_zero = len(self.constants)
                    self.constants.append(0)
                    self.emit(OpCode.OP_CONSTANT)
                    self.emit(const_zero)
                else:
                    self.expression()
                if self.current_token()[0] == Token.DOS_PUNTOS:
                    self.consume(Token.DOS_PUNTOS)
                    if self.current_token()[0] == Token.CORCHETE_DER:
                        const_none = len(self.constants)
                        self.constants.append(None)
                        self.emit(OpCode.OP_CONSTANT)
                        self.emit(const_none)
                    else:
                        self.expression()
                    self.consume(Token.CORCHETE_DER)
                    self.emit(OpCode.OP_SLICE)
                else:
                    self.consume(Token.CORCHETE_DER)
                    self.emit(OpCode.OP_GET_INDEX)
                continue

            self.consume(Token.PUNTO)
            prop_name = self.consume(Token.IDENTIFICADOR)

            if self.current_token()[0] == Token.CORCHETE_IZQ:
                const_index = self._add_constant(prop_name)
                self.emit(OpCode.OP_CONSTANT)
                self.emit(const_index)
                self.emit(OpCode.OP_GET_ATTR)
                self.pos += 1
                if self.current_token()[0] == Token.DOS_PUNTOS:
                    const_zero = len(self.constants)
                    self.constants.append(0)
                    self.emit(OpCode.OP_CONSTANT)
                    self.emit(const_zero)
                else:
                    self.expression()
                if self.current_token()[0] == Token.DOS_PUNTOS:
                    self.consume(Token.DOS_PUNTOS)
                    if self.current_token()[0] == Token.CORCHETE_DER:
                        const_none = len(self.constants)
                        self.constants.append(None)
                        self.emit(OpCode.OP_CONSTANT)
                        self.emit(const_none)
                    else:
                        self.expression()
                    self.consume(Token.CORCHETE_DER)
                    self.emit(OpCode.OP_SLICE)
                else:
                    self.consume(Token.CORCHETE_DER)
                    self.emit(OpCode.OP_GET_INDEX)
                continue
            elif self.current_token()[0] == Token.PUNTO:
                # Bajar mas niveles
                const_index = self._add_constant(prop_name)
                self.emit(OpCode.OP_CONSTANT)
                self.emit(const_index)
                self.emit(OpCode.OP_GET_ATTR)
            elif self.current_token()[0] == Token.ASIGNACION:
                self.consume(Token.ASIGNACION)
                self.expression()
                const_index = self._add_constant(prop_name)
                self.emit(OpCode.OP_CONSTANT)
                self.emit(const_index)
                self.emit(OpCode.OP_SET_ATTR)
                break
            elif self.current_token()[0] == Token.PAREN_IZQ:
                # Llamada a metodo
                const_index = self._add_constant(prop_name)
                self.emit(OpCode.OP_CONSTANT)
                self.emit(const_index)
                self.emit(OpCode.OP_GET_ATTR)
                self.consume(Token.PAREN_IZQ)
                num_args = self._parse_arguments()
                self.consume(Token.PAREN_DER)
                self.emit(OpCode.OP_CALL)
                self.emit(0)
                self.emit(num_args)
                self.emit(0)
                self.emit(OpCode.OP_POP)  # Resultado no usado como sentencia
                break
            else:
                raise RuntimeError(f"Error de sintaxis: Se esperaba '.' o '=' despues de '{prop_name}'")

    def _compile_function_call(self, var_name):
        self.consume(Token.PAREN_IZQ)
        num_args = 0
        if self.current_token()[0] != Token.PAREN_DER:
            self.expression()
            num_args += 1
            while self.current_token()[0] == Token.COMA:
                self.pos += 1
                self.expression()
                num_args += 1
        self.consume(Token.PAREN_DER)

        if var_name == "iniciar_servidor":
            self.emit(OpCode.OP_START_SERVER)
            self.emit(OpCode.OP_POP)
            return

        if var_name in self.functions:
            func_info = self.functions[var_name]
            func_addr, expected_args = func_info[0], func_info[1]
            is_async = func_info[3] if len(func_info) > 3 else False
            if num_args != expected_args:
                raise RuntimeError(
                    f"Error: La funcion '{var_name}' esperaba {expected_args} argumentos, "
                    f"pero recibio {num_args}"
                )
            call_op = OpCode.OP_ASYNC_CALL if is_async else OpCode.OP_CALL
            self.emit(call_op)
            self.emit(func_addr)
            self.emit(num_args)
            self.emit(0)
            self.emit(OpCode.OP_POP)
        elif self._var_exists(var_name):
            self._load_var(var_name)
            self.emit(OpCode.OP_CALL)
            self.emit(0)
            self.emit(num_args)
            self.emit(0)
            self.emit(OpCode.OP_POP)
        else:
            opciones = list(self.functions.keys()) + KEYWORDS_ALVZ
            sugerencia = obtener_sugerencia(var_name, opciones)
            mensaje = f"Error: La funcion '{var_name}' no existe"
            if sugerencia:
                mensaje += f". Quisiste decir '{sugerencia}'?"
            raise RuntimeError(mensaje)

    def _parse_arguments(self):
        num_args = 0
        if self.current_token()[0] != Token.PAREN_DER:
            self.expression()
            num_args += 1
            while self.current_token()[0] == Token.COMA:
                self.pos += 1
                self.expression()
                num_args += 1
        return num_args

    # ---------------------------------------------------------------
    # Compilacion de import
    # ---------------------------------------------------------------

    def compile_import(self):
        self.consume(Token.IMPORTAR)
        filename = self.consume(Token.STRING)

        import os

        # Buscar archivo: primero en CWD, luego en stdlib del paquete
        paths_to_try = [filename]
        if not filename.endswith('.alvz'):
            paths_to_try.append(filename + '.alvz')
        stdlib_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'stdlib')
        paths_to_try.append(os.path.join(stdlib_dir, filename))
        if not filename.endswith('.alvz'):
            paths_to_try.append(os.path.join(stdlib_dir, filename + '.alvz'))

        # Buscar en paquetes instalados
        try:
            from .package_manager import PACKAGES_DIR
            pkg_path = os.path.join(PACKAGES_DIR, filename, filename + '.alvz')
            paths_to_try.append(pkg_path)
            pkg_path2 = os.path.join(PACKAGES_DIR, filename, f"{filename}.alvz")
            if pkg_path2 != pkg_path:
                paths_to_try.append(pkg_path2)
        except Exception:
            pass

        imported_code = None
        opened_path = None
        for p in paths_to_try:
            try:
                with open(p, 'r', encoding='utf-8-sig') as f:
                    imported_code = f.read()
                    opened_path = p
                    break
            except Exception:
                continue

        if imported_code is None:
            raise RuntimeError(f"Error al importar '{filename}': archivo no encontrado")

        # Compilar archivo importado
        from .lexer import Lexer as LexerClass
        lexer = LexerClass(imported_code)
        tokens = lexer.tokenize()

        parser = self.__class__(tokens)
        parser.functions = {}
        parser.functions.update(self.functions)
        parser.global_symbols = self.global_symbols
        parser.symbols = self.global_symbols
        parser.constants = self.constants
        if not hasattr(self, 'static_globals'):
            self.static_globals = {}
        parser.static_globals = self.static_globals

        parser._pre_scan_functions()

        jump_offset = len(self.bytecode)
        existing_funcs = set(self.functions.keys())

        while parser.current_token()[0] != Token.EOF:
            parser.compile_statement()

        imported_bytecode = parser.bytecode

        # Ajustar direcciones de salto
        i = 0
        while i < len(imported_bytecode):
            op = imported_bytecode[i]
            if op in (OpCode.OP_JUMP, OpCode.OP_JUMP_IF_FALSE, OpCode.OP_JUMP_IF_TRUE, OpCode.OP_TRY_PUSH):
                imported_bytecode[i + 1] += jump_offset
                i += 2
            elif op == OpCode.OP_CALL:
                if imported_bytecode[i + 1] != 0:
                    imported_bytecode[i + 1] += jump_offset
                i += 3
            elif op == OpCode.OP_MAKE_FUNC:
                imported_bytecode[i + 1] += jump_offset
                i += 3
            elif op in (OpCode.OP_CONSTANT, OpCode.OP_CLASS, OpCode.OP_NEW,
                        OpCode.OP_STORE, OpCode.OP_LOAD,
                        OpCode.OP_STORE_GLOBAL, OpCode.OP_LOAD_GLOBAL):
                i += 2
            else:
                i += 1

        # Registrar funciones importadas con direcciones absolutas
        for name in parser.functions:
            if name not in existing_funcs:
                finfo = parser.functions[name]
                if len(finfo) >= 4:
                    addr, nargs, params, is_async = finfo
                else:
                    addr, nargs, params = finfo
                    is_async = False
                self.functions[name] = (addr + jump_offset, nargs, params, is_async)

        # Remover HALT final si existe
        if imported_bytecode and imported_bytecode[-1] == OpCode.OP_HALT:
            imported_bytecode.pop()

        self.bytecode.extend(imported_bytecode)
        for line_ip in parser.line_map:
            self.line_map[line_ip + jump_offset] = parser.line_map[line_ip]
        self.constants = parser.constants

    # ---------------------------------------------------------------
    # Global keyword
    # ---------------------------------------------------------------

    def compile_global(self):
        self.consume(Token.GLOBAL)
        var_name = self._consume_identifier()
        self._add_global_var(var_name)
        while self.current_token()[0] == Token.COMA:
            self.pos += 1
            var_name = self._consume_identifier()
            self._add_global_var(var_name)

    def _add_global_var(self, var_name):
        self._global_vars.add(var_name)
        if var_name not in self.global_symbols:
            self.global_symbols[var_name] = len(self.global_symbols)

    # ---------------------------------------------------------------
    # Asignaciones y Expresiones
    # ---------------------------------------------------------------

    def compile_assignment(self):
        t_t, _, l = self.current_token()  # noqa: E741
        self.consume(Token.VARIABLE)
        var_name = self._consume_identifier()

        var_type = None
        if self.current_token()[0] == Token.DOS_PUNTOS:
            self.pos += 1
            var_type = self._consume_identifier()
            if not hasattr(self, 'var_types'):
                self.var_types = {}
            self.var_types[var_name] = var_type

        if var_name in self._global_vars:
            if var_name not in self.global_symbols:
                self.global_symbols[var_name] = len(self.global_symbols)
            idx = self.global_symbols[var_name]
        elif var_name not in self.symbols:
            self.symbols[var_name] = len(self.symbols)
        idx = self.symbols[var_name] if var_name not in self._global_vars else self.global_symbols[var_name]
        if self.symbols is self.global_symbols:
            self.global_symbols[var_name] = idx

        self.consume(Token.ASIGNACION)

        # Soporte pre-inicializacion de constantes globales
        if (self.symbols is self.global_symbols and
                self.pos < len(self.tokens)):
            t_type, val, _ = self.current_token()
            is_simple_const = False
            if t_type in (Token.NUMERO, Token.STRING, Token.VERDADERO, Token.FALSO, Token.NULO):
                next_t = self.tokens[self.pos + 1][0] if self.pos + 1 < len(self.tokens) else Token.EOF
                operadores = (
                    Token.MAS, Token.MENOS, Token.POR, Token.ENTRE, Token.MODULO,
                    Token.IGUAL_IGUAL, Token.DIFERENTE, Token.MAYOR, Token.MENOR,
                    Token.MAYOR_IGUAL, Token.MENOR_IGUAL, Token.Y, Token.O,
                )
                if next_t not in operadores:
                    is_simple_const = True

            if is_simple_const:
                if not hasattr(self, 'static_globals'):
                    self.static_globals = {}
                real_val = val
                if t_type == Token.VERDADERO:
                    real_val = True
                elif t_type == Token.FALSO:
                    real_val = False
                elif t_type == Token.NULO:
                    real_val = None
                self.static_globals[var_name] = real_val

        self.expression()
        if var_name in self._global_vars:
            self.emit(OpCode.OP_STORE_GLOBAL)
        elif self.symbols is self.global_symbols:
            self.emit(OpCode.OP_STORE_GLOBAL)
        else:
            self.emit(OpCode.OP_STORE)
        self.emit(idx)

    # ---------------------------------------------------------------
    # Expresiones (precedencia: o < y < comparacion < aritmetica < termino < factor)
    # ---------------------------------------------------------------

    def expression(self):
        """Maneja el operador logico O."""
        self.logical_and()
        while self.pos < len(self.tokens) and self.current_token()[0] == Token.O:
            self.pos += 1
            self.logical_and()
            self.emit(OpCode.OP_OR)

    def logical_and(self):
        """Maneja el operador logico Y."""
        self.comparison()
        while self.pos < len(self.tokens) and self.current_token()[0] == Token.Y:
            self.pos += 1
            self.comparison()
            self.emit(OpCode.OP_AND)

    def comparison(self):
        """Maneja comparaciones (==, !=, >, <, >=, <=) e instanceof."""
        self.arithmetic()
        while self.pos < len(self.tokens) and self.current_token()[0] in (
            Token.IGUAL_IGUAL, Token.DIFERENTE, Token.MAYOR, Token.MENOR,
            Token.MAYOR_IGUAL, Token.MENOR_IGUAL, Token.INSTANCIA,
        ):
            op, _, line = self.current_token()
            self.pos += 1
            if op == Token.INSTANCIA:
                class_name = self._consume_identifier()
                const_idx = len(self.constants)
                self.constants.append(class_name)
                self.emit(OpCode.OP_CONSTANT)
                self.emit(const_idx)
                self.emit(OpCode.OP_INSTANCEOF)
            else:
                self.arithmetic()
                if op == Token.IGUAL_IGUAL:
                    self.emit(OpCode.OP_EQ)
                elif op == Token.DIFERENTE:
                    self.emit(OpCode.OP_NE)
                elif op == Token.MAYOR:
                    self.emit(OpCode.OP_GT)
                elif op == Token.MENOR:
                    self.emit(OpCode.OP_LT)
                elif op == Token.MAYOR_IGUAL:
                    self.emit(OpCode.OP_GTE)
                elif op == Token.MENOR_IGUAL:
                    self.emit(OpCode.OP_LTE)

    def arithmetic(self):
        """Maneja suma y resta."""
        self.term()
        while self.pos < len(self.tokens) and self.current_token()[0] in (Token.MAS, Token.MENOS):
            op, _, line = self.current_token()
            self.pos += 1
            self.term()
            if op == Token.MAS:
                self.emit(OpCode.OP_ADD)
            else:
                self.emit(OpCode.OP_SUB)

    def term(self):
        """Maneja multiplicacion, division y modulo."""
        self.factor()
        while self.pos < len(self.tokens) and self.current_token()[0] in (Token.POR, Token.ENTRE, Token.MODULO):
            op, _, line = self.current_token()
            self.pos += 1
            self.factor()
            if op == Token.POR:
                self.emit(OpCode.OP_MUL)
            elif op == Token.ENTRE:
                self.emit(OpCode.OP_DIV)
            else:
                self.emit(OpCode.OP_MOD)

    def _add_constant(self, value):
        """Agrega una constante y devuelve su indice."""
        idx = len(self.constants)
        self.constants.append(value)
        return idx

