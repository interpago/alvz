# Alvz Language (v0.5)

Un lenguaje de programación interpretado con sintaxis completamente en español, basado en una Máquina Virtual (VM) de pila.

## Instalación Local

Para poder usar el comando `alvz` desde cualquier parte de tu terminal, instala el paquete en modo editable:

```bash
pip install -e .
```

## Uso

Una vez instalado, puedes ejecutar tus archivos `.alvz` directamente:

```bash
alvz programa.alvz
```

## Sintaxis Básica

- **Variables**: `variable nombre = "valor"`
- **Imprimir**: `imprimir("mensaje")`
- **Lectura**: `variable dato = leer()`
- **Condicionales**: `si (condicion) { ... } sino { ... }`
- **Bucles**: `mientras (condicion) { ... }`
- **Operadores**: `+`, `-`, `*`, `/`, `==`, `>`, `<`
