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

# Find code section and get function 0 code
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
            body_end = cp + body_size
            lpos = cp
            local_decl_count, lpos = decode_leb128(wasm_bytes, lpos)
            for _ in range(local_decl_count):
                cnt, lpos = decode_leb128(wasm_bytes, lpos)
                lpos += 1
            code_start = lpos
            code = wasm_bytes[code_start:body_end]
            
            if func_idx == 0:
                # Search for else/if/end nesting around error
                err_off = 3559  # code offset of error
                
                # Find nested IF/ELSE/END structure
                # Scan from start to find matching IF for the ELSE at err_off
                stack = []  # track IF positions
                i = 0
                while i < len(code):
                    op = code[i]
                    if op == 0x04:  # IF
                        stack.append(i)
                        i += 2  # skip block type
                    elif op == 0x05:  # ELSE
                        if stack:
                            if_pos = stack[-1]
                            if i == err_off:
                                print(f"ELSE at code_offset {err_off} matches IF at code_offset {if_pos}")
                            # Don't pop; else is same level as IF
                        i += 1
                    elif op == 0x0b:  # END
                        if stack:
                            stack.pop()
                        i += 1
                    else:
                        # Skip instruction
                        if op == 0x41: i += 2  # i32.const 1 byte
                        elif op == 0x44: i += 9  # f64.const 8 bytes
                        elif op in (0x20, 0x21, 0x22, 0x23, 0x24): i += 2  # local/global get/set/tee
                        elif op in (0x36, 0x39): i += 3  # i32.store, f64.store (+ 2 LEB128)
                        elif op in (0x28, 0x2c): i += 3  # loads
                        elif op in (0x10,): i += 2  # call (1 byte LEB128)
                        elif op in (0x0c, 0x0d): i += 2  # br, br_if
                        elif op == 0x02: i += 2  # block
                        elif op == 0x03: i += 2  # loop
                        else: i += 1  # single byte ops (add, mul, etc.)
                    
                    if i > err_off + 5:
                        break
                
                # Print from IF to ELSE
                # Find the IF that matches err_off
                i = 0
                if_level = 0
                target_if = -1
                target_else = err_off
                match_found = False
                while i < err_off:
                    op = code[i]
                    old_i = i
                    if op == 0x04:
                        if_level += 1
                        i += 2
                    elif op == 0x05:
                        old_if_level = if_level
                        i += 1
                    elif op == 0x0b:
                        if_level -= 1
                        i += 1
                    elif op == 0x41: i += 2
                    elif op == 0x44: i += 9
                    elif op in (0x20, 0x21, 0x22, 0x23, 0x24): i += 2
                    elif op in (0x36, 0x39, 0x28, 0x2c): i += 3
                    elif op in (0x10,): i += 2
                    elif op in (0x0c, 0x0d): i += 2
                    elif op == 0x02: i += 2
                    elif op == 0x03: i += 2
                    else: i += 1
                
                # Now find all IFs at the right nesting level
                i = 0
                if_level = 0
                last_if = -1
                while i < err_off:
                    op = code[i]
                    if op == 0x04:
                        if_level += 1
                        if_levels_at_i = if_level
                        last_if = i
                        i += 2
                    elif op == 0x05:
                        i += 1
                    elif op == 0x0b:
                        if_level -= 1
                        i += 1
                    elif op == 0x41: i += 2
                    elif op == 0x44: i += 9
                    elif op in (0x20, 0x21, 0x22, 0x23, 0x24): i += 2
                    elif op in (0x36, 0x39, 0x28, 0x2c): i += 3
                    elif op in (0x10,): i += 2
                    elif op in (0x0c, 0x0d): i += 2
                    elif op == 0x02: i += 2
                    elif op == 0x03: i += 2
                    else: i += 1
                
                if last_if >= 0:
                    print(f"\nMatching IF at code_offset {last_if} for ELSE at {err_off}")
                    # Print code from 50 before IF to 30 after ELSE
                    context_start = max(0, last_if - 50)
                    context_end = min(len(code), err_off + 30)
                    ctx = code[context_start:context_end]
                    print(f"Context [{context_start}:{context_end}]:")
                    i = 0
                    while i < len(ctx):
                        ci = context_start + i
                        op = ctx[i]
                        prefix = f"[{ci}]"
                        if ci == last_if: prefix += " ==>IF"
                        elif ci == err_off: prefix += " ==>ELSE"
                        else: prefix = f" {prefix}" 
                        
                        if op == 0x04: print(f"{prefix} if {ctx[i+1]:02x}"); i += 2
                        elif op == 0x05: print(f"{prefix} else"); i += 1
                        elif op == 0x0b: print(f"{prefix} end"); i += 1
                        elif op == 0x41: print(f"{prefix} i32.const {ctx[i+1]}"); i += 2
                        elif op == 0x44:
                            import struct
                            val = struct.unpack_from('<d', ctx, i+1)[0]
                            print(f"{prefix} f64.const {val}"); i += 9
                        elif op == 0x20: print(f"{prefix} local.get {ctx[i+1]}"); i += 2
                        elif op == 0x21: print(f"{prefix} local.set {ctx[i+1]}"); i += 2
                        elif op == 0x22: print(f"{prefix} local.tee {ctx[i+1]}"); i += 2
                        elif op == 0x23: print(f"{prefix} global.get {ctx[i+1]}"); i += 2
                        elif op == 0x24: print(f"{prefix} global.set {ctx[i+1]}"); i += 2
                        elif op == 0x36: print(f"{prefix} i32.store {ctx[i+1]:02x} {ctx[i+2]:02x}"); i += 3
                        elif op == 0x39: print(f"{prefix} f64.store {ctx[i+1]:02x} {ctx[i+2]:02x}"); i += 3
                        elif op == 0x28: print(f"{prefix} i32.load {ctx[i+1]:02x} {ctx[i+2]:02x}"); i += 3
                        elif op == 0x2c: print(f"{prefix} f64.load {ctx[i+1]:02x} {ctx[i+2]:02x}"); i += 3
                        elif op == 0x46: print(f"{prefix} i32.eq"); i += 1
                        elif op == 0x47: print(f"{prefix} i32.ne"); i += 1
                        elif op == 0x4e: print(f"{prefix} i32.gt_s"); i += 1
                        elif op == 0x52: print(f"{prefix} i32.ge_s"); i += 1
                        elif op == 0x5a: print(f"{prefix} i32.and"); i += 1
                        elif op == 0x6a: print(f"{prefix} i32.add"); i += 1
                        elif op == 0xb7: print(f"{prefix} f64.convert_i32_s"); i += 1
                        elif op == 0x9f: print(f"{prefix} f64.neg"); i += 1
                        elif op == 0x05: print(f"{prefix} else (non-target)"); i += 1
                        elif op == 0x02: print(f"{prefix} block {ctx[i+1]:02x}"); i += 2
                        elif op == 0x03: print(f"{prefix} loop {ctx[i+1]:02x}"); i += 2
                        elif op == 0x0c: print(f"{prefix} br {ctx[i+1]}"); i += 2
                        elif op == 0x0d: print(f"{prefix} br_if {ctx[i+1]}"); i += 2
                        else: print(f"{prefix} op_{op:02x}"); i += 1
    pos = section_end
