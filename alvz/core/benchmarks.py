import time
import io
import contextlib
from .lexer import Lexer
from .parser import Parser
from .vm import VM

_EJEMPLOS = {}

def _registrar(nombre, codigo):
    _EJEMPLOS[nombre] = codigo

_registrar("fibonacci", """
funcion fib(n) {
    si n <= 1 { retornar n }
    retornar fib(n-1) + fib(n-2)
}
fib(20)
""")

_registrar("bucle", """
variable s = 0
para i de 1 a 100000 {
    s = s + i
}
imprimir(s)
""")

_registrar("lista", """
variable lst = []
para i de 1 a 10000 {
    agregar(lst, i)
}
variable s = 0
cada x en lst {
    s = s + x
}
""")

_registrar("strings", """
variable t = ""
para i de 1 a 1000 {
    t = t + "hola"
}
variable n = longitud(t)
""")

_registrar("diccionario", """
variable d = {}
para i de 1 a 10000 {
    d["k" + i] = i
}
variable s = 0
cada k en d {
    s = s + d[k]
}
""")

_registrar("matematicas", """
variable r = 1
para i de 1 a 10000 {
    r = r * 2
    r = r / 2
    r = r + i
    r = r - i
}
""")

_registrar("condicionales", """
variable c = 0
para i de 1 a 100000 {
    si i % 2 == 0 {
        c = c + 1
    } sino {
        c = c - 1
    }
}
""")


def ejecutar_benchmark(nombre, codigo, repeticiones=3):
    tiempos = []
    for _ in range(repeticiones):
        inicio = time.perf_counter()
        try:
            lexer = Lexer(codigo)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            bytecode, constants, line_map, funcs = parser.compile(check_types=False)
            vm = VM(bytecode, constants, line_map, funcs)
            with contextlib.redirect_stdout(io.StringIO()):
                vm.run()
        except Exception:
            pass
        fin = time.perf_counter()
        tiempos.append(fin - inicio)
    return min(tiempos), sum(tiempos) / len(tiempos)


def main():
    print("=" * 50)
    print("  Alvz Benchmarks")
    print("=" * 50)
    total_min = 0
    for nombre in sorted(_EJEMPLOS.keys()):
        codigo = _EJEMPLOS[nombre]
        min_t, avg_t = ejecutar_benchmark(nombre, codigo)
        total_min += min_t
        print(f"  {nombre:20s}  min: {min_t*1000:8.2f}ms  avg: {avg_t*1000:8.2f}ms")
    print("-" * 50)
    print(f"  {'TOTAL (min)':20s}  {total_min*1000:8.2f}ms")
    print("=" * 50)


if __name__ == '__main__':
    main()
