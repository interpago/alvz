"""
Debug Adapter Protocol (DAP) for Alvz Language.
"""

import json
import sys
import threading
import traceback

from alvz.core.lexer import Lexer
from alvz.core.parser import Parser
from alvz.core.vm import VM


def _write(msg):
    data = json.dumps(msg, ensure_ascii=False)
    header = f'Content-Length: {len(data)}\r\n\r\n'
    sys.stdout.buffer.write(header.encode())
    sys.stdout.buffer.write(data.encode())
    sys.stdout.buffer.flush()


def _read():
    content_length = 0
    while True:
        line = sys.stdin.buffer.readline()
        if not line or line == b'\r\n':
            break
        line = line.decode().strip()
        if ': ' in line:
            key, value = line.split(': ', 1)
            content_length = int(value)
    if content_length == 0:
        return None
    body = sys.stdin.buffer.read(content_length)
    return json.loads(body.decode())


class DAPServer:
    def __init__(self):
        self._breakpoints = {}
        self._resume = threading.Event()
        self._stopped = False
        self._step_mode = 'continue'
        self._target_frames = 0
        self._current_ip = -1
        self._vm = None
        self._frames_snap = []
        self._stack_snap = []
        self._waiting = False

    def _debug_hook(self, ip, vm):
        self._vm = vm
        self._current_ip = ip
        line = vm.line_map.get(ip, -1)

        if self._should_stop(line, vm):
            self._on_stop(vm)

    def _should_stop(self, line, vm):
        if self._step_mode == 'step_in':
            return True
        if self._step_mode == 'step_over':
            if len(vm.frames) <= self._target_frames:
                return True
        if self._step_mode == 'step_out':
            if len(vm.frames) < self._target_frames:
                return True
        if self._step_mode == 'continue':
            for uri, lines in self._breakpoints.items():
                if line > 0 and line in lines:
                    return True
        return False

    def _on_stop(self, vm):
        self._stopped = True
        self._frames_snap = [dict(f) for f in vm.frames]
        self._stack_snap = list(vm.stack)
        reason = self._step_mode if self._step_mode != 'continue' else 'breakpoint'
        self._send_event('stopped', {
            'reason': reason,
            'threadId': 1,
            'allThreadsStopped': True,
        })
        self._resume.clear()
        self._waiting = True
        self._resume.wait()
        self._waiting = False
        if self._step_mode != 'continue':
            self._step_mode = 'continue'

    def _send_event(self, event, body=None):
        msg = {'type': 'event', 'event': event}
        if body:
            msg['body'] = body
        _write(msg)

    def _reply(self, req, body=None, success=True):
        _write({
            'type': 'response',
            'request_seq': req.get('seq', 0),
            'success': success,
            'command': req.get('command', ''),
            'body': body or {},
        })

    def _handle_initialize(self, req):
        self._reply(req, {
            'supportsConfigurationDoneRequest': True,
            'supportsEvaluateForHovers': True,
        })

    def _handle_launch(self, req):
        args = req.get('arguments', {})
        program = args.get('program', '')
        try:
            with open(program, 'r', encoding='utf-8-sig') as f:
                code = f.read()
            lexer = Lexer(code)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            bc, consts, lm, funcs = parser.compile()
            self._vm = VM(bc, consts, lm, funcs)
            self._vm._debug_hook = self._debug_hook
            self._reply(req)
            self._send_event('initialized')
        except Exception as e:
            self._reply(req, {'error': {'message': str(e)}}, success=False)

    def _handle_configuration_done(self, req):
        self._reply(req)
        threading.Thread(target=self._run_vm, daemon=True).start()

    def _handle_set_breakpoints(self, req):
        args = req.get('arguments', {})
        source = args.get('source', {})
        path = source.get('path', '')
        bps = args.get('breakpoints', [])
        lines = [b.get('line', 0) for b in bps]
        self._breakpoints[path] = lines
        self._reply(req, {
            'breakpoints': [{'verified': True, 'line': line_num, 'source': source} for line_num in lines]
        })

    def _handle_continue(self, req):
        self._step_mode = 'continue'
        self._resume.set()
        self._reply(req, {'allThreadsContinued': True})

    def _handle_next(self, req):
        self._step_mode = 'step_over'
        self._target_frames = len(self._vm.frames) if self._vm else 0
        self._resume.set()
        self._reply(req)

    def _handle_step_in(self, req):
        self._step_mode = 'step_in'
        self._resume.set()
        self._reply(req)

    def _handle_step_out(self, req):
        self._step_mode = 'step_out'
        self._target_frames = len(self._vm.frames) if self._vm else 0
        self._resume.set()
        self._reply(req)

    def _handle_stack_trace(self, req):
        frames = []
        for i, f in enumerate(self._frames_snap):
            name = f.get('func_name', '<modulo>')
            line = 1
            if self._vm:
                for ip_addr, ln in self._vm.line_map.items():
                    if ip_addr <= self._current_ip:
                        line = ln
            frames.append({
                'id': i,
                'name': name,
                'line': max(1, line),
                'column': 1,
            })
        self._reply(req, {'stackFrames': frames, 'totalFrames': len(frames)})

    def _handle_scopes(self, req):
        args = req.get('arguments', {})
        fid = args.get('frameId', 0)
        scopes = []
        if 0 <= fid < len(self._frames_snap):
            scopes.append({'name': 'Locales', 'variablesReference': fid + 1000, 'expensive': False})
        scopes.append({'name': 'Globales', 'variablesReference': 1, 'expensive': False})
        self._reply(req, {'scopes': scopes})

    def _handle_variables(self, req):
        args = req.get('arguments', {})
        ref = args.get('variablesReference', 0)
        vars_list = []
        if ref == 1:
            for k, v in (self._vm.globals.items() if self._vm else []):
                vars_list.append({'name': str(k), 'value': str(v), 'type': type(v).__name__, 'variablesReference': 0})
        elif ref >= 1000:
            fidx = ref - 1000
            if 0 <= fidx < len(self._frames_snap):
                for k, v in self._frames_snap[fidx].get('locals', {}).items():
                    vars_list.append({'name': f'[{k}]', 'value': str(v), 'type': type(v).__name__, 'variablesReference': 0})
        self._reply(req, {'variables': vars_list})

    def _handle_threads(self, req):
        self._reply(req, {'threads': [{'id': 1, 'name': 'Hilo principal'}]})

    def _handle_evaluate(self, req):
        expr = req.get('arguments', {}).get('expression', '')
        try:
            lexer = Lexer(expr)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            bc, consts, lm, funcs = parser.compile()
            evm = VM(bc, consts, lm, funcs)
            evm.stack = list(self._vm.stack) if self._vm else []
            evm.globals = self._vm.globals if self._vm else {}
            evm.frames = [dict(f) for f in (self._vm.frames if self._vm else [])]
            evm.run()
            result = evm.stack.pop() if evm.stack else ''
            self._reply(req, {'result': str(result), 'type': type(result).__name__})
        except Exception as e:
            self._reply(req, {'result': str(e), 'type': 'error'})

    def _handle_disconnect(self, req):
        self._resume.set()
        self._reply(req)

    def _run_vm(self):
        try:
            self._vm.run()
        except Exception as e:
            self._send_event('output', {'output': f'Error: {e}\n', 'category': 'stderr'})
        finally:
            self._send_event('terminated')

    def run(self):
        handlers = {
            'initialize': self._handle_initialize,
            'launch': self._handle_launch,
            'configurationDone': self._handle_configuration_done,
            'setBreakpoints': self._handle_set_breakpoints,
            'continue': self._handle_continue,
            'next': self._handle_next,
            'stepIn': self._handle_step_in,
            'stepOut': self._handle_step_out,
            'stackTrace': self._handle_stack_trace,
            'scopes': self._handle_scopes,
            'variables': self._handle_variables,
            'threads': self._handle_threads,
            'evaluate': self._handle_evaluate,
            'disconnect': self._handle_disconnect,
        }
        while True:
            try:
                msg = _read()
                if msg is None:
                    break
                if msg.get('type') == 'request':
                    handler = handlers.get(msg.get('command'))
                    if handler:
                        handler(msg)
            except EOFError:
                break
            except Exception:
                traceback.print_exc(file=sys.stderr)


def main():
    DAPServer().run()


if __name__ == '__main__':
    main()
