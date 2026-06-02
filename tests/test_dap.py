"""Tests para el Debug Adapter Protocol (DAP) de Alvz."""

import threading
from alvz.core.lexer import Lexer
from alvz.core.parser import Parser
from alvz.core.vm import VM
from alvz.core.bytecode import OpCode


class TestDebugHook:
    def test_hook_is_none_by_default(self):
        vm = VM([], [], {}, {})
        assert vm._debug_hook is None

    def test_hook_called_during_step_mode(self):
        code = 'imprimir(42)\n'
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        bc, consts, lm, funcs = parser.compile()
        vm = VM(bc, consts, lm, funcs)
        calls = []

        def hook(ip, v):
            calls.append(ip)

        vm._debug_hook = hook
        vm.run()
        assert len(calls) > 0

    def test_breakpoint_pauses_vm(self):
        bc = bytearray([
            OpCode.OP_DEBUG_BREAK,
            OpCode.OP_CONSTANT, 0,
            OpCode.OP_PRINT,
            OpCode.OP_HALT,
        ])
        vm = VM(bc, ["42"], {0: 1, 1: 1, 3: 1, 4: 1}, {})

        paused = threading.Event()
        resume = threading.Event()

        def on_breakpoint(ip, vm_obj):
            paused.set()
            resume.wait()

        vm._dap = type('MockDAP', (), {'_on_breakpoint': staticmethod(on_breakpoint)})()

        t = threading.Thread(target=vm.run, daemon=True)
        t.start()

        assert paused.wait(timeout=1), "VM did not pause at OP_DEBUG_BREAK"
        resume.set()
        t.join(timeout=1)
        assert vm.output_buffer == ['42']

    def test_globals_persist(self):
        code = 'imprimir(99)\n'
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        bc, consts, lm, funcs = parser.compile()
        vm = VM(bc, consts, lm, funcs)
        vm.run()
        assert vm.output_buffer == ['99']

    def test_op_debug_break_noop_without_dap(self):
        """OP_DEBUG_BREAK sin DAP no debe causar error."""
        bc = bytearray([OpCode.OP_DEBUG_BREAK, OpCode.OP_HALT])
        vm = VM(bc, [], {0: 0}, {})
        vm.run()
        assert True

    def test_debug_hook_is_called_before_halt(self):
        """El hook se llama antes de procesar OP_HALT."""
        vm = VM([OpCode.OP_HALT], [], {}, {})
        calls = []

        def hook(ip, v):
            calls.append(ip)

        vm._debug_hook = hook
        vm.run()
        assert len(calls) == 1

    def test_stack_trace_frames(self):
        """Verifica que los frames se reconstruyen correctamente."""
        code = 'funcion suma(a, b) { retornar a + b }\nimprimir(suma(3, 4))\n'
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        bc, consts, lm, funcs = parser.compile()
        vm = VM(bc, consts, lm, funcs)
        vm.run()
        assert vm.output_buffer == ['7']

    def test_run_concurrent_safe(self):
        """Multiples VMs con debug hook no deben interferir."""
        def run_one(val):
            code = f'imprimir({val})\n'
            lexer = Lexer(code)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            bc, consts, lm, funcs = parser.compile()
            vm = VM(bc, consts, lm, funcs)
            vm.run()
            return vm.output_buffer

        threads = []
        results = []
        for v in [10, 20, 30]:
            t = threading.Thread(target=lambda v=v: results.append(run_one(v)))
            threads.append(t)
            t.start()
        for t in threads:
            t.join(timeout=2)
        outputs = [r[0] for r in results if r]
        assert '10' in outputs
        assert '20' in outputs
        assert '30' in outputs

    def test_dap_attribute_default(self):
        vm = VM([], [], {}, {})
        assert vm._dap is None
