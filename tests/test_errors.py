"""Tests para el modulo de errores y sugerencias de Alvz."""

from alvz.core.errors import obtener_sugerencia, KEYWORDS_ALVZ


def test_sugerencia_exacta():
    """Una palabra exacta debe retornar la misma palabra."""
    assert obtener_sugerencia('imprimir') == 'imprimir'


def test_sugerencia_typo_cercano():
    """Palabras con typos deben sugerir la keyword correcta."""
    assert obtener_sugerencia('imprmir') == 'imprimir'
    assert obtener_sugerencia('funcion') == 'funcion'
    assert obtener_sugerencia('funcon') == 'funcion'


def test_sugerencia_sin_coincidencia():
    """Palabras muy distintas deben retornar None."""
    assert obtener_sugerencia('xyzzy') is None
    assert obtener_sugerencia('foobar') is None


def test_sugerencia_con_opciones_personalizadas():
    opciones = ['rojo', 'verde', 'azul']
    assert obtener_sugerencia('verde', opciones) == 'verde'
    assert obtener_sugerencia('verda', opciones) == 'verde'
    assert obtener_sugerencia('amarillo', opciones) is None


def test_keywords_list_not_empty():
    assert len(KEYWORDS_ALVZ) > 50  # debe tener 65+ keywords
    assert 'funcion' in KEYWORDS_ALVZ
    assert 'variable' in KEYWORDS_ALVZ
    assert 'clase' in KEYWORDS_ALVZ
    assert 'si' in KEYWORDS_ALVZ
    assert 'retornar' in KEYWORDS_ALVZ
