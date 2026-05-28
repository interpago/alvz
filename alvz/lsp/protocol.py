import json
import sys
import traceback


# ── LSP types ──────────────────────────────────────────────────────────────

class Position:
    def __init__(self, line=0, character=0):
        self.line = line
        self.character = character

    def to_dict(self):
        return {'line': self.line, 'character': self.character}

    @staticmethod
    def from_dict(d):
        return Position(d['line'], d['character'])


class Range:
    def __init__(self, start=None, end=None):
        self.start = start or Position()
        self.end = end or Position()

    def to_dict(self):
        return {'start': self.start.to_dict(), 'end': self.end.to_dict()}

    @staticmethod
    def from_dict(d):
        return Range(Position.from_dict(d['start']), Position.from_dict(d['end']))


class Location:
    def __init__(self, uri='', range_=None):
        self.uri = uri
        self.range = range_ or Range()

    def to_dict(self):
        return {'uri': self.uri, 'range': self.range.to_dict()}


class CompletionItem:
    def __init__(self, label='', kind=14, detail='', documentation=''):
        self.label = label
        self.kind = kind
        self.detail = detail
        self.documentation = documentation

    def to_dict(self):
        d = {'label': self.label, 'kind': self.kind}
        if self.detail:
            d['detail'] = self.detail
        if self.documentation:
            d['documentation'] = self.documentation
        return d


class Diagnostic:
    SEVERITY_ERROR = 1
    SEVERITY_WARNING = 2
    SEVERITY_INFO = 3

    def __init__(self, range_=None, message='', severity=1):
        self.range = range_ or Range()
        self.message = message
        self.severity = severity

    def to_dict(self):
        return {
            'range': self.range.to_dict(),
            'message': self.message,
            'severity': self.severity,
        }


class SymbolKind:
    FILE = 1
    MODULE = 2
    NAMESPACE = 3
    PACKAGE = 4
    CLASS = 5
    METHOD = 6
    PROPERTY = 7
    FIELD = 8
    CONSTRUCTOR = 9
    ENUM = 10
    INTERFACE = 11
    FUNCTION = 12
    VARIABLE = 13
    CONSTANT = 14
    STRING = 15
    NUMBER = 16
    BOOLEAN = 17
    ARRAY = 18
    KEY = 21
    NULL = 22
    STRUCT_MEMBER = 23


# ── JSON-RPC handling ──────────────────────────────────────────────────────

class JSONRPC:
    _next_id = 1

    def __init__(self, send_fn=None):
        self._pending = {}
        self.send_fn = send_fn or self._default_send

    def _default_send(self, msg):
        data = json.dumps(msg, ensure_ascii=False)
        header = f'Content-Length: {len(data)}\r\n\r\n'
        sys.stdout.buffer.write(header.encode())
        sys.stdout.buffer.write(data.encode())
        sys.stdout.buffer.flush()

    def notify(self, method, params=None):
        msg = {'jsonrpc': '2.0', 'method': method}
        if params is not None:
            msg['params'] = params
        self.send_fn(msg)

    def request(self, method, params=None):
        msg_id = self._next_id
        self._next_id += 1
        msg = {'jsonrpc': '2.0', 'id': msg_id, 'method': method}
        if params is not None:
            msg['params'] = params
        self.send_fn(msg)
        return msg_id

    def reply(self, msg_id, result):
        self.send_fn({'jsonrpc': '2.0', 'id': msg_id, 'result': result})

    def error(self, msg_id, code, message):
        self.send_fn({'jsonrpc': '2.0', 'id': msg_id, 'error': {'code': code, 'message': message}})


def read_message():
    content_length = 0
    headers = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line or line == b'\r\n':
            break
        line = line.decode().strip()
        if ': ' in line:
            key, value = line.split(': ', 1)
            headers[key] = value
    content_length = int(headers.get('Content-Length', 0))
    if content_length == 0:
        return None
    body = sys.stdin.buffer.read(content_length)
    return json.loads(body.decode())
