"""Tests para los benchmarks de rendimiento de Alvz."""

from alvz.core.benchmarks import ejecutar_benchmark, _EJEMPLOS


class TestBenchmark:
    def test_ejecutar_benchmark_retorna_floats(self):
        for nombre, codigo in list(_EJEMPLOS.items())[:2]:
            min_time, avg_time = ejecutar_benchmark(nombre, codigo, repeticiones=1)
            assert isinstance(min_time, float)
            assert isinstance(avg_time, float)
            assert min_time >= 0
            assert avg_time >= 0
            assert min_time <= avg_time

    def test_benchmark_fibonacci(self):
        min_time, avg_time = ejecutar_benchmark('fibonacci', _EJEMPLOS['fibonacci'], repeticiones=1)
        assert min_time >= 0

    def test_benchmark_bucle(self):
        min_time, avg_time = ejecutar_benchmark('bucle', _EJEMPLOS['bucle'], repeticiones=1)
        assert min_time >= 0

    def test_lista_ejemplos_no_vacia(self):
        assert len(_EJEMPLOS) >= 7

    def test_nombres_benchmarks(self):
        esperados = ['fibonacci', 'bucle', 'lista', 'strings', 'diccionario', 'matematicas', 'condicionales']
        for nombre in esperados:
            assert nombre in _EJEMPLOS, f"Falta benchmark '{nombre}'"
