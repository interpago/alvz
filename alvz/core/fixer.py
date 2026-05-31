import sys
import re
from .lexer import Lexer, Token


def _sugerir_import(comando):
    sugerencias = {
        'imprimir': 'builtin',
        'leer': 'builtin',
        'azar': 'builtin',
        'longitud': 'builtin',
        'json_codificar': 'builtin',
        'factorial': '"matematicas"',
        'maximo': '"matematicas"',
        'minimo': '"matematicas"',
        'promedio': '"matematicas"',
        'reversa': '"cadenas"',
        'capitalizar': '"cadenas"',
        'contiene': '"cadenas"',
        'vacio': '"colecciones"',
        'http_obtener': '"http"',
        'ahora': '"fecha"',
        'archivo_leer': '"sistema"',
        'base_abrir': '"sqlite"',
    }
    return sugerencias.get(comando)


def analizar_y_sugerir(archivo):
    with open(archivo, 'r', encoding='utf-8') as f:
        codigo = f.read()

    sugerencias = []
    lineas = codigo.split('\n')

    # Detectar imports existentes
    imports = set()
    patron_import = re.compile(r'^\s*importar\s+"([^"]+)"')
    for linea in lineas:
        m = patron_import.match(linea)
        if m:
            imports.add(m.group(1))

    # Detectar funciones usadas sin import
    llamadas = re.findall(r'\b([a-zA-Z_]\w*)\s*\(', codigo)
    keywords = {'si', 'sino', 'mientras', 'para', 'cada', 'funcion',
                'variable', 'clase', 'nuevo', 'retornar', 'importar',
                'intentar', 'capturar', 'lanzar', 'y', 'o', 'en', 'de', 'a',
                'async', 'aguardar', 'global', 'romper', 'continuar', 'estatico',
                'propiedad', 'obtener', 'establecer', 'super', 'instancia'}
    builtins = {'imprimir', 'leer', 'leer_numero', 'azar', 'limpiar',
                'longitud', 'agregar', 'tiempo', 'tipo', 'json_codificar',
                'json_decodificar', 'reemplazar', 'absoluto', 'redondear',
                'potencia', 'raiz', 'mayusculas', 'minusculas', 'enviar_web',
                'esperar', 'dividir', 'unir', 'a_numero', 'regex_buscar',
                'error_msj', 'obtener_salida', 'iniciar_servidor',
                'fecha_actual', 'leer_archivo', 'escribir_archivo',
                'solicitud_http', 'sqlite_abrir', 'sqlite_ejecutar',
                'sqlite_consultar'}

    for func in llamadas:
        if func in keywords or func in builtins:
            continue
        mod = _sugerir_import(func)
        if mod and mod not in imports:
            sugerencias.append({
                'tipo': 'import_faltante',
                'funcion': func,
                'modulo': mod,
                'mensaje': f"La funcion '{func}' requiere importar {mod}"
            })

    # Detectar variables no usadas
    vars_declaradas = set()
    vars_usadas = set()
    patron_var = re.compile(r'\bvariable\s+([a-zA-Z_]\w*)')
    patron_uso = re.compile(r'\b([a-zA-Z_]\w*)\b')
    for i, linea in enumerate(lineas):
        m = patron_var.search(linea)
        if m:
            vars_declaradas.add(m.group(1))
        for u in patron_uso.findall(linea):
            if u not in keywords:
                vars_usadas.add(u)
    no_usadas = vars_declaradas - vars_usadas
    for v in no_usadas:
        sugerencias.append({
            'tipo': 'variable_no_usada',
            'variable': v,
            'mensaje': f"Variable '{v}' declarada pero no usada"
        })

    # Detectar global duplicado
    globales_vistos = set()
    patron_global = re.compile(r'^\s*global\s+(.+)')
    for i, linea in enumerate(lineas):
        m = patron_global.match(linea)
        if m:
            vars_linea = [v.strip() for v in m.group(1).split(',')]
            for v in vars_linea:
                if v in globales_vistos:
                    sugerencias.append({
                        'tipo': 'global_duplicado',
                        'variable': v,
                        'linea': i + 1,
                        'mensaje': f"Variable global '{v}' declarada multiples veces"
                    })
                globales_vistos.add(v)

    return sugerencias


def aplicar_sugerencia(archivo, sugerencia, dry_run=True):
    if sugerencia['tipo'] == 'import_faltante':
        with open(archivo, 'r', encoding='utf-8') as f:
            codigo = f.read()
        nueva_linea = f'importar {sugerencia["modulo"]}\n'
        codigo_nuevo = nueva_linea + codigo
        if dry_run:
            print(f"  [S] Agregar: {nueva_linea.strip()}")
        else:
            with open(archivo, 'w', encoding='utf-8') as f:
                f.write(codigo_nuevo)
            print(f"  [F] {sugerencia['mensaje']}")
        return True

    if sugerencia['tipo'] == 'variable_no_usada':
        if dry_run:
            print(f"  [S] Eliminar variable '{sugerencia['variable']}' (no usada)")
        return True

    if sugerencia['tipo'] == 'global_duplicado':
        if dry_run:
            print(f"  [S] Linea {sugerencia['linea']}: eliminar global duplicado '{sugerencia['variable']}'")
        return True

    return False


def fix_file(archivo, dry_run=True):
    print(f"\nAnalizando: {archivo}")
    sugerencias = analizar_y_sugerir(archivo)
    if not sugerencias:
        print("  No se encontraron problemas.")
        return True

    print(f"  {len(sugerencias)} sugerencia(s):")
    for s in sugerencias:
        aplicar_sugerencia(archivo, s, dry_run)

    if dry_run and sugerencias:
        print(f"\n  Usa 'alvz fix {archivo}' sin --dry-run para aplicar los cambios.")

    return len(sugerencias) == 0


def main():
    archivos = sys.argv[1:] if len(sys.argv) > 1 else []
    dry_run = '--dry-run' in archivos
    if '--dry-run' in archivos:
        archivos.remove('--dry-run')

    if not archivos:
        print("Uso: alvz fix <archivo> [--dry-run]")
        return

    for archivo in archivos:
        fix_file(archivo, dry_run)


if __name__ == '__main__':
    main()
