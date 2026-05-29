import sys, traceback
sys.path.insert(0, '.')
from alvz.core.lexer import Lexer
from alvz.core.parser import Parser
from alvz.core.wasm_compiler import WasmCompiler
import wasmtime

def test(codigo, nombre='test'):
    try:
        lexer = Lexer(codigo)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        bc, consts, lm, funcs = parser.compile()
        compiler = WasmCompiler(bc, consts, funcs, lm)
        wasm_bytes = compiler.compile()
        module = wasmtime.Module(wasmtime.Engine(), wasm_bytes)
        print(f'OK  {nombre}')
        return True
    except Exception as e:
        msg = str(e)
        if 'offset' in msg:
            # Extract offset
            import re
            m = re.search(r'offset (\d+)', msg)
            offset = int(m.group(1)) if m else '?'
            # Show context around offset
            if hasattr(wasm_bytes, '__len__') and isinstance(offset, int):
                start = max(0, offset - 20)
                end = min(len(wasm_bytes), offset + 20)
                ctx = wasm_bytes[start:end].hex(' ')
                marker = ' ' * (3 * (offset - start)) + '^^^'
                print(f'ERR {nombre} (offset {offset}): {msg[:100]}')
                print(f'    ctx: {ctx}')
                print(f'    mrk: {marker}')
            else:
                print(f'ERR {nombre}: {msg[:120]}')
        else:
            print(f'ERR {nombre} (no offset): {msg[:120]}')
        return False

# Basic tests to narrow down
tests = [
    ('42', 'num'),
    ('verdadero', 'bool'),
    ('"hola"', 'str'),
    ('nulo', 'null'),
    ('imprimir(42)', 'print_num'),
    ('imprimir(verdadero)', 'print_bool'),
    ('imprimir("hola")', 'print_str'),
    ('variable x = 42\nimprimir(x)', 'var_load'),
    ('variable x = 42\nvariable y = x', 'var_to_var'),
    ('2 + 3', 'add'),
    ('2 > 1', 'gt'),
    ('si verdadero y falso { imprimir(1) }', 'and'),
    ('[1, 2, 3]', 'list_new'),
    ('{1, 2}', 'set_new'),
]
for codigo, nombre in tests:
    test(codigo, nombre)
