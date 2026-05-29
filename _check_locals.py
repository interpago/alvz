import sys
sys.path.insert(0, '.')
from alvz.core.lexer import Lexer
from alvz.core.parser import Parser
from alvz.core.wasm_compiler import WasmCompiler

codigo = '42'
lexer = Lexer(codigo)
tokens = lexer.tokenize()
parser = Parser(tokens)
bc, consts, lm, funcs = parser.compile()
compiler = WasmCompiler(bc, consts, funcs, lm)
wasm_bytes = compiler.compile()

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

# Find code section
pos = 8
while pos < len(wasm_bytes):
    section_id = wasm_bytes[pos]
    s = pos + 1
    length, _ = decode_leb128(wasm_bytes, s)
    _, s = decode_leb128(wasm_bytes, s)
    content_start = s
    section_end = s + length
    if section_id == 10:  # Code
        code_count, cp = decode_leb128(wasm_bytes, content_start)
        print(f"Code count: {code_count}")
        for i in range(code_count):
            body_size, cp = decode_leb128(wasm_bytes, cp)
            body_start = cp
            body_end = cp + body_size
            print(f"\nFunction {i}: body_size={body_size}, range=[{body_start}:{body_end}]")
            
            # Parse local declarations
            lpos = body_start
            local_decl_count, lpos = decode_leb128(wasm_bytes, lpos)
            print(f"  Local decl groups: {local_decl_count}")
            total_locals = 0
            loc_info = []
            for g in range(local_decl_count):
                cnt, lpos = decode_leb128(wasm_bytes, lpos)
                typ_byte = wasm_bytes[lpos]
                lpos += 1
                typ_name = {0x7f: 'i32', 0x7e: 'i64', 0x7d: 'f32', 0x7c: 'f64'}.get(typ_byte, f'?{typ_byte:02x}')
                loc_info.append(f"  Group {g}: count={cnt}, type={typ_name}")
                total_locals += cnt
            
            for l in loc_info:
                print(l)
            print(f"  Total locals: {total_locals} (indices 0-{total_locals-1})")
            print(f"  Code starts at offset: {lpos}")
    pos = section_end
