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

# Find code section to get code_start
pos = 8
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
            print(f"code_start file offset: {code_start}")
            print(f"code_start = body_start({body_start}) + local_decl_bytes({lpos - body_start})")
            break
    pos = section_end

# Now check what byte is at 6206 and scan for structure
offset = 6206
print(f"\nByte at {offset}: 0x{wasm_bytes[offset]:02x}")
# Compute error offset from code start
err_code_off = offset - code_start
print(f"Error at code offset: {err_code_off}")

# Look at context with correct alignment
start = max(0, offset - 30)
end = min(len(wasm_bytes), offset + 10)
print(f"\nFull context [{start}:{end}]:")
for j in range(start, end):
    b = wasm_bytes[j]
    marker = " <===" if j == offset else ""
    if b in (0x04, 0x05, 0x0b, 0x02, 0x03):
        names = {4: 'IF', 5: 'ELSE', 11: 'END', 2: 'BLOCK', 3: 'LOOP'}
        print(f"  {j}: {names[b]:5s} (0x{b:02x}){marker}")
    elif b in (0x20, 0x21, 0x22, 0x23, 0x24):
        idx = wasm_bytes[j+1]
        names = {32: 'local.get', 33: 'local.set', 34: 'local.tee', 35: 'global.get', 36: 'global.set'}
        print(f"  {j}: {names[b]:10s} {idx}{marker}")
    elif b in (0x36, 0x39):
        extra = f"{wasm_bytes[j+1]:02x} {wasm_bytes[j+2]:02x}"
        names = {0x36: 'i32.store', 0x39: 'f64.store'}
        print(f"  {j}: {names[b]:10s} {extra}{marker}")
    elif b == 0x41:
        val = wasm_bytes[j+1]
        print(f"  {j}: i32.const {val} (0x{val:02x}){marker}")
    elif b == 0x46:
        print(f"  {j}: i32.eq{marker}")
    elif b == 0xa2:
        print(f"  {j}: f64.mul{marker}")
