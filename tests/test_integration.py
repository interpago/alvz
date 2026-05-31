import pytest
from alvz.core.lexer import Lexer
from alvz.core.parser import Parser
from alvz.core.vm import VM


def run_code(code):
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    bytecode, constants, line_map, funcs = parser.compile()
    vm = VM(bytecode, constants, line_map, funcs)
    vm.run()
    return vm


class TestIntegrationBasics:
    def test_hello_world(self):
        vm = run_code('imprimir("Hola Mundo")')
        assert vm.output_buffer == ["Hola Mundo"]

    def test_variable_and_print(self):
        vm = run_code('variable x = 42\nimprimir(x)')
        assert vm.output_buffer == ["42"]

    def test_arithmetic(self):
        vm = run_code('variable x = (1 + 2) * 3\nimprimir(x)')
        assert vm.output_buffer == ["9"]

    def test_if_true(self):
        vm = run_code('variable x = 0\nsi 1 == 1 { x = 10 }\nimprimir(x)')
        assert vm.output_buffer == ["10"]

    def test_if_else(self):
        vm = run_code('variable x = 0\nsi 1 != 1 { x = 10 } sino { x = 20 }\nimprimir(x)')
        assert vm.output_buffer == ["20"]

    def test_while_loop(self):
        vm = run_code(
            "variable i = 0\n"
            "mientras i < 3 {\n"
            "  imprimir(i)\n"
            "  i = i + 1\n"
            "}"
        )
        assert vm.output_buffer == ["0", "1", "2"]

    def test_for_range(self):
        vm = run_code(
            "para i de 1 a 3 {\n"
            "  imprimir(i)\n"
            "}"
        )
        assert vm.output_buffer == ["1", "2", "3"]

    def test_for_each(self):
        vm = run_code(
            "variable lista = [10, 20, 30]\n"
            "para cada item en lista {\n"
            "  imprimir(item)\n"
            "}"
        )
        assert vm.output_buffer == ["10", "20", "30"]


class TestIntegrationFunctions:
    def test_function_no_args(self):
        vm = run_code(
            "funcion saludar() {\n"
            "  imprimir(\"hola\")\n"
            "}\n"
            "saludar()"
        )
        assert vm.output_buffer == ["hola"]

    def test_function_with_args(self):
        vm = run_code(
            "funcion suma(p1, p2) {\n"
            "  retornar p1 + p2\n"
            "}\n"
            "variable r = suma(3, 4)\n"
            "imprimir(r)"
        )
        assert vm.output_buffer == ["7"]

    def test_function_return(self):
        vm = run_code(
            "funcion doble(val) {\n"
            "  retornar val * 2\n"
            "}\n"
            "imprimir(doble(5))"
        )
        assert vm.output_buffer == ["10"]


class TestIntegrationLists:
    def test_list_create_and_print(self):
        vm = run_code('variable x = [1, 2, 3]\nimprimir(x)')
        assert vm.output_buffer == ["[1, 2, 3]"]

    def test_list_index_get(self):
        vm = run_code('variable x = [10, 20, 30]\nimprimir(x[1])')
        assert vm.output_buffer == ["20"]

    def test_list_append(self):
        vm = run_code('variable x = [1, 2]\nagregar(x, 3)\nimprimir(x)')
        assert vm.output_buffer == ["[1, 2, 3]"]

    def test_list_length(self):
        vm = run_code('variable x = [1, 2, 3]\nimprimir(longitud(x))')
        assert vm.output_buffer == ["3"]


class TestIntegrationStrings:
    def test_string_concatenation(self):
        vm = run_code('variable x = "hola " + "mundo"\nimprimir(x)')
        assert vm.output_buffer == ["hola mundo"]

    def test_string_length(self):
        vm = run_code('variable x = longitud("hola")\nimprimir(x)')
        assert vm.output_buffer == ["4"]

    def test_string_lower(self):
        vm = run_code('variable x = minusculas("HOLA")\nimprimir(x)')
        assert vm.output_buffer == ["hola"]

    def test_string_upper(self):
        vm = run_code('variable x = mayusculas("hola")\nimprimir(x)')
        assert vm.output_buffer == ["HOLA"]

    def test_string_replace(self):
        vm = run_code('variable x = reemplazar("hola mundo", "mundo", "alvz")\nimprimir(x)')
        assert vm.output_buffer == ["hola alvz"]


class TestIntegrationDicts:
    def test_dict_create_and_print(self):
        vm = run_code('variable x = {"a": 1, "b": 2}\nimprimir(x)')
        assert vm.output_buffer[0] in ["{'a': 1, 'b': 2}", "{'b': 2, 'a': 1}"]


class TestIntegrationBooleans:
    def test_comparison(self):
        vm = run_code('variable x = 5 > 3\nimprimir(x)')
        assert vm.output_buffer == ["True"]

    def test_logical_and(self):
        vm = run_code('variable x = verdadero y falso\nimprimir(x)')
        assert vm.output_buffer == ["False"]

    def test_logical_or(self):
        vm = run_code('variable x = verdadero o falso\nimprimir(x)')
        assert vm.output_buffer == ["True"]


class TestIntegrationMath:
    def test_potencia(self):
        vm = run_code('imprimir(potencia(2, 3))')
        assert vm.output_buffer == ["8"]

    def test_raiz(self):
        vm = run_code('imprimir(raiz(9))')
        assert vm.output_buffer == ["3.0"]

    def test_absoluto(self):
        vm = run_code('imprimir(absoluto(0 - 5))')
        assert vm.output_buffer == ["5"]

    def test_redondear(self):
        vm = run_code('imprimir(redondear(3.7))')
        assert vm.output_buffer == ["4"]

    def test_azar_in_range(self):
        for _ in range(20):
            vm = run_code('variable r = azar(1, 10)\nimprimir(r)')
            val = int(vm.output_buffer[0])
            assert 1 <= val <= 10


class TestIntegrationType:
    def test_tipo_numero(self):
        vm = run_code('imprimir(tipo(42))')
        assert vm.output_buffer == ["numero"]

    def test_tipo_texto(self):
        vm = run_code('imprimir(tipo("hola"))')
        assert vm.output_buffer == ["texto"]

    def test_tipo_booleano(self):
        vm = run_code('imprimir(tipo(verdadero))')
        assert vm.output_buffer == ["booleano"]

    def test_tipo_nulo(self):
        vm = run_code('imprimir(tipo(nulo))')
        assert vm.output_buffer == ["nulo"]

    def test_nulo_assign_and_print(self):
        vm = run_code('variable x = nulo\nimprimir(x)')
        assert vm.output_buffer == ["nulo"]

    def test_nulo_equality(self):
        vm = run_code('variable x = nulo\nimprimir(x == nulo)')
        assert vm.output_buffer == ["True"]

    def test_nulo_is_falsy(self):
        vm = run_code('si nulo { imprimir("si") } sino { imprimir("no") }')
        assert vm.output_buffer == ["no"]

    def test_tipo_lista(self):
        vm = run_code('imprimir(tipo([1, 2]))')
        assert vm.output_buffer == ["lista"]

    def test_tipo_diccionario(self):
        vm = run_code('imprimir(tipo({"a": 1}))')
        assert vm.output_buffer == ["diccionario"]


class TestIntegrationJSON:
    def test_json_codificar(self):
        vm = run_code('variable r = json_codificar({"a": 1})\nimprimir(r)')
        import json
        assert vm.output_buffer[0] == json.dumps({"a": 1})

    def test_json_decodificar(self):
        vm = run_code("variable r = json_decodificar('{\"a\": 1}')\nimprimir(r)")
        assert "a" in vm.output_buffer[0]


class TestIntegrationTryCatch:
    def test_try_catch_catches_error(self):
        vm = run_code(
            "variable r = 0\n"
            "intentar {\n"
            "  lanzar(\"error\")\n"
            "} capturar {\n"
            "  r = 1\n"
            "}\n"
            "imprimir(r)"
        )
        assert vm.output_buffer == ["1"]

    def test_try_catch_no_error(self):
        vm = run_code(
            "variable r = 0\n"
            "intentar {\n"
            "  r = 42\n"
            "} capturar {\n"
            "  r = 1\n"
            "}\n"
            "imprimir(r)"
        )
        assert vm.output_buffer == ["42"]


class TestIntegrationErrorMsg:
    def test_error_msj_after_catch(self):
        vm = run_code(
            "variable r = \"\"\n"
            "intentar {\n"
            "  lanzar(\"algo salio mal\")\n"
            "} capturar {\n"
            "  r = error_msj()\n"
            "}\n"
            "imprimir(r)"
        )
        assert "algo salio mal" in vm.output_buffer[0]


class TestIntegrationMultipleStatements:
    def test_complex_program(self):
        code = """
variable resultado = 0

funcion factorial(n) {
    variable r = 1
    variable i = 1
    mientras i <= n {
        r = r * i
        i = i + 1
    }
    retornar r
}

resultado = factorial(5)
imprimir(resultado)
"""
        vm = run_code(code)
        assert vm.output_buffer == ["120"]

    def test_nested_control_flow(self):
        code = """
variable r = ""
para i de 1 a 3 {
    si i % 2 == 0 {
        r = r + "par"
    } sino {
        r = r + "impar"
    }
}
imprimir(r)
"""
        vm = run_code(code)
        assert vm.output_buffer == ["imparparimpar"]


class TestIntegrationNewFeatures:
    def test_unary_minus(self):
        vm = run_code('variable x = -5\nimprimir(x)')
        assert vm.output_buffer == ["-5"]

    def test_unary_minus_expression(self):
        vm = run_code('variable x = -(3 + 4)\nimprimir(x)')
        assert vm.output_buffer == ["-7"]

    def test_unary_minus_compound(self):
        vm = run_code('variable x = -5 + 3\nimprimir(x)')
        assert vm.output_buffer == ["-2"]

    def test_compound_add(self):
        vm = run_code('variable x = 5\nx += 3\nimprimir(x)')
        assert vm.output_buffer == ["8"]

    def test_compound_sub(self):
        vm = run_code('variable x = 10\nx -= 3\nimprimir(x)')
        assert vm.output_buffer == ["7"]

    def test_compound_mul(self):
        vm = run_code('variable x = 4\nx *= 3\nimprimir(x)')
        assert vm.output_buffer == ["12"]

    def test_compound_div(self):
        vm = run_code('variable x = 10\nx /= 2\nimprimir(x)')
        assert vm.output_buffer == ["5.0"]

    def test_compound_mod(self):
        vm = run_code('variable x = 10\nx %= 3\nimprimir(x)')
        assert vm.output_buffer == ["1"]

    def test_break_in_while(self):
        vm = run_code(
            "variable i = 0\n"
            "mientras i < 10 {\n"
            "  i = i + 1\n"
            "  si i == 3 { romper }\n"
            "}\n"
            "imprimir(i)"
        )
        assert vm.output_buffer == ["3"]

    def test_continue_in_while(self):
        vm = run_code(
            "variable r = \"\"\n"
            "variable i = 0\n"
            "mientras i < 5 {\n"
            "  i = i + 1\n"
            "  si i == 3 { continuar }\n"
            "  r = r + i\n"
            "}\n"
            "imprimir(r)"
        )
        assert vm.output_buffer == ["1245"]

    def test_string_triple(self):
        vm = run_code('variable x = """hola mundo"""\nimprimir(x)')
        assert vm.output_buffer == ["hola mundo"]

    def test_string_triple_multiline(self):
        vm = run_code('variable x = """linea1\nlinea2"""\nimprimir(x)')
        assert len(vm.output_buffer[0].split("\n")) == 2

    def test_list_comprehension(self):
        vm = run_code(
            "variable r = [x * 2 para cada x en [1, 2, 3]]\n"
            "imprimir(r)"
        )
        assert vm.output_buffer[0] == "[2, 4, 6]"

    def test_list_comprehension_strings(self):
        vm = run_code(
            'variable r = [x + "!" para cada x en ["a", "b"]]\n'
            "imprimir(r)"
        )
        assert vm.output_buffer[0] == "['a!', 'b!']"

    def test_function_as_value_call(self):
        vm = run_code(
            "funcion saludar(nombre) { imprimir(nombre) }\n"
            'saludar("Alvz")'
        )
        assert vm.output_buffer == ["Alvz"]

    def test_function_as_value_store_and_call(self):
        vm = run_code(
            "funcion suma(a, b) { retornar a + b }\n"
            "variable fn = suma\n"
            "variable r = fn(3, 4)\n"
            "imprimir(r)"
        )
        assert vm.output_buffer == ["7"]


class TestIntegrationImports:
    def _make_lib(self, name, content):
        with open(name, 'w', encoding='utf-8') as f:
            f.write(content)

    def test_import_module_with_function(self):
        self._make_lib('_test_import_func.alvz',
                       'funcion duplicar(x) { retornar x * 2 }\n')
        try:
            code = 'importar "_test_import_func.alvz"\nimprimir(duplicar(21))\n'
            vm = run_code(code)
            assert vm.output_buffer == ["42"]
        finally:
            import os
            try:
                os.remove('_test_import_func.alvz')
            except Exception:
                pass

    def test_import_module_side_effect(self):
        self._make_lib('_test_import_side.alvz',
                       'imprimir("modulo cargado")\n')
        try:
            code = 'importar "_test_import_side.alvz"\nimprimir("fin")\n'
            vm = run_code(code)
            assert vm.output_buffer == ["modulo cargado", "fin"]
        finally:
            import os
            try:
                os.remove('_test_import_side.alvz')
            except Exception:
                pass

    def test_import_module_defines_variable(self):
        self._make_lib('_test_import_var.alvz',
                       'variable mensaje = "desde modulo"\n')
        try:
            code = 'importar "_test_import_var.alvz"\nimprimir(mensaje)\n'
            vm = run_code(code)
            assert vm.output_buffer == ["desde modulo"]
        finally:
            import os
            try:
                os.remove('_test_import_var.alvz')
            except Exception:
                pass

    def test_import_multiple_modules(self):
        self._make_lib('_test_liba.alvz',
                       'funcion suma(a, b) { retornar a + b }\n')
        self._make_lib('_test_libb.alvz',
                       'funcion mul(a, b) { retornar a * b }\n')
        try:
            code = (
                'importar "_test_liba.alvz"\n'
                'importar "_test_libb.alvz"\n'
                'imprimir(suma(3, 4))\n'
                'imprimir(mul(5, 6))\n'
            )
            vm = run_code(code)
            assert vm.output_buffer == ["7", "30"]
        finally:
            import os
            for f in ['_test_liba.alvz', '_test_libb.alvz']:
                try:
                    os.remove(f)
                except Exception:
                    pass


class TestIntegrationStdlib:
    def test_import_matematicas_factorial(self):
        vm = run_code('importar "matematicas"\nimprimir(factorial(5))')
        assert vm.output_buffer == ["120"]

    def test_import_matematicas_multiple(self):
        vm = run_code('importar "matematicas"\nimprimir(maximo(10, 20))\nimprimir(minimo(5, 3))\nimprimir(es_par(4))\nimprimir(es_impar(7))')
        assert vm.output_buffer == ["20", "3", "True", "True"]

    def test_import_matematicas_promedio(self):
        vm = run_code('importar "matematicas"\nimprimir(promedio([1, 2, 3, 4]))')
        assert vm.output_buffer == ["2.5"]

    def test_import_cadenas_capitalizar(self):
        vm = run_code('importar "cadenas"\nimprimir(capitalizar("hola mundo"))')
        assert vm.output_buffer == ["Hola mundo"]

    def test_import_cadenas_reversa(self):
        vm = run_code('importar "cadenas"\nimprimir(reversa("abc"))')
        assert vm.output_buffer == ["cba"]

    def test_import_cadenas_recortar(self):
        vm = run_code('importar "cadenas"\nimprimir(recortar("  hola  "))')
        assert vm.output_buffer == ["hola"]

    def test_import_colecciones_primero_ultimo(self):
        vm = run_code('importar "colecciones"\nimprimir(primero([5, 10, 15]))\nimprimir(ultimo([5, 10, 15]))')
        assert vm.output_buffer == ["5", "15"]

    def test_import_colecciones_invertir(self):
        vm = run_code('importar "colecciones"\nimprimir(invertir([1, 2, 3]))')
        assert vm.output_buffer == ["[3, 2, 1]"]

    def test_import_colecciones_vacio(self):
        vm = run_code('importar "colecciones"\nimprimir(vacio([]))\nimprimir(vacio([1]))')
        assert vm.output_buffer == ["True", "False"]


class TestIntegrationClasses:
    def test_class_no_constructor(self):
        vm = run_code(
            'clase Punto { variable x = 0 variable y = 0 }\n'
            'variable p = nuevo Punto()\n'
            'imprimir(p.x)\n'
            'imprimir(p.y)\n'
        )
        assert vm.output_buffer == ["0", "0"]

    def test_class_with_constructor_and_self(self):
        vm = run_code(
            'clase Persona {\n'
            '  variable nombre = ""\n'
            '  funcion inicializar(nombre) {\n'
            '    self.nombre = nombre\n'
            '  }\n'
            '}\n'
            'variable p = nuevo Persona("Ana")\n'
            'imprimir(p.nombre)\n'
        )
        assert vm.output_buffer == ["Ana"]

    def test_class_with_method(self):
        vm = run_code(
            'clase Calculadora {\n'
            '  funcion sumar(a, b) {\n'
            '    retornar a + b\n'
            '  }\n'
            '}\n'
            'variable c = nuevo Calculadora()\n'
            'variable r = c.sumar(3, 4)\n'
            'imprimir(r)\n'
        )
        assert vm.output_buffer == ["7"]

    def test_class_method_uses_self(self):
        vm = run_code(
            'clase Contador {\n'
            '  variable valor = 0\n'
            '  funcion incrementar() {\n'
            '    self.valor = self.valor + 1\n'
            '  }\n'
            '  funcion obtener() {\n'
            '    retornar self.valor\n'
            '  }\n'
            '}\n'
            'variable c = nuevo Contador()\n'
            'c.incrementar()\n'
            'c.incrementar()\n'
            'imprimir(c.obtener())\n'
        )
        assert vm.output_buffer == ["2"]

    def test_constructor_with_multiple_args(self):
        vm = run_code(
            'clase Rectangulo {\n'
            '  variable ancho = 0\n'
            '  variable alto = 0\n'
            '  funcion inicializar(ancho, alto) {\n'
            '    self.ancho = ancho\n'
            '    self.alto = alto\n'
            '  }\n'
            '  funcion area() {\n'
            '    retornar self.ancho * self.alto\n'
            '  }\n'
            '}\n'
            'variable r = nuevo Rectangulo(5, 3)\n'
            'imprimir(r.area())\n'
        )
        assert vm.output_buffer == ["15"]

    def test_property_assignment(self):
        vm = run_code(
            'clase Caja {\n'
            '  variable contenido = ""\n'
            '}\n'
            'variable c = nuevo Caja()\n'
            'c.contenido = "libros"\n'
            'imprimir(c.contenido)\n'
        )
        assert vm.output_buffer == ["libros"]

    def test_chained_property_access(self):
        vm = run_code(
            'clase Direccion {\n'
            '  variable calle = ""\n'
            '}\n'
            'clase Persona {\n'
            '  variable direccion = 0\n'
            '}\n'
            'variable d = nuevo Direccion()\n'
            'd.calle = "Av Siempre Viva"\n'
            'variable p = nuevo Persona()\n'
            'p.direccion = d\n'
            'imprimir(p.direccion.calle)\n'
        )
        assert vm.output_buffer == ["Av Siempre Viva"]

    def test_class_expression_in_new(self):
        vm = run_code(
            'clase Multiplicador {\n'
            '  variable factor = 1\n'
            '  funcion inicializar(factor) {\n'
            '    self.factor = factor\n'
            '  }\n'
            '  funcion aplicar(x) {\n'
            '    retornar x * self.factor\n'
            '  }\n'
            '}\n'
            'variable m = nuevo Multiplicador(2 + 3)\n'
            'imprimir(m.aplicar(4))\n'
        )
        assert vm.output_buffer == ["20"]

    def test_class_error_not_found(self):
        with pytest.raises(RuntimeError, match="La clase 'NoExiste' no existe"):
            run_code('variable x = nuevo NoExiste()\n')

    def test_multiple_instances_independent(self):
        vm = run_code(
            'clase Punto {\n'
            '  variable x = 0\n'
            '  funcion inicializar(x) {\n'
            '    self.x = x\n'
            '  }\n'
            '}\n'
            'variable p1 = nuevo Punto(10)\n'
            'variable p2 = nuevo Punto(20)\n'
            'imprimir(p1.x)\n'
            'imprimir(p2.x)\n'
            'p1.x = 99\n'
            'imprimir(p1.x)\n'
            'imprimir(p2.x)\n'
        )
        assert vm.output_buffer == ["10", "20", "99", "20"]

    def test_method_called_from_expression(self):
        vm = run_code(
            'clase Saludador {\n'
            '  funcion saludar(nombre) {\n'
            '    retornar "Hola " + nombre\n'
            '  }\n'
            '}\n'
            'variable s = nuevo Saludador()\n'
            'variable msg = s.saludar("Mundo")\n'
            'imprimir(msg)\n'
        )
        assert vm.output_buffer == ["Hola Mundo"]

    def test_inheritance_basic(self):
        vm = run_code(
            'clase Animal {\n'
            '  variable nombre = ""\n'
            '  funcion inicializar(nombre) {\n'
            '    self.nombre = nombre\n'
            '  }\n'
            '  funcion saludar() {\n'
            '    retornar "Soy " + self.nombre\n'
            '  }\n'
            '}\n'
            'clase Perro de Animal {\n'
            '  funcion ladrar() {\n'
            '    retornar "Guau!"\n'
            '  }\n'
            '}\n'
            'variable p = nuevo Perro("Rex")\n'
            'imprimir(p.saludar())\n'
            'imprimir(p.ladrar())\n'
        )
        assert vm.output_buffer == ["Soy Rex", "Guau!"]

    def test_super_call(self):
        vm = run_code(
            'clase Animal {\n'
            '  variable nombre = ""\n'
            '  funcion inicializar(nombre) {\n'
            '    self.nombre = nombre\n'
            '  }\n'
            '  funcion saludar() {\n'
            '    retornar "Hola, soy " + self.nombre\n'
            '  }\n'
            '}\n'
            'clase Perro de Animal {\n'
            '  funcion saludar() {\n'
            '    retornar super.saludar() + " (perro)"\n'
            '  }\n'
            '}\n'
            'variable p = nuevo Perro("Rex")\n'
            'imprimir(p.saludar())\n'
        )
        assert vm.output_buffer == ["Hola, soy Rex (perro)"]

    def test_super_chain(self):
        vm = run_code(
            'clase A {\n'
            '  funcion foo() { retornar "A" }\n'
            '}\n'
            'clase B de A {\n'
            '  funcion foo() { retornar super.foo() + "B" }\n'
            '}\n'
            'clase C de B {\n'
            '  funcion foo() { retornar super.foo() + "C" }\n'
            '}\n'
            'variable c = nuevo C()\n'
            'imprimir(c.foo())\n'
        )
        assert vm.output_buffer == ["ABC"]

    def test_instanceof_true(self):
        vm = run_code(
            'clase Animal {}\n'
            'clase Perro de Animal {}\n'
            'variable p = nuevo Perro()\n'
            'variable r = p instancia Perro\n'
            'imprimir(r)\n'
        )
        assert vm.output_buffer == ["True"]

    def test_instanceof_parent(self):
        vm = run_code(
            'clase Animal {}\n'
            'clase Perro de Animal {}\n'
            'variable p = nuevo Perro()\n'
            'variable r = p instancia Animal\n'
            'imprimir(r)\n'
        )
        assert vm.output_buffer == ["True"]

    def test_instanceof_false(self):
        vm = run_code(
            'clase Animal {}\n'
            'clase Perro de Animal {}\n'
            'clase Gato {}\n'
            'variable p = nuevo Perro()\n'
            'variable r = p instancia Gato\n'
            'imprimir(r)\n'
        )
        assert vm.output_buffer == ["False"]

    def test_instanceof_not_an_object(self):
        vm = run_code(
            'clase Animal {}\n'
            'variable r = 42 instancia Animal\n'
            'imprimir(r)\n'
        )
        assert vm.output_buffer == ["False"]

    def test_property_default_expression_arithmetic(self):
        vm = run_code(
            'clase Punto {\n'
            '  variable x = 1 + 2\n'
            '  variable y = 3 * 4\n'
            '}\n'
            'variable p = nuevo Punto()\n'
            'imprimir(p.x)\n'
            'imprimir(p.y)\n'
        )
        assert vm.output_buffer == ["3", "12"]

    def test_property_default_expression_list(self):
        vm = run_code(
            'clase Caja {\n'
            '  variable items = [1, 2, 3]\n'
            '}\n'
            'variable c = nuevo Caja()\n'
            'imprimir(c.items)\n'
        )
        assert vm.output_buffer == ["[1, 2, 3]"]

    def test_property_default_expression_dict(self):
        vm = run_code(
            'clase Config {\n'
            '  variable opts = {"a": 1, "b": 2}\n'
            '}\n'
            'variable c = nuevo Config()\n'
            'imprimir(c.opts)\n'
        )
        assert vm.output_buffer == ["{'a': 1, 'b': 2}"]

    def test_property_default_with_constructor(self):
        vm = run_code(
            'clase Punto {\n'
            '  variable x = 1 + 2\n'
            '  variable y = 3 * 4\n'
            '  funcion inicializar() {\n'
            '    self.x = self.x + 10\n'
            '  }\n'
            '}\n'
            'variable p = nuevo Punto()\n'
            'imprimir(p.x)\n'
            'imprimir(p.y)\n'
        )
        assert vm.output_buffer == ["13", "12"]

    def test_property_default_with_constructor_args(self):
        vm = run_code(
            'clase Punto {\n'
            '  variable x = 1 + 2\n'
            '  funcion inicializar(dx) {\n'
            '    self.x = self.x + dx\n'
            '  }\n'
            '}\n'
            'variable p = nuevo Punto(10)\n'
            'imprimir(p.x)\n'
        )
        assert vm.output_buffer == ["13"]

    def test_property_default_expression_inheritance(self):
        vm = run_code(
            'clase Base {\n'
            '  variable valor = 5 + 5\n'
            '}\n'
            'clase Hijo de Base {\n'
            '  funcion obtener() {\n'
            '    retornar self.valor\n'
            '  }\n'
            '}\n'
            'variable h = nuevo Hijo()\n'
            'imprimir(h.obtener())\n'
        )
        assert vm.output_buffer == ["10"]

    def test_property_default_expression_function_call(self):
        vm = run_code(
            'funcion obtener_valor() { retornar 42 }\n'
            'clase Caja {\n'
            '  variable x = obtener_valor()\n'
            '}\n'
            'variable c = nuevo Caja()\n'
            'imprimir(c.x)\n'
        )
        assert vm.output_buffer == ["42"]

    def test_property_default_mixed_literal_and_expression(self):
        vm = run_code(
            'clase Mix {\n'
            '  variable a = 10\n'
            '  variable b = [1, 2, 3]\n'
            '  variable c = "hola"\n'
            '}\n'
            'variable m = nuevo Mix()\n'
            'imprimir(m.a)\n'
            'imprimir(m.b)\n'
            'imprimir(m.c)\n'
        )
        assert vm.output_buffer == ["10", "[1, 2, 3]", "hola"]

    def test_property_default_independent_instances(self):
        vm = run_code(
            'clase Contador {\n'
            '  variable datos = [0]\n'
            '}\n'
            'variable c1 = nuevo Contador()\n'
            'variable c2 = nuevo Contador()\n'
            'c1.datos = [99]\n'
            'imprimir(c1.datos)\n'
            'imprimir(c2.datos)\n'
        )
        assert vm.output_buffer == ["[99]", "[0]"]

    def test_static_method_basic(self):
        vm = run_code(
            'clase MathUtils {\n'
            '  funcion estatico sumar(a, b) {\n'
            '    retornar a + b\n'
            '  }\n'
            '}\n'
            'variable r = MathUtils.sumar(10, 5)\n'
            'imprimir(r)\n'
        )
        assert vm.output_buffer == ["15"]

    def test_static_method_multiple_args(self):
        vm = run_code(
            'clase Calc {\n'
            '  funcion estatico multiplicar(x, y, z) {\n'
            '    retornar x * y * z\n'
            '  }\n'
            '}\n'
            'variable r = Calc.multiplicar(2, 3, 4)\n'
            'imprimir(r)\n'
        )
        assert vm.output_buffer == ["24"]

    def test_static_method_no_args(self):
        vm = run_code(
            'clase Const {\n'
            '  funcion estatico obtener_pi() {\n'
            '    retornar 3.14\n'
            '  }\n'
            '}\n'
            'variable r = Const.obtener_pi()\n'
            'imprimir(r)\n'
        )
        assert vm.output_buffer == ["3.14"]

    def test_static_method_with_instance_method(self):
        vm = run_code(
            'clase Util {\n'
            '  funcion estatico duplicar(n) {\n'
            '    retornar n * 2\n'
            '  }\n'
            '  funcion mostrar(n) {\n'
            '    retornar "Valor: " + n\n'
            '  }\n'
            '}\n'
            'variable u = nuevo Util()\n'
            'imprimir(Util.duplicar(5))\n'
            'imprimir(u.mostrar(10))\n'
        )
        assert vm.output_buffer == ["10", "Valor: 10"]

    def test_static_method_inheritance(self):
        vm = run_code(
            'clase Base {\n'
            '  funcion estatico saludar() {\n'
            '    retornar "Hola"\n'
            '  }\n'
            '}\n'
            'clase Hijo de Base {}\n'
            'variable r = Hijo.saludar()\n'
            'imprimir(r)\n'
        )
        assert vm.output_buffer == ["Hola"]

    def test_fecha_actual(self):
        vm = run_code(
            'variable f = fecha_actual("%Y-%m-%d")\n'
            'imprimir(f)\n'
        )
        from datetime import datetime
        expected = datetime.now().strftime("%Y-%m-%d")
        assert vm.output_buffer == [expected]

    def test_dividir(self):
        vm = run_code(
            'variable partes = dividir("a,b,c", ",")\n'
            'imprimir(partes)\n'
        )
        assert vm.output_buffer == ["['a', 'b', 'c']"]

    def test_unir(self):
        vm = run_code(
            'variable r = unir(["a", "b", "c"], "-")\n'
            'imprimir(r)\n'
        )
        assert vm.output_buffer == ["a-b-c"]

    def test_a_numero(self):
        vm = run_code(
            'variable n = a_numero("42")\n'
            'imprimir(n + 8)\n'
        )
        assert vm.output_buffer == ["50"]

    def test_regex_buscar(self):
        vm = run_code(
            'variable r = regex_buscar("hola 123 mundo 456", "\\d+")\n'
            'imprimir(r)\n'
        )
        assert vm.output_buffer == ["['123', '456']"]

    def test_getter_and_setter(self):
        vm = run_code(
            'clase Persona {\n'
            '  variable _nombre = ""\n'
            '  variable _edad = 0\n'
            '  propiedad nombre {\n'
            '    obtener {\n'
            '      retornar self._nombre\n'
            '    }\n'
            '    establecer(valor) {\n'
            '      self._nombre = valor\n'
            '    }\n'
            '  }\n'
            '  funcion inicializar(nombre, edad) {\n'
            '    self._nombre = nombre\n'
            '    self._edad = edad\n'
            '  }\n'
            '  funcion cumplir_anios() {\n'
            '    self._edad = self._edad + 1\n'
            '  }\n'
            '}\n'
            'variable p = nuevo Persona("Ana", 25)\n'
            'imprimir(p.nombre)\n'
            'p.nombre = "Ana Maria"\n'
            'imprimir(p.nombre)\n'
        )
        assert vm.output_buffer == ["Ana", "Ana Maria"]

    def test_getter_read_only(self):
        vm = run_code(
            'clase Constante {\n'
            '  variable _valor = 42\n'
            '  propiedad valor {\n'
            '    obtener {\n'
            '      retornar self._valor\n'
            '    }\n'
            '  }\n'
            '}\n'
            'variable c = nuevo Constante()\n'
            'imprimir(c.valor)\n'
        )
        assert vm.output_buffer == ["42"]

    def test_setter_with_computation(self):
        vm = run_code(
            'clase Rectangulo {\n'
            '  variable _area = 0\n'
            '  variable _perimetro = 0\n'
            '  propiedad lado1 {\n'
            '    establecer(v) {\n'
            '      self._lado1 = v\n'
            '    }\n'
            '  }\n'
            '  funcion inicializar(l1, l2) {\n'
            '    self._lado1 = l1\n'
            '    self._lado2 = l2\n'
            '    self._recalcular()\n'
            '  }\n'
            '  funcion _recalcular() {\n'
            '    self._area = self._lado1 * self._lado2\n'
            '    self._perimetro = 2 * (self._lado1 + self._lado2)\n'
            '  }\n'
            '  funcion mostrar() {\n'
            '    imprimir(self._area)\n'
            '    imprimir(self._perimetro)\n'
            '  }\n'
            '}\n'
            'variable r = nuevo Rectangulo(3, 4)\n'
            'r.mostrar()\n'
        )
        assert vm.output_buffer == ["12", "14"]

    def test_getter_uses_computation(self):
        vm = run_code(
            'clase Circulo {\n'
            '  variable _radio = 0\n'
            '  propiedad area {\n'
            '    obtener {\n'
            '      retornar 3.1416 * self._radio * self._radio\n'
            '    }\n'
            '  }\n'
            '  funcion inicializar(r) {\n'
            '    self._radio = r\n'
            '  }\n'
            '}\n'
            'variable c = nuevo Circulo(5)\n'
            'imprimir(c.area)\n'
        )
        assert vm.output_buffer == ["78.54"]

    def test_getter_setter_inheritance(self):
        vm = run_code(
            'clase Base {\n'
            '  variable _x = 0\n'
            '  propiedad x {\n'
            '    obtener {\n'
            '      retornar self._x\n'
            '    }\n'
            '    establecer(v) {\n'
            '      self._x = v * 2\n'
            '    }\n'
            '  }\n'
            '}\n'
            'clase Hijo de Base {\n'
            '  funcion obtener_doble() {\n'
            '    retornar self.x * 2\n'
            '  }\n'
            '}\n'
            'variable h = nuevo Hijo()\n'
            'h.x = 5\n'
            'imprimir(h.x)\n'
            'imprimir(h.obtener_doble())\n'
        )
        assert vm.output_buffer == ["10", "20"]

    def test_getter_setter_backing_field_direct_access(self):
        vm = run_code(
            'clase Demo {\n'
            '  variable _val = 0\n'
            '  propiedad val {\n'
            '    obtener {\n'
            '      retornar self._val + 1\n'
            '    }\n'
            '  }\n'
            '}\n'
            'variable d = nuevo Demo()\n'
            'd._val = 10\n'
            'imprimir(d._val)\n'
            'imprimir(d.val)\n'
        )
        assert vm.output_buffer == ["10", "11"]


class TestIntegrationAsync:
    def test_async_function_call(self):
        vm = run_code(
            'funcion async foo(n) {\n'
            '    retornar n * 2\n'
            '}\n'
            'variable x = aguardar foo(5)\n'
            'imprimir(x)\n'
        )
        assert vm.output_buffer == ["10"]

    def test_async_function_no_return(self):
        vm = run_code(
            'funcion async bar(n) {\n'
            '    imprimir(n + 1)\n'
            '}\n'
            'aguardar bar(99)\n'
        )
        assert vm.output_buffer == ["100"]

    def test_regular_call_still_works(self):
        vm = run_code(
            'funcion normal(x) {\n'
            '    retornar x + 1\n'
            '}\n'
            'imprimir(normal(41))\n'
        )
        assert vm.output_buffer == ["42"]

    def test_mixed_async_regular(self):
        vm = run_code(
            'funcion async async_sqr(n) {\n'
            '    retornar n * n\n'
            '}\n'
            'funcion regular_add(a, b) {\n'
            '    retornar a + b\n'
            '}\n'
            'variable r = aguardar async_sqr(3)\n'
            'variable s = regular_add(r, 1)\n'
            'imprimir(s)\n'
        )
        assert vm.output_buffer == ["10"]


def run_optimized(code):
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    bytecode, constants, line_map, funcs = parser.compile(optimize=True)
    vm = VM(bytecode, constants, line_map, funcs)
    vm.run()
    return vm


class TestIntegrationOptimizer:
    def test_optimizer_constant_folding(self):
        vm = run_optimized('variable x = 2 + 3\nimprimir(x)')
        assert vm.output_buffer == ["5"]

    def test_optimizer_unary_folding(self):
        vm = run_optimized('variable x = -5\nimprimir(x)')
        assert vm.output_buffer == ["-5"]

    def test_optimizer_dead_code(self):
        vm = run_optimized(
            'funcion foo() {\n'
            '    retornar 42\n'
            '    imprimir(99)\n'
            '}\n'
            'imprimir(foo())\n'
        )
        assert vm.output_buffer == ["42"]

    def test_optimizer_jump_to_next(self):
        vm = run_optimized(
            'variable x = 0\n'
            'mientras falso {\n'
            '    x = 1\n'
            '}\n'
            'imprimir(x)\n'
        )
        assert vm.output_buffer == ["0"]

    def test_optimizer_preserves_semantics(self):
        vm = run_optimized(
            'funcion suma(a, b) {\n'
            '    retornar a + b + 10\n'
            '}\n'
            'imprimir(suma(3, 4))\n'
        )
        assert vm.output_buffer == ["17"]


class TestIntegrationConcurrentAsync:
    def test_async_concurrent_execution(self):
        import time
        codigo = (
            'funcion async tarea1() {\n'
            '    esperar(0.3)\n'
            '    imprimir("t1")\n'
            '}\n'
            'funcion async tarea2() {\n'
            '    esperar(0.1)\n'
            '    imprimir("t2")\n'
            '}\n'
            'variable c1 = tarea1()\n'
            'variable c2 = tarea2()\n'
            'aguardar c1\n'
            'aguardar c2\n'
            'imprimir("fin")\n'
        )
        t0 = time.time()
        vm = run_code(codigo)
        t = time.time() - t0
        # t2 (0.1s) should finish before t1 (0.3s)
        assert vm.output_buffer.index("t2") < vm.output_buffer.index("t1")
        # Total time should be ~0.3s (max), not 0.4s (sum)
        assert t < 0.4, f"Concurrent execution took {t:.2f}s, expected <0.4s"
        assert vm.output_buffer[-1] == "fin"

    def test_async_return_value(self):
        codigo = (
            'funcion async calc(n) {\n'
            '    retornar n * 2\n'
            '}\n'
            'variable c = calc(21)\n'
            'variable r = aguardar c\n'
            'imprimir(r)\n'
        )
        vm = run_code(codigo)
        assert vm.output_buffer == ["42"]

    def test_sequential_aguardar(self):
        """aguardar expr() syntax still works (synchronous path)."""
        codigo = (
            'funcion async foo(n) {\n'
            '    retornar n + 1\n'
            '}\n'
            'variable x = aguardar foo(5)\n'
            'imprimir(x)\n'
        )
        vm = run_code(codigo)
        assert vm.output_buffer == ["6"]


class TestIntegrationSQLite:
    def test_sqlite_create_and_select(self):
        import os
        import tempfile
        db = tempfile.mktemp(suffix='.db')
        try:
            codigo = (
                'importar "sqlite"\n'
                f'variable conn = base_abrir("{db}")\n'
                'base_ejecutar(conn, "CREATE TABLE IF NOT EXISTS test (id INTEGER, nombre TEXT)")\n'
                'base_ejecutar(conn, "INSERT INTO test VALUES (1, \'alfa\')")\n'
                'base_ejecutar(conn, "INSERT INTO test VALUES (2, \'beta\')")\n'
                'variable res = base_consultar(conn, "SELECT * FROM test ORDER BY id")\n'
                'imprimir(res[0]["nombre"])\n'
                'imprimir(res[1]["nombre"])\n'
                'base_cerrar(conn)\n'
            )
            vm = run_code(codigo)
            assert vm.output_buffer == ["alfa", "beta"]
        finally:
            try:
                os.remove(db)
            except Exception:
                pass

    def test_sqlite_crear_tabla_e_insertar(self):
        import os
        import tempfile
        db = tempfile.mktemp(suffix='.db')
        try:
            codigo = (
                'importar "sqlite"\n'
                f'variable conn = base_abrir("{db}")\n'
                'base_crear_tabla(conn, "usuarios", ["id INTEGER", "nombre TEXT", "edad INTEGER"])\n'
                'base_insertar(conn, "usuarios", {"id": 1, "nombre": "Ana", "edad": 30})\n'
                'base_insertar(conn, "usuarios", {"id": 2, "nombre": "Luis", "edad": 25})\n'
                'variable res = base_seleccionar(conn, "usuarios", "edad > 26")\n'
                'imprimir(longitud(res))\n'
                'imprimir(res[0]["nombre"])\n'
                'base_cerrar(conn)\n'
            )
            vm = run_code(codigo)
            assert vm.output_buffer == ["1", "Ana"]
        finally:
            try:
                os.remove(db)
            except Exception:
                pass

    def test_sqlite_empty_result(self):
        import os
        import tempfile
        db = tempfile.mktemp(suffix='.db')
        try:
            codigo = (
                'importar "sqlite"\n'
                f'variable conn = base_abrir("{db}")\n'
                'base_ejecutar(conn, "CREATE TABLE IF NOT EXISTS items (id INTEGER)")\n'
                'variable res = base_consultar(conn, "SELECT * FROM items")\n'
                'imprimir(longitud(res))\n'
                'base_cerrar(conn)\n'
            )
            vm = run_code(codigo)
            assert vm.output_buffer == ["0"]
        finally:
            try:
                os.remove(db)
            except Exception:
                pass


class TestIntegrationAnonymousFunctions:
    def test_anon_function_assigned(self):
        vm = run_code(
            'variable f = funcion(x) {\n'
            '    retornar x * 2\n'
            '}\n'
            'imprimir(f(5))\n'
        )
        assert vm.output_buffer == ["10"]

    def test_anon_function_no_args(self):
        vm = run_code(
            'variable f = funcion() {\n'
            '    retornar 42\n'
            '}\n'
            'imprimir(f())\n'
        )
        assert vm.output_buffer == ["42"]

    def test_anon_function_multi_args(self):
        vm = run_code(
            'variable suma = funcion(a, b, c) {\n'
            '    retornar a + b + c\n'
            '}\n'
            'imprimir(suma(1, 2, 3))\n'
        )
        assert vm.output_buffer == ["6"]

    def test_anon_function_passed_as_arg(self):
        vm = run_code(
            'funcion aplica(f, val) {\n'
            '    retornar f(val)\n'
            '}\n'
            'variable f = funcion(x) { retornar x + 1 }\n'
            'imprimir(aplica(f, 10))\n'
        )
        assert vm.output_buffer == ["11"]

    def test_anon_function_list_map(self):
        vm = run_code(
            'variable f = funcion(x) { retornar x + 1 }\n'
            'imprimir(f(1))\n'
        )
        assert vm.output_buffer == ["2"]

    def test_anon_function_typed_params(self):
        vm = run_code(
            'variable f = funcion(x: numero): numero {\n'
            '    retornar x * 3\n'
            '}\n'
            'imprimir(f(7))\n'
        )
        assert vm.output_buffer == ["21"]


class TestIntegrationGlobalKeyword:
    def test_global_read_in_function(self):
        vm = run_code(
            'variable x = 10\n'
            'funcion leer_global() {\n'
            '    global x\n'
            '    imprimir(x)\n'
            '}\n'
            'leer_global()\n'
        )
        assert vm.output_buffer == ["10"]

    def test_global_write_in_function(self):
        vm = run_code(
            'variable x = 10\n'
            'funcion modificar_global() {\n'
            '    global x\n'
            '    x = 20\n'
            '}\n'
            'modificar_global()\n'
            'imprimir(x)\n'
        )
        assert vm.output_buffer == ["20"]

    def test_global_compound_assign(self):
        vm = run_code(
            'variable contador = 0\n'
            'funcion incrementar() {\n'
            '    global contador\n'
            '    contador += 1\n'
            '}\n'
            'incrementar()\n'
            'incrementar()\n'
            'imprimir(contador)\n'
        )
        assert vm.output_buffer == ["2"]

    def test_global_multiple_vars(self):
        vm = run_code(
            'variable a = 1\n'
            'variable b = 2\n'
            'funcion suma_global() {\n'
            '    global a, b\n'
            '    retornar a + b\n'
            '}\n'
            'imprimir(suma_global())\n'
        )
        assert vm.output_buffer == ["3"]

    def test_global_new_var(self):
        vm = run_code(
            'funcion crear_global() {\n'
            '    global x\n'
            '    x = 99\n'
            '}\n'
            'crear_global()\n'
            'imprimir(x)\n'
        )
        assert vm.output_buffer == ["99"]


class TestIntegrationPackageInstall:
    def test_install_and_import_package(self, monkeypatch):
        import os
        import tempfile
        import shutil
        from alvz.core.package_manager import (
            _save_local_db
        )
        tmpdir = tempfile.mkdtemp()
        monkeypatch.setattr("alvz.core.package_manager.ALVZ_DIR", tmpdir)
        monkeypatch.setattr("alvz.core.package_manager.PACKAGES_DIR", os.path.join(tmpdir, "packages"))
        try:
            pkg_dir = os.path.join(tmpdir, "packages", "math")
            os.makedirs(pkg_dir)
            with open(os.path.join(pkg_dir, "math.alvz"), "w", encoding="utf-8") as f:
                f.write(
                    'funcion al_cuadrado(x) {\n'
                    '    retornar x * x\n'
                    '}\n'
                )
            _save_local_db({"math": {"name": "math", "version": "1.0", "entry": "math.alvz"}})

            codigo = (
                'importar "math"\n'
                'imprimir(al_cuadrado(5))\n'
            )
            vm = run_code(codigo)
            assert vm.output_buffer == ["25"]
        finally:
            shutil.rmtree(tmpdir)

    def test_install_package_dependency_chain(self, monkeypatch):
        import os
        import tempfile
        import shutil
        from alvz.core.package_manager import (
            _save_local_db
        )
        tmpdir = tempfile.mkdtemp()
        monkeypatch.setattr("alvz.core.package_manager.ALVZ_DIR", tmpdir)
        monkeypatch.setattr("alvz.core.package_manager.PACKAGES_DIR", os.path.join(tmpdir, "packages"))
        try:
            pkg_dir = os.path.join(tmpdir, "packages", "util")
            os.makedirs(pkg_dir)
            with open(os.path.join(pkg_dir, "util.alvz"), "w", encoding="utf-8") as f:
                f.write(
                    'funcion duplicar(x) {\n'
                    '    retornar x * 2\n'
                    '}\n'
                )
            _save_local_db({"util": {"name": "util", "version": "1.0", "entry": "util.alvz"}})

            codigo = (
                'importar "util"\n'
                'imprimir(duplicar(21))\n'
            )
            vm = run_code(codigo)
            assert vm.output_buffer == ["42"]
        finally:
            shutil.rmtree(tmpdir)
