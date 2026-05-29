import sys
sys.path.insert(0, '.')
from alvz.core.lexer import Lexer
from alvz.core.parser import Parser

# Check what bytecode is generated for simple expressions
for codigo in ['42', 'imprimir(42)', 'verdadero', 'imprimir(verdadero)']:
    lexer = Lexer(codigo)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    bc, consts, lm, funcs = parser.compile()
    print(f"\n=== {codigo} ===")
    print(f"  Bytecode ({len(bc)}): {list(bc)}")
    print(f"  Consts: {consts}")
    print(f"  Funcs: {funcs}")
