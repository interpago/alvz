# Alvz Language v0.18.0

Lenguaje de programación interpretado con sintaxis completamente en español. Orientado a objetos, asíncrono, con tipado estático opcional. Basado en una VM de pila con 83 opcodes y compilación a WebAssembly.

## Características

- **Sintaxis en español** — keywords, errores y documentación en español
- **Orientado a objetos** — clases, herencia, métodos estáticos, getters/setters, `super`
- **Async/await** — ejecución concurrente con `ThreadPoolExecutor`
- **Tipado opcional** — anotaciones de tipo con verificación estática (`--no-check-types` para deshabilitar)
- **83 opcodes** — VM de pila con bytecode completo (aritmética, control de flujo, closures, excepciones, debug)
- **13 módulos stdlib** — `matematicas`, `cadenas`, `colecciones`, `testing`, `json`, `csv`, `sistema`, `fecha`, `http`, `sqlite`, `aleatorio`, `expresiones_regulares`, `consola`
- **Compilación WASM** — genera binarios `.wasm` compatibles con wasmtime 45+
- **LSP + DAP** — language server con diagnósticos, completado, ir a definición, hover; debugger con breakpoints, paso a paso, inspección de variables
- **Extension VS Code** — disponible en el Marketplace como "Alvz en Español": resaltado semántico, 48 snippets, autocompletado, iconos
- **Modo seguro** — `--safe` restringe FS, red, imports y recursos
- **CLI completa** — `alvz archivo.alvz`, `alvz test`, `alvz fmt`, `alvz nuevo`, `alvz build`, `alvz fix`, `alvz bench`, `alvz debug`, `alvz install`
- **Standalone** — `alvz build` genera ejecutables con PyInstaller o Nuitka
- **626 tests** — cobertura de VM, parser, lexer, WASM, LSP, DAP, tipos, formatter, fixer, benchmarks

## Instalación

```bash
pip install -e .
```

Requiere Python 3.10+.

## Uso rápido

```bash
# Ejecutar archivo
alvz programa.alvz

# Ejecutar via WebAssembly (37+ opcodes nativos)
alvz --wasm programa.alvz

# REPL interactivo
alvz

# Ejecutar tests
alvz test tests/

# Formatear código
alvz fmt programa.alvz

# Verificar tipos estáticamente
alvz --no-check-types programa.alvz   # deshabilita type checker

# Modo seguro (sin red, FS restringido)
alvz --safe programa.alvz

# Compilar a ejecutable o WASM
alvz build programa.alvz
alvz build programa.alvz --wasm

# Nuevo proyecto
alvz nuevo proyecto mi_app

# Analizar y corregir
alvz fix programa.alvz

# Benchmarks
alvz bench

# Depurar
alvz debug
```

## Sintaxis básica

```alvz
variable nombre = "Mundo"
imprimir("Hola " + nombre)

si (edad >= 18) {
    imprimir("Mayor de edad")
} sino {
    imprimir("Menor de edad")
}

mientras (x > 0) {
    imprimir(x)
    x = x - 1
}

funcion factorial(n) {
    si (n <= 1) {
        retornar 1
    }
    retornar n * factorial(n - 1)
}

clase Persona {
    variable nombre = ""
    variable edad = 0

    funcion inicializar(n, e) {
        nombre = n
        edad = e
    }

    funcion saludar() {
        imprimir("Hola, soy " + nombre)
    }
}
```

## Documentación

- [Especificación formal del lenguaje](ESPECIFICACION.md)
- [Documentación web](https://alvzes.web.app)

## Proyecto

- GitHub: https://github.com/interpago/alvz
- Web: https://alvzes.web.app
- VS Code Marketplace: https://marketplace.visualstudio.com/items?itemName=alvz-project.alvz-language
- Licencia: GPL-3.0
