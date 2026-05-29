import sys
sys.path.insert(0, '.')
from alvz.core.wasm_encoder import WasmModule
import wasmtime

# Create a minimal WASM module with 10 locals that uses $10
m = WasmModule()
t_main = m.add_type([], [])
m.add_function(t_main)
m.add_memory(1)
m.add_export('main', 'func', 0)

# 10 locals: 0-9. Code: try to use local 10
locals_decl = [(1, 'i32')] * 10  # 10 i32 locals, each count=1
code = bytearray([0x41, 0x2a, 0x21, 0x0a, 0x0b])  # i32.const 42, local.set 10, end

m.add_code(locals_decl, bytes(code))
wasm = m.to_bytes()

try:
    module = wasmtime.Module(wasmtime.Engine(), wasm)
    print("Module validated OK!")
except Exception as e:
    print(f"Error: {e}")
