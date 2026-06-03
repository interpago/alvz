# Changelog

## [0.18.0] — 2026-06-02

### Added
- DAP v1 completo con parcheo de bytecode (`OP_DEBUG_BREAK = 83`)
- `alvz publish <dir>`: empaqueta proyectos con `alvz.json`
- `alvz fmt`: formateador token-aware de código fuente
- `--safe` mode: sandbox de FS, red bloqueada, límites de tiempo/recursión/pila
- `ESPECIFICACION.md`: especificación formal con EBNF, sistema de tipos, 83 opcodes
- Compilación WASM compatible con wasmtime 45 (memoria importada, host calls sin `caller`)
- `OP_SLICE` para strings vía `HOST_SLICE = 44`

### Changed
- VS Code extension: engine `^1.79.0`, `SemanticTokensBuilder.push()` migrado a `number[]`
- Orden de patrones en gramática TextMate: `funcion estatico` antes que `funcion`
- DAP reescrito: de hook por instrucción a parcheo de bytecode (0 overhead sin depuración)

### Fixed
- Crash de VS Code 1.122.1 con `SemanticTokensBuilder` API
- Strings corruptos en WASM con import memory del host
- BOM `utf-8-sig` en `alvz.json`

## [0.17.0] — 2026-05-15

### Added
- LSP completo con autocompletado, hover, ir a definición
- DAP inicial con hook de depuración
- 13 módulos en stdlib (`.alvz`)
- Optimizador de bytecode (230 líneas)
- Type checker estático opcional (457 líneas)
- Package manager con 30 paquetes

### Changed
- VM: 83 opcodes con async/event loop, OOP, HTTP, SQLite, debug
- REPL/CLI con subcomandos: `test | install | uninstall | bench | fix`

## [0.16.0] — 2026-04-20

### Added
- Programación orientada a objetos: clases, herencia, propiedades
- Servidor HTTP con FastAPI/uvicorn
- Cliente HTTP completo (GET, POST, PUT, DELETE)
- SQLite integrado
- Soporte JSON

## [0.15.0] — 2026-03-25

### Added
- Compilación WASM experimental
- Corrutinas y event loop async/await
- Manejo de errores con intentar/capturar/lanzar
- Expresiones regulares

## [0.10.0] — 2026-01-10

### Added
- Funciones, condicionales, ciclos
- Listas, diccionarios, strings
- Operadores aritméticos y lógicos
- Entrada/salida básica

## [0.5.0] — 2025-11-01

### Added
- Lexer, parser y VM básicos
- Variables y constantes
- Tipos: número, texto, booleano, nulo
- `imprimir()` y `leer()`
