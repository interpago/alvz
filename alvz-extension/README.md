# Alvz Language Support

Soporte oficial para **Alvz**, el lenguaje de programación en español con sistema de tipos, OOP, async/await, SQLite, HTTP, WASM y más.

## Características

- **Resaltado semántico** — variables, funciones, clases, keywords, strings, números con colores diferenciados
- **Autocompletado** — palabras clave, funciones de stdlib, snippets
- **Snippets** — estructuras comunes (`funcion`, `si`, `mientras`, `clase`, `intentar`, etc.)
- **Iconos de archivo** — tema de iconos para archivos `.alvz`
- **Soporte LSP** — hover, ir a definición, diagnóstico de errores (requiere `alvz` CLI instalado)

## Instalación

1. Instala Alvz: `pip install alvz-lenguaje`
2. Instala esta extensión desde VS Code marketplace
3. Abre o crea un archivo `.alvz`

## Ejemplo rápido

```alvz
funcion saludar(nombre) {
    imprimir("Hola, " + nombre)
}

variable nombre = leer()
saludar(nombre)
```

## Requisitos

- VS Code `^1.79.0`
- Python 3.10+ con `alvz-lenguaje` (para LSP)

## Documentación

- [Sitio web oficial](https://alvzes.web.app)
- [Especificación del lenguaje](https://github.com/interpago/alvz/blob/main/ESPECIFICACION.md)
- [Repositorio](https://github.com/interpago/alvz)
