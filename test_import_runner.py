import sys
sys.path.insert(0, '.')
from alvz.core.lexer import Lexer
from alvz.core.parser import Parser
from alvz.core.vm import VM
from alvz.core.bytecode import OpCode

with open('test_uuid_import.alvz', encoding='utf-8') as f:
    codigo = f.read()
lexer = Lexer(codigo)
tokens = lexer.tokenize()
parser = Parser(tokens)
try:
    bytecode, constants, line_map, funcs = parser.compile()
    print('Compilacion OK, bytecode:', len(bytecode), 'ops')
    vm = VM(bytecode, constants, line_map, funcs, codigo.split('\n'))
    vm.run()
    print('Ejecucion completada')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
