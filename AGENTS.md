# AGENTS.md - Alvz Language

## Goal
- Profesionalizar Alvz a lenguaje avanzado: POO, LSP, DAP, módulos, StdLib, tipado estático, async/await con event loop real, compilación nativa, package manager.

## Constraints & Preferences
- pytest para tests.
- Lenguaje completo en español (keywords, mensajes de error).
- Herencia vía `clase Hijo de Padre`.
- Constructor por convención: `funcion inicializar()`.
- `self` automático como primer parámetro en métodos de instancia.
- Métodos estáticos con `funcion estatico nombre(args)`.
- Getter/setter con `propiedad nombre { obtener { } establecer(valor) { } }`.
- LSP y DAP manuales vía JSON-RPC sobre stdin/stdout.
- `obtener`, `establecer`, `propiedad` en `_IDENT_KEYWORDS`.

## Progress
### Done
- **Tipado estático**: `type_checker.py`. Verifica anotaciones, parámetros, retorno, llamadas. `--check-types` / `-T`. 21 tests.
- **Async/await**: tokens `ASYNC`, `AGUARDAR`; opcodes `OP_ASYNC_CALL` (76), `OP_AWAIT` (77); event loop con `ThreadPoolExecutor` (concurrencia real).
- **Optimizador de bytecode**: `optimizer.py` con plegado de constantes, código muerto, reasignación de saltos. `--optimize` / `-O`.
- **Compilación nativa**: `compiler.py` — PyInstaller (bytecode embebido) + Nuitka (Python→C++→nativo). `alvz build` y `alvz build --nuitka`. Todos los 82 opcodes funcionan.
- **Instalador Windows**: `setup.py`, `alvz.spec`. Reconstruidos `dist/alvz.exe` e `Instalador_Alvz.exe`.
- **VS Code extension v1.3.0**: resaltado semántico (SemanticTokensProvider) + autocompletado real (CompletionItemProvider). Empaquetada como `.vsix` (12.34 KB).
- **Documentación**: `public/index.html` con docs completos, ejemplos, favicon. Deploy a Firebase (https://alvzes.web.app).
- **ZIP de distribución**: `public/alvz_v0.15.0.zip` con alvz.exe, Instalador, VSIX y StdLib.
- **Package manager**: 30 paquetes en `github.com/interpago/alvz-packages`. Soportan `install`, `uninstall`, `search`, `list-packages`, `info`.
- **Importar desde paquetes**: `_import_file` busca en `~/.alvz/packages/<name>/`.
- **StdLib (8 módulos)**: matematicas, cadenas, colecciones, http, fecha, testing, sistema, sqlite.
- **Test runner**: `alvz test <archivo/directorio>` — descubre y ejecuta tests `.alvz` automáticamente.
- **Formateador**: `alvz fmt <archivo>` — formatea código (indentación de llaves). `--check` para solo verificar.
- **Scaffolding**: `alvz nuevo <tipo> [nombre]` — genera proyectos (proyecto, api, cli, lib, test).
- **450 tests pasando**.
- **Funciones anónimas (lambdas)**, **`global` keyword**, **`cada` standalone**, **acceso encadenado**, **iteración diccionarios**, **keyword-identifiers** corregidos.
- **LSP con parser real**: `Analyzer._analyze()` ejecuta `Parser.compile()` para errores reales de sintaxis/semántica.
- **Stack traces mejorados**: `_build_stack_trace()` muestra la línea de código fuente ofensiva. VM acepta `source_lines`.
- **Type checking automático**: `check_types=True` por defecto. Flag `--no-check-types` / `-NT`.
- **DAP CLI**: `alvz debug` ejecuta el servidor DAP.
- **GitHub Actions CI/CD**: `.github/workflows/tests.yml` — Python 3.10-3.12 en push/PR.
- **REPL mejorado**: historial (readline), colores ANSI, autocompletado con Tab, prompt multinea.
- **Benchmarks**: `alvz bench` ejecuta y mide velocidad de bytecode (fibonacci, bucles, listas, etc.).
- **Fixer**: `alvz fix [--dry-run]` detecta imports faltantes, variables no usadas, globals duplicados.
- **Compilación nativa vía Nuitka**: `alvz build --nuitka` compila Python→C++→nativo.

### In Progress
- N/A

### Blocked
- LLVM/WASM: No hay bindings ni toolchain integrados. El approach correcto requeriría llvmlite (Python→LLVM IR) o traducir bytecode a WASM vía emscripten/wasi-sdk. Es un proyecto grande (>500 líneas de backend) que no se ha iniciado.

## Key Decisions
- Event loop real vía `ThreadPoolExecutor` + futuros: concurrencia real para `esperar()` en paralelo.
- Package manager: registro JSON vía GitHub raw. Index URL: `https://raw.githubusercontent.com/interpago/alvz-packages/main/index.json`.
- `run()` acepta `output_buffer=None` — si se pasa, usa ese buffer sin resetear.
- Forward references para funciones: pre-scan recolecta nombres de funciones antes de compilar.
- StdLib ampliada usa funciones del VM via opcodes, no implementación Python directa.

## Next Steps
- Nada urgente. Mantenimiento, más paquetes, y si hay interés: compilador WASM real.

## Critical Context
- `run(output_buffer=None)` en VM: si se pasa buffer, lo usa sin resetear.
- `package_manager.py` usa `ALVZ_DIR = ~/.alvz` y `PACKAGES_DIR = ~/.alvz/packages/`.
- `_import_file()` busca en: ruta literal, +.alvz, stdlib/, stdlib/ +.alvz, `~/.alvz/packages/<name>/<name>.alvz`.
- Comandos CLI: `alvz test`, `alvz fmt`, `alvz nuevo`, `alvz install`, `alvz build`, `alvz debug`, `alvz bench`, `alvz fix`.
- `alvz.spec` con `datas=[('alvz/stdlib/*.alvz', 'alvz/stdlib')]`.

## Relevant Files
- `alvz/core/vm.py`: Coroutine, EventLoop, opcodes HTTP/SQLite, run(output_buffer=None), _import_file(), source_lines.
- `alvz/core/compiler.py`: build() con PyInstaller y Nuitka. `--nuitka` flag.
- `alvz/core/benchmarks.py`: Benchmarks de VM. `alvz bench`.
- `alvz/core/fixer.py`: Corrector automático. `alvz fix`.
- `alvz/core/package_manager.py`: Package, fetch_registry, install/uninstall/search/list/info. 30 paquetes.
- `alvz/core/bytecode.py`: OP_DICT_KEYS=82, OP_SOLICITUD_HTTP=81, OP_SQLITE_ABRIR=78, etc.
- `alvz/core/lexer.py`: tokens SQLITE_ABRIR, SQLITE_EJECUTAR, SQLITE_CONSULTAR, SOLICITUD_HTTP, GLOBAL.
- `alvz/core/parser_base.py`: compile() con _pre_scan_functions() para forward references. compile_global().
- `alvz/core/parser.py`: _compile_anonymous_function(), _compile_chained_access(), factor() con FUNCION.
- `alvz/lsp/analyzer.py`, `server.py`, `dap.py`, `protocol.py`: LSP + DAP real.
- `alvz/repl.py`: main() con todos los subcomandos. REPL con colores, historial, autocompletado.
- `alvz/stdlib/`: 8 módulos (matematicas, cadenas, colecciones, http, fecha, testing, sistema, sqlite).
- `alvz-extension/`: VS Code extension v1.3.0 con semántico + autocompletado.
- `registry/`: index.json + 30 paquetes en packages/.
- `.github/workflows/tests.yml`: CI/CD.
- `public/index.html`: Documentación completa desplegada en Firebase.
