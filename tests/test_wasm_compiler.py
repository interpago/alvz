"""Test: compilar Alvz a WASM y ejecutar con wasmtime."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alvz.core.lexer import Lexer
from alvz.core.parser import Parser
from alvz.core.wasm_compiler import WasmCompiler
import wasmtime

# Programa Alvz simple: imprimir 2 + 3
codigo = """
variable x = 2 + 3
imprimir(x)
"""

print("=== Compilando Alvz a bytecode ===")
lexer = Lexer(codigo)
tokens = lexer.tokenize()
parser = Parser(tokens)
bytecode, constants, line_map, functions = parser.compile()
print(f"Bytecode ({len(bytecode)} ops): {[int(b) for b in bytecode]}")
print(f"Constants: {constants}")
print(f"Functions: {functions}")

print("\n=== Compilando bytecode a WASM ===")
compiler = WasmCompiler(bytecode, constants, functions, line_map)
wasm_bytes = compiler.compile()
print(f"WASM generado: {len(wasm_bytes)} bytes")

print("\n=== Ejecutando WASM con wasmtime ===")
# Crear store y modulo
store = wasmtime.Store()
module = wasmtime.Module(store.engine, wasm_bytes)

# Definir funciones host
printed_values = []

def print_num(val: float):
    printed_values.append(f"num:{val}")
    print(f"  [host] print_num({val})")

def print_bool(val: int):
    printed_values.append(f"bool:{val}")
    print(f"  [host] print_bool({val})")

def print_str(ptr: int, length: int):
    memory = instance.exports(store)["memory"]
    if memory:
        try:
            data = memory.read(store, ptr, ptr + length)
            text = data.decode('utf-8', errors='replace')
            printed_values.append(f"str:{text}")
            print(f"  [host] print_str({text})")
        except Exception as e:
            print(f"  [host] print_str error: {e}")

# Linkear
linker = wasmtime.Linker(store.engine)
linker.define(store, "alvz", "print_num", wasmtime.Func(store, wasmtime.FuncType([wasmtime.ValType.f64()], []), print_num))
linker.define(store, "alvz", "print_bool", wasmtime.Func(store, wasmtime.FuncType([wasmtime.ValType.i32()], []), print_bool))
linker.define(store, "alvz", "print_str", wasmtime.Func(store, wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32()], []), print_str))

# Instanciar
instance = linker.instantiate(store, module)
main_func = instance.exports(store)["main"]

print("\n  Ejecutando main()...")
try:
    main_func(store)
    print(f"  Output: {printed_values}")
except Exception as e:
    print(f"  Error: {e}")

print("\n=== Prueba completada ===")
