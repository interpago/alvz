import sys
sys.path.insert(0, '.')
from alvz.core.lexer import Lexer
from alvz.core.parser import Parser
from alvz.core.wasm_compiler import WasmCompiler, _GET_LOCAL, _I32, OpCode, _SET_LOCAL

codigo = '42'
lexer = Lexer(codigo)
tokens = lexer.tokenize()
parser = Parser(tokens)
bc, consts, lm, funcs = parser.compile()

original_check = WasmCompiler._check_op
handler_sizes = []
handler_names = []

def tracking_check(self, opcode, handler_bytes):
    result = original_check(self, opcode, handler_bytes)
    handler_sizes.append(len(result))
    handler_names.append(f"{opcode} ({int(opcode)})")
    return result

WasmCompiler._check_op = tracking_check
compiler = WasmCompiler(bc, consts, funcs, lm)
wasm_bytes = compiler.compile()
WasmCompiler._check_op = original_check

# Calculate code_start properly
def decode_leb128(data, pos):
    result = 0
    shift = 0
    while True:
        byte = data[pos]
        result |= (byte & 0x7f) << shift
        shift += 7
        pos += 1
        if not (byte & 0x80):
            break
    return result, pos

pos = 8
code_start = None
while pos < len(wasm_bytes):
    section_id = wasm_bytes[pos]
    s = pos + 1
    length, _ = decode_leb128(wasm_bytes, s)
    _, s = decode_leb128(wasm_bytes, s)
    content_start = s
    section_end = s + length
    if section_id == 10:
        code_count, cp = decode_leb128(wasm_bytes, content_start)
        for func_idx in range(code_count):
            body_size, cp = decode_leb128(wasm_bytes, cp)
            body_start = cp
            lpos = cp
            local_decl_count, lpos = decode_leb128(wasm_bytes, lpos)
            for _ in range(local_decl_count):
                cnt, lpos = decode_leb128(wasm_bytes, lpos)
                lpos += 1
            code_start = lpos
    pos = section_end

err_file_off = 6206
err_code_off = err_file_off - code_start

init_size = 4 + 2 + 2 + 10
offset = init_size
print(f"Code start at file offset: {code_start}")
print(f"Error at code offset: {err_code_off}")
print(f"Init size: {init_size}")
for i, (name, size) in enumerate(zip(handler_names, handler_sizes)):
    end = offset + size
    if offset <= err_code_off < end:
        rel = err_code_off - offset
        print(f">>> ERROR in handler {name} at relative offset +{rel}")
        print(f"    Handler range [{offset}:{end}], size={size}")
        break
    offset = end
