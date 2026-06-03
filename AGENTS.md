# AGENTS.md - Alvz Language

## Goal
- Revisar, limpiar y profesionalizar el proyecto Alvz (lenguaje en español) — linting con Ruff, docs actualizadas, cobertura de tests, CI/CD, deploy a Firebase, push a GitHub.

## Constraints & Preferences
- pytest para tests.
- Lenguaje completo en español (keywords, mensajes de error).
- Ruff como linter (line-length=120, select E/F/W).
- Compilación WASM compatible con wasmtime 45 (memoria importada, host calls sin `caller`).
- Deploy en Firebase Hosting (alvzes.web.app).

## Progress
### Done
- **Documentación web**: `public/index.html` con arquitectura interna del lenguaje (12 capas), desplegada en https://alvzes.web.app
- **Firebase deploy**: exitoso, 2 archivos.
- **Compatibilidad wasmtime 45**: memoria compartida, host functions sin `caller`, `_MemWrapper`.
- **WASM strings corruptos**: fix con import memory del host.
- **OP_SLICE para strings**: via HOST_SLICE = 44.
- **DAP v1 con parcheo de bytecode**: VM corre a velocidad normal entre breakpoints (OP_DEBUG_BREAK = 83). Step mode usa hook temporal.
- **Modo seguro** (`--safe`): sandbox de FS, red bloqueada, límites de tiempo (30s), recursión (200 niveles), pila (10k).
- **Especificación formal** (`ESPECIFICACION.md`): EBNF, sistema de tipos, 83 opcodes documentados.
- **Formateador token-aware** (`alvz/core/formatter.py`): corrige bugs de indentación (`}` en nueva línea, doble espacio antes de `{`, espacio tras `.`).
- **Auto-fixer** (`alvz/core/fixer.py`): detección de imports faltantes, variables no usadas, globales duplicados.
- **alvz publish**: empaqueta proyectos con `alvz.json`, soporta BOM utf-8-sig.
- **CHANGELOG.md, LICENSE (MIT), CONTRIBUTING.md**: creados.
- **CI/CD expandido**: tests en todas las ramas + job de benchmarks.
- **VS Code extension**: engine `^1.79.0`, `SemanticTokensBuilder.push()` migrado a `number[]`, orden `funcion estatico` antes que `funcion`.
- **LSP completo**: autocompletado, hover, ir a definición.
- **Package manager**: 30 paquetes disponibles.
- **Optimizador de bytecode** (230 líneas), **Type checker estático** (457 líneas).

### In Progress
- N/A

### Blocked
- N/A

## Key Decisions
- **Import memory en WASM**: módulo importa `'alvz', 'memory'` del host compartiendo espacio de direcciones.
- **WASM**: global vars en 0x9000, locals en 0x8000.
- **DAP**: parcheo de bytecode en vez de hook por instrucción (0 overhead sin depuración).
- **Modo seguro**: flag `--safe` explícito en vez de sandbox automático.

## Next Steps
- Compilar cada función Alvz a función WASM separada (no inline en dispatch loop).
- Sistema de pruebas integrado para código `.alvz`.

## Critical Context
- **626 tests, 0 fallos, 0 errores** en ~13s.
- `ruff check alvz/ tests/` → 0 errores.
- `firebase deploy --only hosting` → https://alvzes.web.app
- Firebase project: `alvz-56156`, site: `alvzes`.
- Versión: 0.18.0.

## Relevant Files
- `public/index.html`: Documentación web completa (2763 líneas).
- `alvz/core/vm.py`: VM principal (~1390 líneas), 83 opcodes (incl. OP_DEBUG_BREAK).
- `alvz/core/parser.py` + `parser_base.py`: Parser/compiler (~2100 líneas).
- `alvz/core/wasm_compiler.py` + `wasm_encoder.py`: Compilador WASM (~2300 líneas).
- `alvz/core/wasm_runtime.py`: Runtime WASM (712 líneas).
- `alvz/core/bytecode.py`: 83 opcodes.
- `alvz/core/formatter.py`: Formateador token-aware (283 líneas).
- `alvz/core/fixer.py`: Auto-fix (171 líneas).
- `alvz/core/benchmarks.py`: Benchmarks de rendimiento (116 líneas).
- `alvz/core/compiler.py`: PyInstaller/Nuitka/WASM build (273 líneas).
- `alvz/core/package_manager.py`: 30 paquetes (224 líneas).
- `alvz/core/errors.py`: Sugerencias de errores (30 líneas).
- `alvz/lsp/dap.py`: DAP con parcheo de bytecode.
- `alvz/stdlib/`: 13 módulos `.alvz`.
- `alvz/repl.py`: REPL/CLI, VERSION = "0.18.0".
- `alvz-extension/package.json`: Extension VS Code v1.6.0.
- `CHANGELOG.md`, `LICENSE`, `CONTRIBUTING.md`: Documentación del proyecto.
- `ESPECIFICACION.md`: Especificación formal del lenguaje.
- `.github/workflows/tests.yml`: CI (lint + tests + benchmarks).
- `firebase.json`, `.firebaserc`: Config Firebase.
- `AGENTS.md`: Este archivo.
