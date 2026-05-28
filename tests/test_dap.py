import pytest
from alvz.core.lexer import Lexer
from alvz.core.parser import Parser
from alvz.core.vm import VM


class TestDebugHook:
    def test_hook_is_none_by_default(self):
        vm = VM([], [], {}, {})
        assert not hasattr(vm, '_debug_hook') or vm._debug_hook is None

    def test_hook_called_during_run(self):
        code = 'imprimir(1)\n'
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
        code = 'imprimir(42)\n'
        lexer = Lexer(code)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        bc, consts, lm, funcs = parser.compile()
        vm = VM(bc, consts, lm, funcs)

        import threading
        paused = threading.Event()
        resume = threading.Event()

        def hook(ip, v):
            paused.set()
            resume.wait()

        vm._debug_hook = hook
        t = threading.Thread(target=vm.run, daemon=True)
        t.start()

        assert paused.wait(timeout=1), "VM did not pause at first instruction"
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
