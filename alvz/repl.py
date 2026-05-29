"""
Modulo interactivo REPL y punto de entrada principal para Alvz Language.
"""

import sys
import os
import json

VERSION = "0.17.0"

from .core.lexer import Lexer
from .core.parser import Parser
from .core.vm import VM
from .core.bytecode import OpCode


class _Terminal:
    def __init__(self):
        self._use_color = os.name != 'nt' or os.environ.get('TERM', '') in ('xterm', 'xterm-256color', 'ansi')
        self._hist = []
        self._hist_idx = 0
        self._buffer = ''
        self._readline_available = False
        try:
            import readline
            self._readline_available = True
            readline.set_completer(self._completer)
            readline.parse_and_bind('tab: complete')
        except ImportError:
            pass

    def _completer(self, text, state):
        _KEYWORDS = ['si', 'sino', 'mientras', 'para', 'cada', 'funcion', 'variable', 'clase',
                     'nuevo', 'retornar', 'importar', 'intentar', 'capturar', 'lanzar',
                     'verdadero', 'falso', 'nulo', 'y', 'o', 'en', 'de', 'a',
                     'async', 'aguardar', 'global', 'romper', 'continuar', 'estatico',
                     'propiedad', 'obtener', 'establecer']
        _BUILTINS = ['imprimir', 'leer', 'leer_numero', 'azar', 'limpiar', 'longitud',
                     'agregar', 'tiempo', 'tipo', 'json_codificar', 'json_decodificar',
                     'reemplazar', 'absoluto', 'redondear', 'potencia', 'raiz',
                     'mayusculas', 'minusculas', 'enviar_web', 'esperar']
        if state == 0:
            self._matches = [w for w in _KEYWORDS + _BUILTINS if w.startswith(text)]
        try:
            return self._matches[state]
        except IndexError:
            return None

    def _rojo(self, t):
        return f'\033[91m{t}\033[0m' if self._use_color else t

    def _verde(self, t):
        return f'\033[92m{t}\033[0m' if self._use_color else t

    def _amarillo(self, t):
        return f'\033[93m{t}\033[0m' if self._use_color else t

    def _cian(self, t):
        return f'\033[96m{t}\033[0m' if self._use_color else t

    def _negrita(self, t):
        return f'\033[1m{t}\033[0m' if self._use_color else t

    def prompt(self, text):
        return input(self._cian(text) if self._use_color else text)

    def mostrar_resultado(self, valor):
        print(f'{self._verde("=>")} {valor}')

    def mostrar_error(self, msg):
        print(f'{self._rojo("Error:")} {msg}')

    def mostrar_info(self, msg):
        print(f'{self._amarillo("*")} {msg}')

    def bienvenida(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(self._negrita(self._cian('Alvz Language REPL')))
        print(self._amarillo('Escribe "salir" para terminar.\n'))


def repl():
    term = _Terminal()
    term.bienvenida()
    buffer = ""
    vm = VM([], [], source_lines=[])
    global_symbols = {}
    functions = {}
    constants = []
    nivel_llaves = 0

    while True:
        try:
            if nivel_llaves > 0:
                prompt = "... "
            else:
                prompt = "alvz> "

            linea = term.prompt(prompt)
            if linea.strip().lower() == "salir":
                break

            buffer += linea + "\n"
            nivel_llaves += linea.count("{") - linea.count("}")

            if nivel_llaves > 0:
                continue

            if not buffer.strip():
                buffer = ""
                continue

            lexer = Lexer(buffer)
            tokens = lexer.tokenize()

            parser = Parser(tokens)
            parser.global_symbols = global_symbols
            parser.symbols = global_symbols
            parser.functions = functions
            parser.constants = constants

            bytecode, constants, line_map, funcs = parser.compile()

            vm.bytecode = bytecode
            vm.constants = constants
            vm.line_map = line_map
            vm.functions = funcs
            vm.ip = 0
            vm.output_buffer = []

            vm.run()

            global_symbols = parser.global_symbols
            functions = parser.functions
            constants = parser.constants

            if vm.stack:
                resultado = vm.stack.pop()
                term.mostrar_resultado(resultado)

            buffer = ""

        except KeyboardInterrupt:
            print()
            buffer = ""
            nivel_llaves = 0
        except Exception as e:
            term.mostrar_error(str(e))
            buffer = ""
            nivel_llaves = 0


def _run_test_files(files):
    """Ejecuta archivos de test y reporta resultados."""
    import time
    inicio = time.time()
    total = len(files)
    pasaron = 0
    fallaron = 0

    print(f"Ejecutando {total} archivo(s) de test...\n")

    for f in files:
        try:
            with open(f, 'r', encoding='utf-8-sig') as fp:
                codigo = fp.read()
            lexer = Lexer(codigo)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            bytecode, constants, line_map, funcs = parser.compile(check_types=True)
            source_lines = codigo.split('\n')
            vm = VM(bytecode, constants, line_map, funcs, source_lines)
            vm.run()
            pasaron += 1
        except Exception as e:
            print(f"  Error en {f}: {e}")
            fallaron += 1

    fin = time.time()
    print(f"\nResultados: {pasaron} pasaron, {fallaron} fallaron "
          f"({total} total) en {fin - inicio:.2f}s")
    return fallaron == 0


def _cmd_test(args):
    """Comando 'alvz test': ejecuta tests."""
    if not args:
        args = ["tests/"]
    
    test_files = []
    for arg in args:
        path = arg
        if os.path.isdir(path):
            for root, _, files in os.walk(path):
                for f in files:
                    if f.endswith('.alvz') and (f.startswith('test_') or f.endswith('_test.alvz')):
                        test_files.append(os.path.join(root, f))
        elif os.path.isfile(path) and path.endswith('.alvz'):
            test_files.append(path)
        elif os.path.isfile(path + '.alvz'):
            test_files.append(path + '.alvz')
    
    if not test_files:
        print("No se encontraron archivos de test.")
        return
    
    exito = _run_test_files(test_files)
    sys.exit(0 if exito else 1)


def _cmd_fmt(args):
    """Comando 'alvz fmt': formatea archivos .alvz."""
    if not args:
        print("Uso: alvz fmt <archivo.alvz> [--check]")
        sys.exit(1)
    
    check_only = '--check' in args
    args = [a for a in args if a != '--check']
    
    for filename in args:
        if not os.path.isfile(filename):
            print(f"Error: archivo '{filename}' no encontrado")
            sys.exit(1)
        
        with open(filename, 'r', encoding='utf-8-sig') as f:
            codigo = f.read()
        
        try:
            lexer = Lexer(codigo)
            tokens = lexer.tokenize()
        except Exception as e:
            print(f"Error lexico en {filename}: {e}")
            continue
        
        lineas = codigo.split('\n')
        indentado = 0
        output = []
        
        for linea in lineas:
            stripped = linea.strip()
            if not stripped:
                output.append('')
                continue
            
            if stripped.startswith('#'):
                output.append(stripped)
                continue
            
            dedent = 0
            for ch in stripped:
                if ch == '}':
                    dedent += 1
                else:
                    break
            
            nivel = indentado - dedent
            if nivel < 0:
                nivel = 0
            
            indent_str = '\t' * nivel
            output.append(indent_str + stripped)
            
            indentado += stripped.count('{') - stripped.count('}')
            if indentado < 0:
                indentado = 0
        
        formatted = '\n'.join(output)
        
        if check_only:
            if codigo != formatted:
                print(f"{filename}: necesita formateo")
                sys.exit(1)
        else:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(formatted)
            print(f"Formateado: {filename}")


def _cmd_nuevo(args):
    """Comando 'alvz nuevo': crea proyectos desde plantillas."""
    if len(args) < 1:
        print("Uso: alvz nuevo <tipo> [nombre]")
        print("")
        print("Tipos disponibles:")
        print("  proyecto    Crea un proyecto Alvz completo")
        print("  api         Crea una API REST con FastAPI")
        print("  cli         Crea una aplicacion CLI")
        print("  lib         Crea una libreria Alvz")
        print("  test        Crea un archivo de test")
        sys.exit(1)
    
    tipo = args[0]
    nombre = args[1] if len(args) > 1 else "mi_proyecto"
    
    PLANTILLAS = {
        "proyecto": {
            "descripcion": "Proyecto Alvz completo",
            "archivos": {
                f"{nombre}/main.alvz": 
                    'importar "matematicas"\nimportar "cadenas"\nimportar "colecciones"\nimportar "testing"\n\nfuncion main() {\n\timprimir("Iniciando ' + nombre + '")\n}\n\nmain()\n',
                f"{nombre}/README.md": 
                    f"# {nombre}\n\nProyecto creado con Alvz.\n",
                f"{nombre}/.gitignore":
                    "__pycache__/\n*.pyc\ndist/\n",
            }
        },
        "api": {
            "descripcion": "API REST con FastAPI",
            "archivos": {
                f"{nombre}/main.alvz": 
                    'funcion bienvenida() {\n\tretornar {"mensaje": "' + nombre + ' API funcionando"}\n}\n\nfuncion listar_items() {\n\tretornar {"items": []}\n}\n\nfuncion crear_item(nombre, precio) {\n\tretornar {"creado": verdadero, "nombre": nombre, "precio": precio}\n}\n\nvariable rutas = {\n\t"/": "bienvenida",\n\t"/items": "listar_items",\n\t"/items": {"funcion": "crear_item", "metodo": "POST"}\n}\n\niniciar_servidor(8000, rutas)\n',
                f"{nombre}/README.md":
                    f"# {nombre}\n\nAPI REST creada con Alvz.\n",
            }
        },
        "cli": {
            "descripcion": "Aplicacion CLI",
            "archivos": {
                f"{nombre}/main.alvz":
                    'importar "sistema"\n\nfuncion main() {\n\timprimir("' + nombre + ' CLI")\n\timprimir("Comandos disponibles:")\n\timprimir("  1. Opcion 1")\n\timprimir("  2. Opcion 2")\n\timprimir("  3. Salir")\n\t\n\tvariable opcion = 0\n\tmientras opcion != 3 {\n\t\topcion = leer_numero()\n\t\tsi opcion == 1 {\n\t\t\timprimir("Ejecutando opcion 1")\n\t\t} sino si opcion == 2 {\n\t\t\timprimir("Ejecutando opcion 2")\n\t\t} sino si opcion == 3 {\n\t\t\timprimir("Hasta luego")\n\t\t} sino {\n\t\t\timprimir("Opcion invalida")\n\t\t}\n\t}\n}\n\nmain()\n',
                f"{nombre}/README.md":
                    f"# {nombre}\n\nCLI creada con Alvz.\n",
            }
        },
        "lib": {
            "descripcion": "Libreria Alvz",
            "archivos": {
                f"{nombre}/{nombre}.alvz":
                    'importar "matematicas"\nimportar "cadenas"\nimportar "colecciones"\n\nfuncion version() {\n\tretornar "0.1.0"\n}\n\nfuncion saludar(nombre) {\n\tretornar "Hola desde ' + nombre + '!"\n}\n',
                f"{nombre}/test_{nombre}.alvz":
                    'importar "testing"\nimportar "' + nombre + '"\n\ndescribir("' + nombre + ' tests")\n\nprobar("version devuelve string", funcion() {\n\tafirmar(tipo(version()) == "texto", "version debe ser texto")\n})\n\nprobar("saludar funciona", funcion() {\n\tafirmar_igual("Hola desde Mundo!", saludar("Mundo"), "saludo correcto")\n})\n\nresumen()\n',
            }
        },
        "test": {
            "descripcion": "Archivo de test",
            "archivos": {
                f"{nombre}.alvz":
                    'importar "testing"\n\nfuncion suma(a, b) {\n\tretornar a + b\n}\n\nfuncion resta(a, b) {\n\tretornar a - b\n}\n\ndescribir("Tests de ' + nombre.replace('test_', '').replace('_test', '') + '")\n\nprobar("suma funciona", funcion() {\n\tafirmar_igual(5, suma(2, 3), "2 + 3 = 5")\n})\n\nprobar("resta funciona", funcion() {\n\tafirmar_igual(3, resta(5, 2), "5 - 2 = 3")\n})\n\nprobar("valores negativos", funcion() {\n\tafirmar_igual(-1, resta(2, 3), "2 - 3 = -1")\n})\n\nresumen()\n',
            }
        }
    }
    
    if tipo not in PLANTILLAS:
        print(f"Error: tipo '{tipo}' no reconocido.")
        print("Tipos disponibles: proyecto, api, cli, lib, test")
        sys.exit(1)
    
    plantilla = PLANTILLAS[tipo]
    archivos = plantilla["archivos"]
    
    for ruta, contenido in archivos.items():
        dir_name = os.path.dirname(ruta)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(contenido)
        print(f"  Creado: {ruta}")
    
    print(f"\n[OK] Proyecto '{nombre}' de tipo '{tipo}' creado.")


def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "test":
            _cmd_test(sys.argv[2:])
            return
        
        if cmd == "fmt":
            _cmd_fmt(sys.argv[2:])
            return
        
        if cmd == "nuevo":
            _cmd_nuevo(sys.argv[2:])
            return
        
        if cmd in ("install", "uninstall", "search", "list-packages"):
            from .core.package_manager import cli as pkg_cli
            pkg_cli()
            return
        
        if cmd == "build":
            from .core.compiler import cli as build_cli
            build_cli()
            return

        if cmd == "debug":
            from .lsp.dap import DAPServer
            dap = DAPServer()
            dap.run()
            return

        if cmd == "bench":
            from .core.benchmarks import main as bench_main
            bench_main()
            return

        if cmd == "fix":
            from .core.fixer import main as fix_main
            fix_main()
            return

    optimize_flag = False
    check_types_flag = True
    filenames = []
    for arg in sys.argv[1:]:
        if arg in ('--optimize', '-O'):
            optimize_flag = True
        elif arg in ('--no-check-types', '-NT'):
            check_types_flag = False
        elif arg in ('--version', '-V'):
            print(f"Alvz v{VERSION}")
            sys.exit(0)
        elif arg.startswith('-'):
            print(f"Error: Opcion desconocida '{arg}'")
            sys.exit(1)
        else:
            filenames.append(arg)

    if filenames:
        for filename in filenames:
            try:
                with open(filename, 'r', encoding='utf-8-sig') as f:
                    codigo_fuente = f.read()

                lexer = Lexer(codigo_fuente)
                tokens = lexer.tokenize()
                parser = Parser(tokens)
                bytecode, constants, line_map, funcs = parser.compile(
                    optimize=optimize_flag, check_types=check_types_flag
                )
                source_lines = codigo_fuente.split('\n')
                vm = VM(bytecode, constants, line_map, funcs, source_lines)
                vm.run()

            except Exception as e:
                print(f"Error: {e}")
                sys.exit(1)
    else:
        if optimize_flag:
            print("Modo interactivo no soporta --optimize")
        repl()
