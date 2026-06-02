# Contribuyendo a Alvz

Gracias por tu interés en contribuir a Alvz, el lenguaje de programación en español.

## Código de Conducta

Sé respetuoso, inclusivo y constructivo. No se tolera discriminación ni acoso.

## Cómo Contribuir

1. **Fork** el repositorio y crea una rama desde `main`.
2. **Desarrolla** tu cambio con tests.
3. **Asegura** que pases los checks:
   ```bash
   python -m pytest tests/ -q
   python -m ruff check alvz/ tests/
   ```
4. **Haz commit** con mensaje descriptivo en español.
5. **Abre un Pull Request** a `main`.

## Estándares

- **Código**: Python 3.10+, tipado opcional, line-length 120.
- **Tests**: `pytest` para todo código nuevo.
- **Linter**: `ruff` (select E/F/W).
- **Idioma**: Todo en español (keywords, errores, docs, commits).
- **Sin dependencias innecesarias**: minimizar requirements.

## Reportar Issues

Usa el rastreador de GitHub para bugs, features o dudas.
Incluye: versión, código de ejemplo, comportamiento esperado vs real.
