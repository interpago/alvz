# Alvz en Español

**Alvz** es un lenguaje de programación completo en **español** con tipado dinámico, OOP, async/await, SQLite, HTTP, compilación WASM y más.

## Características

| # | Característica | Descripción |
|---|---|---|
| 1 | **Resaltado semántico** | Variables, funciones, clases, builtins con colores diferenciados |
| 2 | **Autocompletado** | Keywords, stdlib, snippets de estructuras comunes |
| 3 | **Snippets** | `funcion`, `si`, `mientras`, `clase`, `intentar`, `cada`, `para` |
| 4 | **Iconos de archivo** | Tema de iconos para archivos `.alvz` |
| 5 | **LSP** | Hover, ir a definición, diagnóstico (requiere `alvz` CLI) |

## Instalación

```bash
# Instalar el lenguaje
pip install alvz-lenguaje

# Verificar
alvz --version
```

## Ejemplo

```alvz
funcion fibonacci(n) {
    si (n <= 1) { retornar n }
    retornar fibonacci(n - 1) + fibonacci(n - 2)
}

variable resultado = fibonacci(10)
imprimir("Fibonacci(10) = " + resultado)
```

## Documentación

- [Sitio web oficial](https://alvzes.web.app)
- [Especificación formal del lenguaje](https://github.com/interpago/alvz/blob/main/ESPECIFICACION.md)
- [Repositorio GitHub](https://github.com/interpago/alvz)

## Requisitos

- VS Code `^1.79.0`
- Python 3.10+ (para LSP)

## Créditos

Desarrollado por la comunidad Alvz. ¡Contribuciones bienvenidas!
