const vscode = require('vscode');

const KEYWORDS = [
    'variable', 'funcion', 'clase', 'nuevo', 'estatico',
    'si', 'sino', 'mientras', 'para', 'cada', 'retornar',
    'intentar', 'capturar', 'lanzar', 'importar',
    'aguardar', 'async', 'global', 'romper', 'continuar',
    'propiedad', 'obtener', 'establecer', 'de', 'a', 'en', 'y', 'o',
];

const CONSTANTS = ['verdadero', 'falso', 'nulo'];

const STDLIB_FUNCS = [
    { name: 'imprimir', args: '...valores', desc: 'Imprime en consola' },
    { name: 'leer', args: '', desc: 'Lee entrada del usuario' },
    { name: 'leer_numero', args: '', desc: 'Lee un número del usuario' },
    { name: 'azar', args: 'min, max', desc: 'Número aleatorio' },
    { name: 'limpiar', args: '', desc: 'Limpia la consola' },
    { name: 'longitud', args: 'objeto', desc: 'Longitud de string/lista/dict' },
    { name: 'agregar', args: 'lista, elemento', desc: 'Agrega a una lista' },
    { name: 'esperar', args: 'ms', desc: 'Espera milisegundos' },
    { name: 'enviar_web', args: 'url, datos', desc: 'Envía petición HTTP' },
    { name: 'leer_archivo', args: 'ruta', desc: 'Lee un archivo' },
    { name: 'escribir_archivo', args: 'ruta, contenido', desc: 'Escribe un archivo' },
    { name: 'json_codificar', args: 'valor', desc: 'Codifica a JSON' },
    { name: 'json_decodificar', args: 'texto', desc: 'Decodifica JSON' },
    { name: 'supabase_insertar', args: 'tabla, datos', desc: 'Inserta en Supabase' },
    { name: 'supabase_consultar', args: 'tabla, columna, valor', desc: 'Consulta Supabase' },
    { name: 'mayusculas', args: 'texto', desc: 'Convierte a mayúsculas' },
    { name: 'minusculas', args: 'texto', desc: 'Convierte a minúsculas' },
    { name: 'reemplazar', args: 'texto, buscar, reemplazo', desc: 'Reemplaza texto' },
    { name: 'absoluto', args: 'n', desc: 'Valor absoluto' },
    { name: 'redondear', args: 'n, decimales', desc: 'Redondea un número' },
    { name: 'potencia', args: 'base, exp', desc: 'Eleva a potencia' },
    { name: 'raiz', args: 'n', desc: 'Raíz cuadrada' },
    { name: 'tipo', args: 'valor', desc: 'Tipo de dato' },
    { name: 'error_msj', args: '', desc: 'Último mensaje de error' },
    { name: 'iniciar_servidor', args: 'puerto, rutas', desc: 'Inicia servidor HTTP' },
    { name: 'tiempo', args: '', desc: 'Timestamp actual' },
    { name: 'obtener_salida', args: '', desc: 'Obtiene salida acumulada' },
];

let AlvzSemanticTokensProvider = (function () {
    function AlvzSemanticTokensProvider() {}
    AlvzSemanticTokensProvider.prototype.getLegend = function () {
        return new vscode.SemanticTokensLegend(
            ['variable', 'function', 'class', 'keyword', 'string', 'number',
             'builtinFunction', 'property', 'comment', 'parameter', 'type'],
            ['declaration', 'definition', 'readonly', 'defaultLibrary']
        );
    };
    AlvzSemanticTokensProvider.prototype.provideDocumentSemanticTokens = function (doc) {
        const builder = new vscode.SemanticTokensBuilder(this.getLegend());
        const text = doc.getText();
        const lines = text.split('\n');
        const tokenRegex = /('(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*"|#[^\n]*|\b[a-zA-Z_]\w*\b|\d+(?:\.\d+)?)/g;
        const funcDeclRegex = /^\s*funcion\s+(?:(?:async|estatico)\s+)?([a-zA-Z_]\w*)/;
        const classDeclRegex = /^\s*clase\s+([a-zA-Z_]\w*)/;
        const varDeclRegex = /^\s*variable\s+([a-zA-Z_]\w*)/;
        const paramRegex = /funcion\s+(?:(?:async|estatico)\s+)?[a-zA-Z_]\w*\s*\(([^)]*)\)/;
        const forParamRegex = /para\s+(?:cada\s+)?([a-zA-Z_]\w*)/;
        const obtenerRegex = /^\s*propiedad\s+([a-zA-Z_]\w*)\s*\{/;
        const globalRegex = /^\s*global\s+([a-zA-Z_]\w*(?:\s*,\s*[a-zA-Z_]\w*)*)/;

        for (let lineIdx = 0; lineIdx < lines.length; lineIdx++) {
            const line = lines[lineIdx];
            const trimmed = line.trim();

            if (/^\s*#/.test(line)) continue;

            let m;
            if ((m = funcDeclRegex.exec(trimmed))) {
                const col = line.indexOf(m[1]);
                builder.push(lineIdx, col, m[1].length, 1, 1);
                continue;
            }
            if ((m = classDeclRegex.exec(trimmed))) {
                const col = line.indexOf(m[1]);
                builder.push(lineIdx, col, m[1].length, 2, 1);
                continue;
            }
            if ((m = varDeclRegex.exec(trimmed))) {
                const col = line.indexOf(m[1]);
                builder.push(lineIdx, col, m[1].length, 0, 1);
                continue;
            }
            if ((m = obtenerRegex.exec(trimmed))) {
                const col = line.indexOf(m[1]);
                builder.push(lineIdx, col, m[1].length, 7, 0);
                continue;
            }
            if ((m = globalRegex.exec(trimmed))) {
                const names = m[1].split(',').map(s => s.trim());
                for (const name of names) {
                    const col = line.indexOf(name);
                    if (col >= 0) builder.push(lineIdx, col, name.length, 0, 1);
                }
                continue;
            }
        }

        for (let lineIdx = 0; lineIdx < lines.length; lineIdx++) {
            const line = lines[lineIdx];
            let match;
            while ((match = tokenRegex.exec(line)) !== null) {
                const token = match[1];
                const col = match.index;
                const len = token.length;

                if (token.startsWith('#') || token.startsWith('"') || token.startsWith("'")) {
                    if (token.startsWith('#')) {
                        builder.push(lineIdx, col, len, 8, 0);
                    } else {
                        builder.push(lineIdx, col, len, 4, 0);
                    }
                    continue;
                }

                if (/^\d/.test(token)) {
                    builder.push(lineIdx, col, len, 5, 0);
                    continue;
                }

                if (CONSTANTS.includes(token)) {
                    builder.push(lineIdx, col, len, 3, 0);
                    continue;
                }

                if (KEYWORDS.includes(token)) {
                    builder.push(lineIdx, col, len, 3, 0);
                    continue;
                }

                const isBuiltin = STDLIB_FUNCS.some(f => f.name === token);
                if (isBuiltin) {
                    builder.push(lineIdx, col, len, 6, 3);
                    continue;
                }

                const nextChar = line[col + len];
                if (nextChar === '(') {
                    builder.push(lineIdx, col, len, 1, 0);
                }
            }
        }

        return builder.build();
    };
    return AlvzSemanticTokensProvider;
})();

let AlvzCompletionProvider = (function () {
    function AlvzCompletionProvider() {}
    AlvzCompletionProvider.prototype.provideCompletionItems = function (doc, position) {
        const items = [];
        const linePrefix = doc.lineAt(position).text.substring(0, position.character);
        const wordMatch = /[a-zA-Z_]\w*$/.exec(linePrefix);
        const partial = wordMatch ? wordMatch[0].toLowerCase() : '';

        const snippets = {
            'funcion': { label: 'funcion nombre(args) { … }', detail: 'Definir función', insert: 'funcion ${1:nombre}(${2:args}) {\n\t$0\n}' },
            'si': { label: 'si (condición) { … }', detail: 'Condicional si', insert: 'si ${1:condicion} {\n\t$0\n}' },
            'sino': { label: 'si (cond) { … } sino { … }', detail: 'Condicional si-sino', insert: 'si ${1:condicion} {\n\t$0\n} sino {\n\t\n}' },
            'mientras': { label: 'mientras (cond) { … }', detail: 'Bucle mientras', insert: 'mientras ${1:condicion} {\n\t$0\n}' },
            'para': { label: 'para i de 1 a n { … }', detail: 'Bucle para rango', insert: 'para ${1:i} de ${2:1} a ${3:n} {\n\t$0\n}' },
            'cada': { label: 'cada x en lista { … }', detail: 'Bucle cada elemento', insert: 'cada ${1:elemento} en ${2:lista} {\n\t$0\n}' },
            'clase': { label: 'clase Nombre { … }', detail: 'Definir clase', insert: 'clase ${1:Nombre} {\n\tfuncion inicializar(${2:args}) {\n\t\t$0\n\t}\n}' },
            'importar': { label: 'importar "módulo"', detail: 'Importar módulo', insert: 'importar "${1:modulo}"' },
            'intentar': { label: 'intentar { … } capturar e { … }', detail: 'Manejo de errores', insert: 'intentar {\n\t$0\n} capturar ${1:e} {\n\t\n}' },
            'async': { label: 'funcion async nombre() { … }', detail: 'Función asíncrona', insert: 'funcion async ${1:nombre}(${2:args}) {\n\t$0\n}' },
            'global': { label: 'global x, y', detail: 'Declarar variable global', insert: 'global ${1:x}, ${2:y}' },
            'propiedad': { label: 'propiedad nombre { obtener { } … }', detail: 'Propiedad getter/setter', insert: 'propiedad ${1:nombre} {\n\tobtener {\n\t\tretornar ${2:valor}\n\t}\n\testablecer(${3:valor}) {\n\t\t$4\n\t}\n}' },
        };

        for (const kw of KEYWORDS) {
            if (partial && !kw.startsWith(partial)) continue;
            if (snippets[kw]) continue;
            const item = new vscode.CompletionItem(kw, vscode.CompletionItemKind.Keyword);
            items.push(item);
        }

        for (const [prefix, snip] of Object.entries(snippets)) {
            if (partial && !prefix.startsWith(partial)) continue;
            const item = new vscode.CompletionItem(snip.label, vscode.CompletionItemKind.Snippet);
            item.insertText = new vscode.SnippetString(snip.insert);
            item.detail = snip.detail;
            items.push(item);
        }

        for (const fn of STDLIB_FUNCS) {
            if (partial && !fn.name.startsWith(partial)) continue;
            const item = new vscode.CompletionItem(fn.name, vscode.CompletionItemKind.Function);
            item.detail = `${fn.name}(${fn.args}) — ${fn.desc}`;
            item.insertText = fn.args ? new vscode.SnippetString(`${fn.name}(\${1:${fn.args}})\$0`) : `${fn.name}()`;
            items.push(item);
        }

        for (const c of CONSTANTS) {
            if (partial && !c.startsWith(partial)) continue;
            const item = new vscode.CompletionItem(c, vscode.CompletionItemKind.Constant);
            items.push(item);
        }

        if (linePrefix.includes('importar "') && linePrefix.split('"').length % 2 === 0) {
            const stdlibMods = ['matematicas', 'http', 'fecha', 'testing', 'sistema', 'sqlite'];
            for (const mod of stdlibMods) {
                if (partial && !mod.startsWith(partial)) continue;
                const item = new vscode.CompletionItem(`"${mod}"`, vscode.CompletionItemKind.Module);
                item.insertText = mod;
                items.push(item);
            }
        }

        return items;
    };
    return AlvzCompletionProvider;
})();

function activate(context) {
    const semantic = new AlvzSemanticTokensProvider();
    context.subscriptions.push(
        vscode.languages.registerDocumentSemanticTokensProvider(
            { language: 'alvz', scheme: 'file' },
            semantic,
            semantic.getLegend()
        )
    );

    const completions = new AlvzCompletionProvider();
    context.subscriptions.push(
        vscode.languages.registerCompletionItemProvider(
            { language: 'alvz', scheme: 'file' },
            completions,
            '.', '"', ' '
        )
    );

    // Activar iconos de Alvz si el usuario no tiene un theme personalizado
    const config = vscode.workspace.getConfiguration('workbench');
    const currentIconTheme = config.get('iconTheme');
    if (!currentIconTheme || currentIconTheme === 'vs-seti') {
        config.update('iconTheme', 'alvz-icons', vscode.ConfigurationTarget.Global);
    }
}

function deactivate() {}

module.exports = { activate, deactivate };
