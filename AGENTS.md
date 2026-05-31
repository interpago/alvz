# AGENTS.md - Alvz Language

## Goal
- Revisar, limpiar y profesionalizar el proyecto Alvz (lenguaje en español) — linting con Ruff, docs actualizadas, deploy a Firebase, push a GitHub.

## Constraints & Preferences
- pytest para tests.
- Lenguaje completo en español (keywords, mensajes de error).
- Ruff como linter (line-length=120, select E/F/W).
- Compilación WASM compatible con wasmtime 45 (memoria importada, host calls sin `caller`).
- Deploy en Firebase Hosting (alvzes.web.app).

## Progress
### Done
- **Ruff configurado**: `pyproject.toml` con line-length=120, select E/F/W. Pre-commit hooks con ruff --fix y ruff-format.
- **133 errores de lint corregidos**: F401 (imports no usados), F541 (f-strings sin placeholders), F841 (variables asignadas no usadas), W293 (espacios en líneas en blanco), E741 (nombres ambiguos), E402 (imports no al inicio), E401 (múltiples imports en una línea), F811 (redefinición de import).
- **Documentación web actualizada**: `public/index.html` con nueva sección "Arquitectura Interna de Alvz" que documenta las 12 capas del lenguaje (Lexer, Parser, Bytecode/82 opcodes, VM, Optimizador, Type Checker, WASM, Nativo, LSP, DAP, StdLib/13 módulos, Package Manager/30 paquetes). Estadísticas del proyecto (549 tests, ~12,000 líneas Python).
- **Deploy a Firebase**: https://alvzes.web.app — deploy exitoso (2 archivos, 151 KB).
- **Compatibilidad wasmtime 45**: memoria compartida entre módulo y host, host functions sin `caller`, `_MemWrapper` con ctypes.
- **WASM strings corruptos**: fix con import memory del host en vez de memoria interna.
- **OP_SLICE para strings**: implementado vía host function HOST_SLICE = 44.
- **549 tests, 0 fallos, 0 errores**.

### In Progress
- N/A

### Blocked
- N/A

## Key Decisions
- **Import memory en WASM**: módulo importa `'alvz', 'memory'` del host compartiendo espacio de direcciones.
- **WASM: global vars en 0x9000**, locals en 0x8000.
- **Ruff --unsafe-fixes** usado para limpiar E401 (múltiples imports en una línea).

## Next Steps
- Benchmarks en CI para detectar regresiones de rendimiento.
- Compilar cada función Alvz a función WASM separada (no inline en dispatch loop).

## Critical Context
- **549 tests, 0 fallos, 0 errores** en ~2.2s.
- `ruff check --fix --unsafe-fixes alvz/ tests/` → 0 errores.
- `firebase deploy --only hosting` → https://alvzes.web.app
- Firebase project: `alvz-56156`, site: `alvzes`.

## Relevant Files
- `public/index.html`: Documentación web completa con 12 secciones técnicas (2763 líneas).
- `alvz/core/vm.py`: VM principal (1127 líneas), 82 opcodes, async/event loop, OOP, HTTP, SQLite.
- `alvz/core/parser.py` + `parser_base.py`: Parser/compiler (~2100 líneas).
- `alvz/core/wasm_compiler.py` + `wasm_encoder.py`: Compilador WASM (~2300 líneas).
- `alvz/core/wasm_runtime.py`: Runtime WASM (~713 líneas).
- `alvz/core/bytecode.py`: 82 opcodes.
- `alvz/core/type_checker.py`: Tipado estático (457 líneas).
- `alvz/core/optimizer.py`: Optimizador bytecode (230 líneas).
- `alvz/core/fixer.py`: Auto-fix (144 líneas).
- `alvz/core/compiler.py`: PyInstaller/Nuitka build (227 líneas).
- `alvz/core/package_manager.py`: 30 paquetes (224 líneas).
- `alvz/lsp/`: LSP + DAP (~880 líneas).
- `alvz/stdlib/`: 13 módulos `.alvz`.
- `alvz/repl.py`: REPL/CLI, VERSION = "0.18.0".
- `alvz-extension/package.json`: Extension VS Code v1.6.0.
- `firebase.json`, `.firebaserc`: Config Firebase.
- `AGENTS.md`: Este archivo.
