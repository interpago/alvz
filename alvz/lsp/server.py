"""
LSP Server for Alvz Language.

Implements the Language Server Protocol over stdin/stdout
using JSON-RPC, providing diagnostics, completions,
go-to-definition, hover info, and document symbols.
"""

import sys
import traceback

from .protocol import (
    JSONRPC, read_message,
)
from .analyzer import Analyzer


class AlvzLanguageServer:
    def __init__(self):
        self.rpc = JSONRPC()
        self.analyzer = Analyzer()
        self.capabilities = {}
        self._initialized = False

    def run(self):
        while True:
            try:
                msg = read_message()
                if msg is None:
                    break
                self._handle(msg)
            except EOFError:
                break
            except Exception:
                traceback.print_exc(file=sys.stderr)

    def _handle(self, msg):
        method = msg.get('method')
        msg_id = msg.get('id')
        params = msg.get('params', {})

        handlers = {
            'initialize': self._on_initialize,
            'initialized': self._on_initialized,
            'shutdown': self._on_shutdown,
            'textDocument/didOpen': self._on_did_open,
            'textDocument/didChange': self._on_did_change,
            'textDocument/didClose': self._on_did_close,
            'textDocument/completion': self._on_completion,
            'textDocument/definition': self._on_definition,
            'textDocument/hover': self._on_hover,
            'textDocument/documentSymbol': self._on_document_symbol,
        }

        handler = handlers.get(method)
        if handler:
            result = handler(params)
            if msg_id is not None:
                self.rpc.reply(msg_id, result)
        elif msg_id is not None:
            self.rpc.reply(msg_id, None)

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def _on_initialize(self, params):
        self.capabilities = {
            'textDocumentSync': {
                'openClose': True,
                'change': 1,  # Full sync
            },
            'completionProvider': {
                'resolveProvider': False,
                'triggerCharacters': ['.', '"'],
            },
            'definitionProvider': True,
            'hoverProvider': True,
            'documentSymbolProvider': True,
        }
        return {
            'capabilities': self.capabilities,
            'serverInfo': {
                'name': 'alvz-lsp',
                'version': '0.1.0',
            },
        }

    def _on_initialized(self, params):
        self._initialized = True

    def _on_shutdown(self, params):
        sys.exit(0)

    # ── Text document events ───────────────────────────────────────────────

    def _on_did_open(self, params):
        doc = params.get('textDocument', {})
        uri = doc.get('uri', '')
        text = doc.get('text', '')
        errors = self.analyzer.open_file(uri, text)
        self._publish_diagnostics(uri, errors)

    def _on_did_change(self, params):
        doc = params.get('textDocument', {})
        uri = doc.get('uri', '')
        changes = params.get('contentChanges', [])
        if changes:
            text = changes[-1].get('text', '')
            errors = self.analyzer.update_file(uri, text)
            self._publish_diagnostics(uri, errors)

    def _on_did_close(self, params):
        doc = params.get('textDocument', {})
        uri = doc.get('uri', '')
        self.analyzer.close_file(uri)

    # ── Features ───────────────────────────────────────────────────────────

    def _on_completion(self, params):
        doc = params.get('textDocument', {})
        uri = doc.get('uri', '')
        pos = params.get('position', {})
        line = pos.get('line', 0)
        col = pos.get('character', 0)
        items = self.analyzer.get_completions(uri, line, col)
        return {'isIncomplete': False, 'items': items}

    def _on_definition(self, params):
        doc = params.get('textDocument', {})
        uri = doc.get('uri', '')
        pos = params.get('position', {})
        line = pos.get('line', 0)
        col = pos.get('character', 0)
        result = self.analyzer.find_definition(uri, line, col)
        return result

    def _on_hover(self, params):
        doc = params.get('textDocument', {})
        uri = doc.get('uri', '')
        pos = params.get('position', {})
        line = pos.get('line', 0)
        col = pos.get('character', 0)
        result = self.analyzer.get_hover(uri, line, col)
        return result

    def _on_document_symbol(self, params):
        doc = params.get('textDocument', {})
        uri = doc.get('uri', '')
        return self.analyzer.get_symbols(uri)

    # ── Diagnostics ────────────────────────────────────────────────────────

    def _publish_diagnostics(self, uri, errors):
        diagnostics = []
        for err in errors:
            line = max(0, err['line'] - 1)
            col = err.get('col', 0)
            diagnostics.append({
                'range': {
                    'start': {'line': line, 'character': col},
                    'end': {'line': line, 'character': col + 1},
                },
                'message': err['message'],
                'severity': err.get('severity', 1),
            })
        self.rpc.notify('textDocument/publishDiagnostics', {
            'uri': uri,
            'diagnostics': diagnostics,
        })


def main():
    server = AlvzLanguageServer()
    server.run()


if __name__ == '__main__':
    main()
