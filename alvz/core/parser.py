"""
Parser/Compilador completo para Alvz Language.

Extiende parser_base.Parser anadiendo los metodos que compilan
las sentencias del lenguaje (factor, bloques, definiciones, etc.)
"""

from .parser_base import Parser as _Parser, _IDENT_KEYWORDS
from .bytecode import OpCode
from .lexer import Token
from .errors import obtener_sugerencia, KEYWORDS_ALVZ


class Parser(_Parser):
    """Parser/Compilador completo con todos los metodos de compilacion."""

    # ============================================================
    # Factor (built-in functions, literales, variables, llamadas)
    # ============================================================

    def factor(self):
        """Maneja numeros, strings, booleanos, variables, funciones, listas y parentesis."""
        token_type, value, line = self.current_token()

        # Keywords que pueden usarse como identificadores (a, y, o, en, de)
        if token_type in _IDENT_KEYWORDS:
            token_type = Token.IDENTIFICADOR
            value = value  # token.value ya tiene el string correcto

        if token_type == Token.MENOS:
            self.pos += 1
            self.factor()
            self.emit(OpCode.OP_NEGATE)

        elif token_type == Token.NUMERO:
            self.pos += 1
            const_index = len(self.constants)
            self.constants.append(value)
            self.emit(OpCode.OP_CONSTANT)
            self.emit(const_index)

        elif token_type == Token.STRING:
            self.pos += 1
            const_index = len(self.constants)
            self.constants.append(value)
            self.emit(OpCode.OP_CONSTANT)
            self.emit(const_index)

        elif token_type == Token.STRING_TRIPLE:
            self.pos += 1
            const_index = len(self.constants)
            self.constants.append(value)
            self.emit(OpCode.OP_CONSTANT)
            self.emit(const_index)

        elif token_type == Token.VERDADERO:
            self.pos += 1
            const_index = len(self.constants)
            self.constants.append(True)
            self.emit(OpCode.OP_CONSTANT)
            self.emit(const_index)

        elif token_type == Token.FALSO:
            self.pos += 1
            const_index = len(self.constants)
            self.constants.append(False)
            self.emit(OpCode.OP_CONSTANT)
            self.emit(const_index)

        elif token_type == Token.NULO:
            self.pos += 1
            self.emit(OpCode.OP_NULL)

        elif token_type == Token.AGUARDAR:
            self.pos += 1
            self.factor()
            self.emit(OpCode.OP_AWAIT)

        elif token_type == Token.LEER:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_INPUT)

        elif token_type == Token.LEER_NUMERO:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_INPUT_NUM)

        elif token_type == Token.AZAR:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.COMA)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_RANDOM)

        elif token_type == Token.LONGITUD:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_LENGTH)

        elif token_type == Token.AGREGAR:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.COMA)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_APPEND)

        elif token_type == Token.ESPERAR:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_WAIT)

        elif token_type == Token.ENVIAR_WEB:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.COMA)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_WEB_SEND)

        elif token_type == Token.ESCRIBIR_ARCHIVO:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.COMA)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_WRITE_FILE)

        elif token_type == Token.MINUSCULAS:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_LOWER)

        elif token_type == Token.MAYUSCULAS:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_UPPER)

        elif token_type == Token.OBTENER_SALIDA:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_GET_OUTPUT)

        elif token_type == Token.SUPABASE_INSERTAR:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.COMA)
            self.expression()
            self.consume(Token.COMA)
            self.expression()
            self.consume(Token.COMA)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_SUPABASE_INSERT)

        elif token_type == Token.LEER_ARCHIVO:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_READ_FILE)

        elif token_type == Token.SUPABASE_CONSULTAR:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.COMA)
            self.expression()
            self.consume(Token.COMA)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_SUPABASE_SELECT)

        elif token_type == Token.JSON_DECODIFICAR:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_JSON_DECODE)

        elif token_type == Token.REDONDEAR:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_ROUND)

        elif token_type == Token.POTENCIA:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.COMA)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_POW)

        elif token_type == Token.RAIZ:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_SQRT)

        elif token_type == Token.TIEMPO:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_TIME)

        elif token_type == Token.JSON_CODIFICAR:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_JSON_ENCODE)

        elif token_type == Token.TIPO_KW:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_TYPE)

        elif token_type == Token.REEMPLAZAR:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.COMA)
            self.expression()
            self.consume(Token.COMA)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_REPLACE)

        elif token_type == Token.ABSOLUTO:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_ABS)

        elif token_type == Token.FECHA_ACTUAL:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_DATE_FORMAT)

        elif token_type == Token.DIVIDIR:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.COMA)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_STRING_SPLIT)

        elif token_type == Token.UNIR:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.COMA)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_STRING_JOIN)

        elif token_type == Token.A_NUMERO:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_TO_NUMBER)

        elif token_type == Token.REGEX_BUSCAR:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.COMA)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_REGEX_SEARCH)

        elif token_type == Token.INICIAR_SERVIDOR:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.COMA)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_START_SERVER)

        elif token_type == Token.ERROR_MSJ:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_ERROR_MSG)

        elif token_type == Token.NUEVO:
            self.pos += 1
            class_name = self._consume_identifier()
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

            const_index = len(self.constants)
            self.constants.append(class_name)
            self.emit(OpCode.OP_CONSTANT)
            self.emit(const_index)
            self.emit(OpCode.OP_NEW)
            self.emit(num_args)

        elif token_type == Token.CORCHETE_IZQ:
            self.pos += 1

            if self.current_token()[0] == Token.CORCHETE_DER:
                self.consume(Token.CORCHETE_DER)
                self.emit(OpCode.OP_LIST)
                self.emit(0)
                return

            # Detectar si es comprension de lista: [expr para cada var en source]
            lookahead = self.pos
            is_list_comp = False
            loop_var_lookahead = None
            para_pos = None
            body_start = self.pos
            while lookahead < len(self.tokens):
                tt = self.tokens[lookahead][0]
                if tt == Token.PARA:
                    para_pos = lookahead
                    is_list_comp = True
                    for i in range(lookahead, min(lookahead + 5, len(self.tokens))):
                        if self.tokens[i][0] == Token.CADA:
                            if i + 1 < len(self.tokens):
                                loop_var_lookahead = self.tokens[i + 1][1]
                            break
                    break
                if tt in (Token.CORCHETE_DER, Token.EOF):
                    break
                lookahead += 1

            if is_list_comp and loop_var_lookahead:
                if loop_var_lookahead not in self.symbols:
                    self.symbols[loop_var_lookahead] = len(self.symbols)

            if is_list_comp:
                self.pos = para_pos
            else:
                self.expression()

            if self.current_token()[0] == Token.PARA:
                self.consume(Token.PARA)
                self.consume(Token.CADA)
                loop_var = self._consume_identifier()
                self.consume(Token.EN)

                source_idx = len(self.bytecode)

                self.expression()

                list_name = f"_lc_list_{loop_var}"
                if list_name not in self.symbols:
                    self.symbols[list_name] = len(self.symbols)
                list_var_idx = self.symbols[list_name]
                opc = OpCode.OP_STORE_GLOBAL if self.symbols is self.global_symbols else OpCode.OP_STORE
                self.emit(opc)
                self.emit(list_var_idx)

                idx_name = f"_lc_idx_{loop_var}"
                if idx_name not in self.symbols:
                    self.symbols[idx_name] = len(self.symbols)
                idx_var_idx = self.symbols[idx_name]
                const_zero = len(self.constants)
                self.constants.append(0)
                self.emit(OpCode.OP_CONSTANT)
                self.emit(const_zero)
                self.emit(opc)
                self.emit(idx_var_idx)

                result_name = f"_lc_res_{loop_var}"
                if result_name not in self.symbols:
                    self.symbols[result_name] = len(self.symbols)
                res_var_idx = self.symbols[result_name]
                self.emit(OpCode.OP_LIST)
                self.emit(0)
                self.emit(opc)
                self.emit(res_var_idx)

                loop_start = len(self.bytecode)
                self.consume(Token.CORCHETE_DER)

                load_opc = OpCode.OP_LOAD_GLOBAL if self.symbols is self.global_symbols else OpCode.OP_LOAD
                self.emit(load_opc)
                self.emit(idx_var_idx)
                self.emit(load_opc)
                self.emit(list_var_idx)
                self.emit(OpCode.OP_LENGTH)
                self.emit(OpCode.OP_LT)

                exit_jump = self.emit(OpCode.OP_JUMP_IF_FALSE)
                exit_offset = self.emit(0)

                self.emit(load_opc)
                self.emit(list_var_idx)
                self.emit(load_opc)
                self.emit(idx_var_idx)
                self.emit(OpCode.OP_GET_INDEX)

                if loop_var not in self.symbols:
                    self.symbols[loop_var] = len(self.symbols)
                user_var_idx = self.symbols[loop_var]
                self.emit(opc)
                self.emit(user_var_idx)

                self.emit(load_opc)
                self.emit(res_var_idx)

                saved_pos = self.pos
                self.pos = body_start
                self.expression()
                self.pos = saved_pos

                self.emit(OpCode.OP_APPEND)
                self.emit(OpCode.OP_POP)

                self.emit(load_opc)
                self.emit(idx_var_idx)
                const_one = len(self.constants)
                self.constants.append(1)
                self.emit(OpCode.OP_CONSTANT)
                self.emit(const_one)
                self.emit(OpCode.OP_ADD)
                self.emit(opc)
                self.emit(idx_var_idx)

                self.emit(OpCode.OP_JUMP)
                self.emit(loop_start)
                self.patch(exit_offset, len(self.bytecode))

                self.emit(load_opc)
                self.emit(res_var_idx)
            else:
                num_elements = 1
                while self.pos < len(self.tokens) and self.current_token()[0] == Token.COMA:
                    self.pos += 1
                    self.expression()
                    num_elements += 1
                self.consume(Token.CORCHETE_DER)
                self.emit(OpCode.OP_LIST)
                self.emit(num_elements)

        elif token_type == Token.LLAVE_IZQ:
            self.pos += 1
            num_pairs = 0
            if self.pos < len(self.tokens) and self.current_token()[0] != Token.LLAVE_DER:
                self.expression()
                self.consume(Token.DOS_PUNTOS)
                self.expression()
                num_pairs += 1
                while self.pos < len(self.tokens) and self.current_token()[0] == Token.COMA:
                    self.pos += 1
                    self.expression()
                    self.consume(Token.DOS_PUNTOS)
                    self.expression()
                    num_pairs += 1
            self.consume(Token.LLAVE_DER)
            self.emit(OpCode.OP_DICT)
            self.emit(num_pairs)

        elif token_type == Token.SUPER:
            self.pos += 1
            self.consume(Token.PUNTO)
            method_name = self.consume(Token.IDENTIFICADOR)
            parent_name = getattr(self, 'super_class_parent', None)
            if not parent_name:
                raise RuntimeError(
                    "Error: 'super' solo puede usarse en metodos de clases con herencia"
                )
            const_method = len(self.constants)
            self.constants.append(method_name)
            const_parent = len(self.constants)
            self.constants.append(parent_name)
            self.emit(OpCode.OP_LOAD)
            self.emit(0)
            self.emit(OpCode.OP_CONSTANT)
            self.emit(const_method)
            self.emit(OpCode.OP_CONSTANT)
            self.emit(const_parent)
            self.emit(OpCode.OP_SUPER_ATTR)
            if self.pos < len(self.tokens) and self.current_token()[0] == Token.PAREN_IZQ:
                self.consume(Token.PAREN_IZQ)
                num_args = 0
                if self.pos < len(self.tokens) and self.current_token()[0] != Token.PAREN_DER:
                    self.expression()
                    num_args += 1
                    while self.pos < len(self.tokens) and self.current_token()[0] == Token.COMA:
                        self.pos += 1
                        self.expression()
                        num_args += 1
                self.consume(Token.PAREN_DER)
                self.emit(OpCode.OP_CALL)
                self.emit(0)
                self.emit(num_args)
                self.emit(0)

        elif token_type == Token.SOLICITUD_HTTP:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.COMA)
            self.expression()
            self.consume(Token.COMA)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_SOLICITUD_HTTP)

        elif token_type == Token.SQLITE_ABRIR:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_SQLITE_ABRIR)

        elif token_type == Token.SQLITE_EJECUTAR:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.COMA)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_SQLITE_EJECUTAR)

        elif token_type == Token.SQLITE_CONSULTAR:
            self.pos += 1
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.COMA)
            self.expression()
            self.consume(Token.PAREN_DER)
            self.emit(OpCode.OP_SQLITE_CONSULTAR)

        elif token_type == Token.IDENTIFICADOR:
            self.pos += 1
            next_type = self.current_token()[0] if self.pos < len(self.tokens) else Token.EOF

            if next_type == Token.PAREN_IZQ:
                self.pos += 1
                num_args = 0

                # Para llamada a funcion desde variable: cargar descriptor ANTES de los args
                # para que la pila quede [..., descriptor, arg1, arg2, ...]
                loaded_var = False
                if value not in self.functions and self._var_exists(value):
                    self._load_var(value)
                    loaded_var = True

                if self.pos < len(self.tokens) and self.current_token()[0] != Token.PAREN_DER:
                    self.expression()
                    num_args += 1
                    while self.pos < len(self.tokens) and self.current_token()[0] == Token.COMA:
                        self.pos += 1
                        self.expression()
                        num_args += 1
                self.consume(Token.PAREN_DER)

                if value in self.functions:
                    func_addr, expected_args, _, is_async = self.functions[value]
                    if num_args != expected_args:
                        raise RuntimeError(
                            f"Error: La funcion '{value}' esperaba {expected_args} "
                            f"argumentos, pero recibio {num_args}"
                        )
                    call_op = OpCode.OP_ASYNC_CALL if is_async else OpCode.OP_CALL
                    self.emit(call_op)
                    self.emit(func_addr)
                    self.emit(num_args)
                    self.emit(0)
                elif loaded_var or self._var_exists(value):
                    if not loaded_var:
                        self._load_var(value)
                    self.emit(OpCode.OP_CALL)
                    self.emit(0)
                    self.emit(num_args)
                    self.emit(0)
                else:
                    opciones = list(self.functions.keys()) + KEYWORDS_ALVZ
                    sugerencia = obtener_sugerencia(value, opciones)
                    mensaje = f"Error: La funcion '{value}' no existe"
                    if sugerencia:
                        mensaje += f". Quisiste decir '{sugerencia}'?"
                    raise RuntimeError(mensaje)

            elif next_type == Token.CORCHETE_IZQ:
                if value in self.symbols:
                    opc = OpCode.OP_LOAD_GLOBAL if self.symbols is self.global_symbols else OpCode.OP_LOAD
                    self.emit(opc)
                    self.emit(self.symbols[value])
                elif value in self.global_symbols:
                    self.emit(OpCode.OP_LOAD_GLOBAL)
                    self.emit(self.global_symbols[value])
                else:
                    raise RuntimeError(f"Error: La variable '{value}' no existe")

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

            elif next_type == Token.PUNTO:
                if hasattr(self, 'defined_classes') and value in self.defined_classes:
                    self._compile_static_call(value)
                    return

                if value in self.symbols:
                    opc = OpCode.OP_LOAD_GLOBAL if self.symbols is self.global_symbols else OpCode.OP_LOAD
                    self.emit(opc)
                    self.emit(self.symbols[value])
                elif value in self.global_symbols:
                    self.emit(OpCode.OP_LOAD_GLOBAL)
                    self.emit(self.global_symbols[value])
                else:
                    raise RuntimeError(f"Error: La variable '{value}' no existe")

                while self.pos < len(self.tokens) and self.current_token()[0] == Token.PUNTO:
                    self.consume(Token.PUNTO)
                    prop_name = self._consume_identifier()

                    const_index = len(self.constants)
                    self.constants.append(prop_name)
                    self.emit(OpCode.OP_CONSTANT)
                    self.emit(const_index)
                    self.emit(OpCode.OP_GET_ATTR)

                    if self.pos < len(self.tokens) and self.current_token()[0] == Token.PAREN_IZQ:
                        self.consume(Token.PAREN_IZQ)
                        num_args = 0
                        if self.pos < len(self.tokens) and self.current_token()[0] != Token.PAREN_DER:
                            self.expression()
                            num_args += 1
                            while self.pos < len(self.tokens) and self.current_token()[0] == Token.COMA:
                                self.pos += 1
                                self.expression()
                                num_args += 1
                        self.consume(Token.PAREN_DER)

                        self.emit(OpCode.OP_CALL)
                        self.emit(0)
                        self.emit(num_args)
                        self.emit(0)

                    if self.pos < len(self.tokens) and self.current_token()[0] == Token.CORCHETE_IZQ:
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

            else:
                if value in self.symbols:
                    opc = OpCode.OP_LOAD_GLOBAL if self.symbols is self.global_symbols else OpCode.OP_LOAD
                    self.emit(opc)
                    self.emit(self.symbols[value])
                elif value in self.global_symbols:
                    self.emit(OpCode.OP_LOAD_GLOBAL)
                    self.emit(self.global_symbols[value])
                elif value in self.functions:
                    const_idx = len(self.constants)
                    self.constants.append(('FUNC_NAME', value))
                    self.emit(OpCode.OP_CONSTANT)
                    self.emit(const_idx)
                elif hasattr(self, 'static_globals') and value in self.static_globals:
                    const_val = self.static_globals[value]
                    const_index = len(self.constants)
                    self.constants.append(const_val)
                    self.emit(OpCode.OP_CONSTANT)
                    self.emit(const_index)
                else:
                    opciones = (
                        list(self.symbols.keys())
                        + list(self.global_symbols.keys())
                        + list(self.functions.keys())
                        + KEYWORDS_ALVZ
                    )
                    sugerencia = obtener_sugerencia(value, opciones)
                    mensaje = f"Error: La variable '{value}' no existe"
                    if sugerencia:
                        mensaje += f". Quisiste decir '{sugerencia}'?"
                    raise RuntimeError(mensaje)

        elif token_type == Token.FUNCION:
            # Anonymous function: funcion(args) { cuerpo }
            self.pos += 1
            self._compile_anonymous_function()

        elif token_type == Token.PAREN_IZQ:
            self.pos += 1
            self.expression()
            self.consume(Token.PAREN_DER)

        else:
            raise RuntimeError(
                f"Error de sintaxis (linea {line}): "
                f"Se esperaba un valor o expresion, pero se encontro {token_type}"
            )

        # Handle chained access for any factor: [...], .xxx
        self._compile_chained_access()

    # ============================================================
    # Sentencias de compilacion
    # ============================================================

    def compile_print(self):
        self.consume(Token.IMPRIMIR)
        next_type = self.current_token()[0]
        if next_type == Token.PAREN_IZQ:
            self.consume(Token.PAREN_IZQ)
            self.expression()
            self.consume(Token.PAREN_DER)
        else:
            self.expression()
        self.emit(OpCode.OP_PRINT)

    def compile_clear(self):
        self.consume(Token.LIMPIAR)
        next_type = self.current_token()[0]
        if next_type == Token.PAREN_IZQ:
            self.consume(Token.PAREN_IZQ)
            self.consume(Token.PAREN_DER)
        self.emit(OpCode.OP_CLEAR)

    def compile_agregar_statement(self):
        self.factor()
        self.emit(OpCode.OP_POP)

    def compile_longitud_statement(self):
        self.factor()
        self.emit(OpCode.OP_POP)

    def compile_esperar_statement(self):
        self.factor()

    def compile_enviar_web_statement(self):
        self.factor()
        self.emit(OpCode.OP_POP)

    def compile_escribir_archivo_statement(self):
        self.factor()
        self.emit(OpCode.OP_POP)

    # ============================================================
    # Funciones
    # ============================================================

    def compile_function_definition(self):
        self.consume(Token.FUNCION)

        is_async = False
        if self.current_token()[0] == Token.ASYNC:
            self.pos += 1
            is_async = True

        func_name = self._consume_identifier()

        jump_op_idx = self.emit(OpCode.OP_JUMP)
        jump_offset_idx = self.emit(0)
        func_start_addr = len(self.bytecode)

        self.consume(Token.PAREN_IZQ)
        params = []
        param_types = []
        if self.current_token()[0] != Token.PAREN_DER:
            pname = self._consume_identifier()
            ptype = None
            if self.current_token()[0] == Token.DOS_PUNTOS:
                self.pos += 1
                ptype = self._consume_identifier()
            params.append(pname)
            param_types.append(ptype)
            while self.current_token()[0] == Token.COMA:
                self.pos += 1
                pname = self._consume_identifier()
                ptype = None
                if self.current_token()[0] == Token.DOS_PUNTOS:
                    self.pos += 1
                    ptype = self._consume_identifier()
                params.append(pname)
                param_types.append(ptype)
        self.consume(Token.PAREN_DER)

        return_type = None
        if self.current_token()[0] == Token.DOS_PUNTOS:
            self.pos += 1
            return_type = self._consume_identifier()

        if not hasattr(self, 'func_types'):
            self.func_types = {}
        self.func_types[func_name] = (param_types, return_type)

        if is_async:
            if not hasattr(self, 'async_funcs'):
                self.async_funcs = set()
            self.async_funcs.add(func_name)

        if is_async:
            if not hasattr(self, 'async_funcs'):
                self.async_funcs = set()
            self.async_funcs.add(func_name)

        old_symbols = self.symbols
        self.symbols = {name: i for i, name in enumerate(params)}
        self.functions[func_name] = (func_start_addr, len(params), params, is_async)

        self.consume(Token.LLAVE_IZQ)
        self.compile_block()
        self.consume(Token.LLAVE_DER)

        const_index = len(self.constants)
        self.constants.append(False)
        self.emit(OpCode.OP_CONSTANT)
        self.emit(const_index)
        self.emit(OpCode.OP_RETURN)

        self.symbols = old_symbols
        self.patch(jump_offset_idx, len(self.bytecode))

        if func_name not in self.global_symbols:
            self.global_symbols[func_name] = len(self.global_symbols)
        func_var_idx = self.global_symbols[func_name]

        self.emit(OpCode.OP_MAKE_FUNC)
        self.emit(func_start_addr)
        self.emit(len(params))
        self.emit(OpCode.OP_STORE_GLOBAL)
        self.emit(func_var_idx)

    def _compile_anonymous_function(self):
        """Compila una funcion anonima como expresion: funcion(args) { cuerpo }"""
        is_async = False
        if self.current_token()[0] == Token.ASYNC:
            self.pos += 1
            is_async = True

        anon_id = getattr(self, '_anon_counter', 0) + 1
        self._anon_counter = anon_id
        func_name = f'__anon_{anon_id}'

        jump_op_idx = self.emit(OpCode.OP_JUMP)
        jump_offset_idx = self.emit(0)
        func_start_addr = len(self.bytecode)

        self.consume(Token.PAREN_IZQ)
        params = []
        param_types = []
        if self.current_token()[0] != Token.PAREN_DER:
            pname = self._consume_identifier()
            ptype = None
            if self.current_token()[0] == Token.DOS_PUNTOS:
                self.pos += 1
                ptype = self._consume_identifier()
            params.append(pname)
            param_types.append(ptype)
            while self.current_token()[0] == Token.COMA:
                self.pos += 1
                pname = self._consume_identifier()
                ptype = None
                if self.current_token()[0] == Token.DOS_PUNTOS:
                    self.pos += 1
                    ptype = self._consume_identifier()
                params.append(pname)
                param_types.append(ptype)
        self.consume(Token.PAREN_DER)

        return_type = None
        if self.current_token()[0] == Token.DOS_PUNTOS:
            self.pos += 1
            return_type = self._consume_identifier()

        if not hasattr(self, 'func_types'):
            self.func_types = {}
        self.func_types[func_name] = (param_types, return_type)

        if is_async:
            if not hasattr(self, 'async_funcs'):
                self.async_funcs = set()
            self.async_funcs.add(func_name)

        old_symbols = self.symbols
        self.symbols = {name: i for i, name in enumerate(params)}
        self.functions[func_name] = (func_start_addr, len(params), params, is_async)

        self.consume(Token.LLAVE_IZQ)
        self.compile_block()
        self.consume(Token.LLAVE_DER)

        const_index = len(self.constants)
        self.constants.append(False)
        self.emit(OpCode.OP_CONSTANT)
        self.emit(const_index)
        self.emit(OpCode.OP_RETURN)

        self.symbols = old_symbols
        self.patch(jump_offset_idx, len(self.bytecode))

        self.emit(OpCode.OP_MAKE_FUNC)
        self.emit(func_start_addr)
        self.emit(len(params))

    def compile_return(self):
        self.consume(Token.RETORNAR)
        tokens_no_expresion = (
            Token.LLAVE_DER, Token.EOF, Token.VARIABLE, Token.IMPRIMIR,
            Token.SI, Token.SINO, Token.MIENTRAS, Token.LIMPIAR,
            Token.RETORNAR,
        )

        if self.current_token()[0] not in tokens_no_expresion:
            self.expression()
        else:
            const_index = len(self.constants)
            self.constants.append(False)
            self.emit(OpCode.OP_CONSTANT)
            self.emit(const_index)

        self.emit(OpCode.OP_RETURN)

    # ============================================================
    # Control de flujo
    # ============================================================

    def compile_if(self):
        self.consume(Token.SI)

        tiene_parentesis = self.current_token()[0] == Token.PAREN_IZQ
        if tiene_parentesis:
            self.consume(Token.PAREN_IZQ)

        self.expression()

        if tiene_parentesis:
            self.consume(Token.PAREN_DER)

        jump_if_false_op_idx = self.emit(OpCode.OP_JUMP_IF_FALSE)
        jump_if_false_offset_idx = self.emit(0)

        self.consume(Token.LLAVE_IZQ)
        self.compile_block()
        self.consume(Token.LLAVE_DER)

        if self.current_token()[0] == Token.SINO:
            sino_pos = self.pos
            self.pos += 1
            if self.current_token()[0] == Token.SI:
                # sino si ... { ... } -> patch false jump, compile new if
                jump_sino_si_idx = self.emit(OpCode.OP_JUMP)
                jump_sino_si_offset_idx = self.emit(0)
                self.patch(jump_if_false_offset_idx, len(self.bytecode))
                self.compile_if()
                self.patch(jump_sino_si_offset_idx, len(self.bytecode))
            else:
                jump_op_idx = self.emit(OpCode.OP_JUMP)
                jump_offset_idx = self.emit(0)
                self.patch(jump_if_false_offset_idx, len(self.bytecode))
                self.consume(Token.LLAVE_IZQ)
                self.compile_block()
                self.consume(Token.LLAVE_DER)
                self.patch(jump_offset_idx, len(self.bytecode))
        else:
            self.patch(jump_if_false_offset_idx, len(self.bytecode))

    def compile_while(self):
        loop_start_idx = len(self.bytecode)

        self.consume(Token.MIENTRAS)

        tiene_parentesis = self.current_token()[0] == Token.PAREN_IZQ
        if tiene_parentesis:
            self.consume(Token.PAREN_IZQ)

        self.expression()

        if tiene_parentesis:
            self.consume(Token.PAREN_DER)

        exit_jump_op_idx = self.emit(OpCode.OP_JUMP_IF_FALSE)
        exit_jump_offset_idx = self.emit(0)

        loop_info = {'breaks': [], 'continues': [], 'continue_target': loop_start_idx}
        self._loop_stack.append(loop_info)

        self.consume(Token.LLAVE_IZQ)
        self.compile_block()
        self.consume(Token.LLAVE_DER)

        self._loop_stack.pop()

        self.emit(OpCode.OP_JUMP)
        self.emit(loop_start_idx)
        self.patch(exit_jump_offset_idx, len(self.bytecode))

        for idx in loop_info['breaks']:
            self.patch(idx, len(self.bytecode))
        for idx in loop_info['continues']:
            self.patch(idx, loop_start_idx)

    def compile_for(self):
        self.consume(Token.PARA)
        if self.current_token()[0] == Token.CADA:
            self.compile_for_each()
        else:
            self.compile_for_range()

    def compile_for_range(self):
        var_name = self._consume_identifier()
        self.consume(Token.DE)

        self.expression()
        if var_name not in self.symbols:
            self.symbols[var_name] = len(self.symbols)
        var_idx = self.symbols[var_name]
        opc = OpCode.OP_STORE_GLOBAL if self.symbols is self.global_symbols else OpCode.OP_STORE
        self.emit(opc)
        self.emit(var_idx)

        loop_start_idx = len(self.bytecode)
        self.consume(Token.A)

        load_opc = OpCode.OP_LOAD_GLOBAL if self.symbols is self.global_symbols else OpCode.OP_LOAD
        self.emit(load_opc)
        self.emit(var_idx)
        self.expression()
        self.emit(OpCode.OP_LTE)

        exit_jump_op_idx = self.emit(OpCode.OP_JUMP_IF_FALSE)
        exit_jump_offset_idx = self.emit(0)

        self.consume(Token.LLAVE_IZQ)

        loop_info = {'breaks': [], 'continues': [], 'continue_target': None}
        self._loop_stack.append(loop_info)
        self.compile_block()
        self._loop_stack.pop()

        self.consume(Token.LLAVE_DER)

        increment_start = len(self.bytecode)
        if loop_info['continue_target'] is None:
            loop_info['continue_target'] = increment_start

        self.emit(load_opc)
        self.emit(var_idx)
        const_index = len(self.constants)
        self.constants.append(1)
        self.emit(OpCode.OP_CONSTANT)
        self.emit(const_index)
        self.emit(OpCode.OP_ADD)
        self.emit(opc)
        self.emit(var_idx)

        self.emit(OpCode.OP_JUMP)
        self.emit(loop_start_idx)
        self.patch(exit_jump_offset_idx, len(self.bytecode))

        for idx in loop_info['breaks']:
            self.patch(idx, len(self.bytecode))
        for idx in loop_info['continues']:
            self.patch(idx, loop_info['continue_target'])

    def compile_for_each(self):
        self.consume(Token.CADA)
        var_name = self._consume_identifier()
        self.consume(Token.EN)

        self.expression()
        self.emit(OpCode.OP_DICT_KEYS)
        temp_list_name = f"_list_{var_name}"
        if temp_list_name not in self.symbols:
            self.symbols[temp_list_name] = len(self.symbols)
        list_var_idx = self.symbols[temp_list_name]

        opc = OpCode.OP_STORE_GLOBAL if self.symbols is self.global_symbols else OpCode.OP_STORE
        self.emit(opc)
        self.emit(list_var_idx)

        internal_idx_name = f"_idx_{var_name}"
        if internal_idx_name not in self.symbols:
            self.symbols[internal_idx_name] = len(self.symbols)
        idx_var_idx = self.symbols[internal_idx_name]

        const_zero_idx = len(self.constants)
        self.constants.append(0)
        self.emit(OpCode.OP_CONSTANT)
        self.emit(const_zero_idx)

        self.emit(opc)
        self.emit(idx_var_idx)

        loop_start_idx = len(self.bytecode)
        load_opc = OpCode.OP_LOAD_GLOBAL if self.symbols is self.global_symbols else OpCode.OP_LOAD

        self.emit(load_opc)
        self.emit(idx_var_idx)
        self.emit(load_opc)
        self.emit(list_var_idx)
        self.emit(OpCode.OP_LENGTH)
        self.emit(OpCode.OP_LT)

        exit_jump_op_idx = self.emit(OpCode.OP_JUMP_IF_FALSE)
        exit_jump_offset_idx = self.emit(0)

        self.emit(load_opc)
        self.emit(list_var_idx)
        self.emit(load_opc)
        self.emit(idx_var_idx)
        self.emit(OpCode.OP_GET_INDEX)

        if var_name not in self.symbols:
            self.symbols[var_name] = len(self.symbols)
        user_var_idx = self.symbols[var_name]
        self.emit(opc)
        self.emit(user_var_idx)

        self.consume(Token.LLAVE_IZQ)

        loop_info = {'breaks': [], 'continues': [], 'continue_target': None}
        self._loop_stack.append(loop_info)
        self.compile_block()
        self._loop_stack.pop()

        self.consume(Token.LLAVE_DER)

        increment_start = len(self.bytecode)
        if loop_info['continue_target'] is None:
            loop_info['continue_target'] = increment_start

        self.emit(load_opc)
        self.emit(idx_var_idx)
        const_one_idx = len(self.constants)
        self.constants.append(1)
        self.emit(OpCode.OP_CONSTANT)
        self.emit(const_one_idx)
        self.emit(OpCode.OP_ADD)
        self.emit(opc)
        self.emit(idx_var_idx)

        self.emit(OpCode.OP_JUMP)
        self.emit(loop_start_idx)
        self.patch(exit_jump_offset_idx, len(self.bytecode))

        for idx in loop_info['breaks']:
            self.patch(idx, len(self.bytecode))
        for idx in loop_info['continues']:
            self.patch(idx, loop_info['continue_target'])

    # ============================================================
    # Try / Catch
    # ============================================================

    def compile_try_catch(self):
        self.consume(Token.INTENTAR)

        self.emit(OpCode.OP_TRY_PUSH)
        handler_placeholder_idx = self.emit(0)

        self.consume(Token.LLAVE_IZQ)
        self.compile_block()
        self.consume(Token.LLAVE_DER)

        self.emit(OpCode.OP_TRY_POP)
        jump_over_catch_idx = self.emit(OpCode.OP_JUMP)
        jump_over_catch_offset_idx = self.emit(0)

        handler_addr = len(self.bytecode)
        self.patch(handler_placeholder_idx, handler_addr)

        self.consume(Token.CAPTURAR)
        self.consume(Token.LLAVE_IZQ)
        self.compile_block()
        self.consume(Token.LLAVE_DER)

        self.patch(jump_over_catch_offset_idx, len(self.bytecode))

    # ============================================================
    # Clases
    # ============================================================

    def _skip_expression(self):
        depth = 0
        while self.pos < len(self.tokens):
            t_type, _, _ = self.tokens[self.pos]
            if t_type in (Token.PAREN_IZQ, Token.CORCHETE_IZQ, Token.LLAVE_IZQ):
                depth += 1
            elif t_type == Token.PAREN_DER:
                if depth == 0:
                    break
                depth -= 1
            elif t_type in (Token.CORCHETE_DER,):
                if depth == 0:
                    break
                depth -= 1
            elif t_type == Token.LLAVE_DER:
                if depth == 0:
                    break
                depth -= 1
            elif depth == 0 and t_type in (Token.VARIABLE, Token.FUNCION, Token.PROPIEDAD, Token.EOF):
                break
            self.pos += 1

    def _compile_static_call(self, class_name):
        while self.pos < len(self.tokens) and self.current_token()[0] == Token.PUNTO:
            self.consume(Token.PUNTO)
            method_name = self._consume_identifier()
            class_info = self.defined_classes[class_name]
            parent_backup = class_name

            # Walk inheritance chain to find the static method
            found = None
            current = class_name
            while current:
                cinfo = self.defined_classes.get(current)
                if not cinfo:
                    break
                sm = cinfo.get('static_methods', {})
                if method_name in sm:
                    found = sm[method_name]
                    break
                current = cinfo.get('parent')
                if current and current not in self.defined_classes:
                    current = None

            if found:
                addr, expected_args = found
                if self.pos < len(self.tokens) and self.current_token()[0] == Token.PAREN_IZQ:
                    self.consume(Token.PAREN_IZQ)
                    num_args = 0
                    if self.pos < len(self.tokens) and self.current_token()[0] != Token.PAREN_DER:
                        self.expression()
                        num_args += 1
                        while self.pos < len(self.tokens) and self.current_token()[0] == Token.COMA:
                            self.pos += 1
                            self.expression()
                            num_args += 1
                    self.consume(Token.PAREN_DER)
                    if num_args != expected_args:
                        raise RuntimeError(
                            f"Error: El metodo estatico '{class_name}.{method_name}' "
                            f"esperaba {expected_args} argumentos, pero recibio {num_args}"
                        )
                    self.emit(OpCode.OP_CALL)
                    self.emit(addr)
                    self.emit(num_args)
                    self.emit(0)
                else:
                    const_idx = self._add_constant(('FUNC', addr, expected_args))
                    self.emit(OpCode.OP_CONSTANT)
                    self.emit(const_idx)
            else:
                raise RuntimeError(
                    f"Error: La clase '{class_name}' no tiene el metodo estatico '{method_name}'"
                )

    def compile_class_definition(self):
        self.consume(Token.CLASE)
        class_name = self._consume_identifier()

        parent_name = None
        if self.current_token()[0] == Token.DE:
            self.consume(Token.DE)
            parent_name = self._consume_identifier()

        self.consume(Token.LLAVE_IZQ)

        props = {}
        methods = {}
        static_methods = {}
        getters = {}
        setters = {}
        pending_inits = []

        while self.current_token()[0] != Token.LLAVE_DER:
            t_type, _, _ = self.current_token()
            if t_type == Token.VARIABLE:
                self.consume(Token.VARIABLE)
                prop_name = self._consume_identifier()
                self.consume(Token.ASIGNACION)
                t_val_type, val, _ = self.current_token()
                if t_val_type in (Token.NUMERO, Token.STRING, Token.VERDADERO, Token.FALSO):
                    peek = self.pos + 1
                    if peek < len(self.tokens) and self.tokens[peek][0] in (Token.VARIABLE, Token.FUNCION, Token.PROPIEDAD, Token.LLAVE_DER, Token.EOF):
                        props[prop_name] = val
                        self.pos += 1
                    else:
                        pending_inits.append((prop_name, self.pos))
                        self._skip_expression()
                else:
                    pending_inits.append((prop_name, self.pos))
                    self._skip_expression()
            elif t_type == Token.FUNCION:
                is_static = False
                self.consume(Token.FUNCION)
                if self.current_token()[0] == Token.ESTATICO:
                    self.consume(Token.ESTATICO)
                    is_static = True
                method_name = self._consume_identifier()

                jump_idx = self.emit(OpCode.OP_JUMP)
                jump_offset_idx = self.emit(0)
                method_start = len(self.bytecode)

                self.consume(Token.PAREN_IZQ)
                if is_static:
                    params = []
                else:
                    params = ['self']
                param_types = []
                if self.current_token()[0] != Token.PAREN_DER:
                    pname = self._consume_identifier()
                    ptype = None
                    if self.current_token()[0] == Token.DOS_PUNTOS:
                        self.pos += 1
                        ptype = self._consume_identifier()
                    params.append(pname)
                    param_types.append(ptype)
                    while self.current_token()[0] == Token.COMA:
                        self.pos += 1
                        pname = self._consume_identifier()
                        ptype = None
                        if self.current_token()[0] == Token.DOS_PUNTOS:
                            self.pos += 1
                            ptype = self._consume_identifier()
                        params.append(pname)
                        param_types.append(ptype)
                self.consume(Token.PAREN_DER)

                return_type = None
                if self.current_token()[0] == Token.DOS_PUNTOS:
                    self.pos += 1
                    return_type = self._consume_identifier()

                if not hasattr(self, 'func_types'):
                    self.func_types = {}
                self.func_types[method_name] = (param_types, return_type)

                old_symbols = self.symbols
                old_super_parent = getattr(self, 'super_class_parent', None)
                self.super_class_parent = parent_name
                self.symbols = {name: i for i, name in enumerate(params)}

                self.consume(Token.LLAVE_IZQ)
                self.compile_block()
                self.consume(Token.LLAVE_DER)

                self.emit(OpCode.OP_RETURN)
                self.symbols = old_symbols
                self.super_class_parent = old_super_parent
                self.patch(jump_offset_idx, len(self.bytecode))

                if is_static:
                    static_methods[method_name] = (method_start, len(params))
                else:
                    methods[method_name] = (method_start, len(params))
            elif t_type == Token.PROPIEDAD:
                self.consume(Token.PROPIEDAD)
                prop_name = self._consume_identifier()
                self.consume(Token.LLAVE_IZQ)

                while self.current_token()[0] != Token.LLAVE_DER:
                    if self.current_token()[0] == Token.OBTENER:
                        self.consume(Token.OBTENER)
                        self.consume(Token.LLAVE_IZQ)

                        old_sym = self.symbols
                        old_super = getattr(self, 'super_class_parent', None)
                        self.super_class_parent = parent_name
                        p = ['self']
                        self.symbols = {n: i for i, n in enumerate(p)}

                        jump_idx = self.emit(OpCode.OP_JUMP)
                        jump_off = self.emit(0)
                        gaddr = len(self.bytecode)

                        self.compile_block()
                        self.consume(Token.LLAVE_DER)
                        self.emit(OpCode.OP_RETURN)
                        self.symbols = old_sym
                        self.super_class_parent = old_super
                        self.patch(jump_off, len(self.bytecode))
                        getters[prop_name] = (gaddr, 1)

                    elif self.current_token()[0] == Token.ESTABLECER:
                        self.consume(Token.ESTABLECER)
                        self.consume(Token.PAREN_IZQ)
                        param_name = self._consume_identifier()
                        self.consume(Token.PAREN_DER)
                        self.consume(Token.LLAVE_IZQ)

                        old_sym = self.symbols
                        old_super = getattr(self, 'super_class_parent', None)
                        self.super_class_parent = parent_name
                        p = ['self', param_name]
                        self.symbols = {n: i for i, n in enumerate(p)}

                        jump_idx = self.emit(OpCode.OP_JUMP)
                        jump_off = self.emit(0)
                        sadd = len(self.bytecode)

                        self.compile_block()
                        self.consume(Token.LLAVE_DER)
                        self.emit(OpCode.OP_RETURN)
                        self.symbols = old_sym
                        self.super_class_parent = old_super
                        self.patch(jump_off, len(self.bytecode))
                        setters[prop_name] = (sadd, 2)
                    else:
                        self.pos += 1

                self.consume(Token.LLAVE_DER)
            else:
                self.pos += 1

        self.consume(Token.LLAVE_DER)

        if pending_inits:
            saved_pos = self.pos
            saved_symbols = self.symbols

            jump_idx = self.emit(OpCode.OP_JUMP)
            jump_offset_idx = self.emit(0)
            method_start = len(self.bytecode)

            params = ['self']
            self.symbols = {name: i for i, name in enumerate(params)}

            for prop_name, expr_start in pending_inits:
                self.pos = expr_start
                self.emit(OpCode.OP_LOAD)
                self.emit(0)
                const_idx = len(self.constants)
                self.constants.append(prop_name)
                self.expression()
                self.emit(OpCode.OP_CONSTANT)
                self.emit(const_idx)
                self.emit(OpCode.OP_SET_ATTR)

            self.emit(OpCode.OP_RETURN)
            self.symbols = saved_symbols
            self.patch(jump_offset_idx, len(self.bytecode))
            self.pos = saved_pos

            methods['__init_props'] = (method_start, len(params))

        if static_methods:
            static_methods_info = {name: (addr, n) for name, (addr, n) in static_methods.items()}
        else:
            static_methods_info = {}
        self.defined_classes[class_name] = {
            'static_methods': static_methods_info,
            'getters': getters,
            'setters': setters,
            'parent': parent_name,
        }

        const_index = len(self.constants)
        class_data = {'props': props, 'methods': methods, 'static_methods': static_methods, 'getters': getters, 'setters': setters, 'parent': parent_name}
        self.constants.append(class_data)

        self.emit(OpCode.OP_CLASS)
        name_const_idx = len(self.constants)
        self.constants.append(class_name)
        self.emit(name_const_idx)
        self.emit(const_index)

    # ============================================================
    # Bloque
    # ============================================================

    def _compile_chained_access(self):
        """Handle chained access for any value on stack: [...], .xxx"""
        while self.pos < len(self.tokens):
            t = self.current_token()[0]
            if t == Token.CORCHETE_IZQ:
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
            elif t == Token.PUNTO:
                self.pos += 1
                prop_name = self._consume_identifier()
                const_index = len(self.constants)
                self.constants.append(prop_name)
                self.emit(OpCode.OP_CONSTANT)
                self.emit(const_index)
                self.emit(OpCode.OP_GET_ATTR)
                if self.pos < len(self.tokens) and self.current_token()[0] == Token.PAREN_IZQ:
                    self.consume(Token.PAREN_IZQ)
                    num_args = 0
                    if self.pos < len(self.tokens) and self.current_token()[0] != Token.PAREN_DER:
                        self.expression()
                        num_args += 1
                        while self.pos < len(self.tokens) and self.current_token()[0] == Token.COMA:
                            self.pos += 1
                            self.expression()
                            num_args += 1
                    self.consume(Token.PAREN_DER)
                    self.emit(OpCode.OP_CALL)
                    self.emit(0)
                    self.emit(num_args)
                    self.emit(0)
            else:
                break

    def compile_block(self):
        while self.current_token()[0] not in (Token.LLAVE_DER, Token.EOF):
            self.compile_statement()
