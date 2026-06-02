"""Tests para el auto-fixer de Alvz."""

import tempfile
import os
from alvz.core.fixer import analizar_y_sugerir, fix_file


def _escribir_temp(codigo):
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.alvz', delete=False, encoding='utf-8')
    tmp.write(codigo)
    tmp.close()
    return tmp.name


def test_sugerir_import_faltante():
    codigo = 'factorial(5)'
    archivo = _escribir_temp(codigo)
    try:
        sugerencias = analizar_y_sugerir(archivo)
        assert any(s['tipo'] == 'import_faltante' and s['funcion'] == 'factorial' for s in sugerencias)
    finally:
        os.unlink(archivo)


def test_sin_problemas():
    codigo = 'imprimir("hola")\nvariable x = 10\nimprimir(x)'
    archivo = _escribir_temp(codigo)
    try:
        sugerencias = analizar_y_sugerir(archivo)
        assert len(sugerencias) == 0
    finally:
        os.unlink(archivo)


def test_global_duplicado():
    codigo = 'global x\nglobal x'
    archivo = _escribir_temp(codigo)
    try:
        sugerencias = analizar_y_sugerir(archivo)
        assert any(s['tipo'] == 'global_duplicado' for s in sugerencias)
    finally:
        os.unlink(archivo)


def test_fix_file_agrega_import():
    codigo = 'factorial(5)'
    archivo = _escribir_temp(codigo)
    try:
        result = fix_file(archivo, dry_run=True)
        assert not result
        with open(archivo, 'r') as f:
            contenido = f.read()
        assert contenido == codigo  # dry-run no modifica
    finally:
        os.unlink(archivo)


def test_fix_file_dry_run_no_modifica():
    codigo = 'variable x = 10\nimprimir("hola")'
    archivo = _escribir_temp(codigo)
    try:
        fix_file(archivo, dry_run=True)
        with open(archivo, 'r') as f:
            contenido = f.read()
        assert contenido == codigo
    finally:
        os.unlink(archivo)


def test_funcion_keyword_no_sugerida():
    codigo = 'funcion si() {imprimir(1)}\nsi()'
    archivo = _escribir_temp(codigo)
    try:
        sugerencias = analizar_y_sugerir(archivo)
        imports_faltantes = [s for s in sugerencias if s['tipo'] == 'import_faltante']
        assert len(imports_faltantes) == 0
    finally:
        os.unlink(archivo)
