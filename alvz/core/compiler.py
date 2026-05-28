"""
Compilador: empaqueta bytecode Alvz en un ejecutable standalone via PyInstaller.

Uso:
    alvz build archivo.alvz [-o salida]
"""

import os
import sys
import tempfile
import shutil
import platform

from .bytecode import OpCode
from .lexer import Lexer
from .parser import Parser

# Map opcode enum values to human-readable names for the embedded comment
_OP_NAMES = {v: k for k, v in vars(OpCode).items() if k.startswith('OP_')}


def _py_repr(val):
    """Serialize a constant value as a Python literal."""
    if val is None:
        return "None"
    if isinstance(val, bool):
        return "True" if val else "False"
    if isinstance(val, (int, float)):
        return repr(val)
    if isinstance(val, str):
        return repr(val)
    return "None"


def _func_tuple(name, addr, nparams, bytecode):
    """Serialize function metadata to Python source."""
    return f'("{name}", {addr}, {nparams}, {list(bytecode)})'


def _generate_py_script(bytecode, constants, line_map, functions):
    """Generate a Python wrapper script that loads and runs the bytecode."""

    # Build function info strings
    func_items = []
    for name, (addr, nparams, params, is_async) in functions.items():
        func_items.append(f'    "{name}": ({addr}, {nparams}, {repr(params)}, {is_async}),')

    funcs_dict = "{\n" + "\n".join(func_items) + "\n}"

    bc_str = repr([int(b) for b in bytecode])
    const_str = repr(list(constants))
    lm_str = repr({int(k): v for k, v in line_map.items()})

    script = f'''"""
Alvz - Programa compilado.
Generado por alvz build. No modificar manualmente.
"""
import sys
import os

# Ensure bundled alvz package is importable
_bundle_dir = os.path.dirname(os.path.abspath(__file__))
if _bundle_dir not in sys.path:
    sys.path.insert(0, _bundle_dir)

from alvz.core.vm import VM

# Bytecode embebido
bytecode = {bc_str}
constants = {const_str}
line_map = {lm_str}
functions = {funcs_dict}

vm = VM(bytecode, constants, line_map, functions)
vm.run()
'''
    return script


def build(source_file, output_file=None, opts=None):
    """Compile an .alvz file to standalone executable.
    
    Args:
        source_file: Path to .alvz file
        output_file: Output executable path (optional)
        opts: Dict with options like {'backend': 'pyinstaller'|'nuitka'}
    """
    if opts is None:
        opts = {}
    if not os.path.exists(source_file):
        print(f"Error: archivo '{source_file}' no encontrado")
        return False

    # Compile Alvz source to bytecode
    with open(source_file, 'r', encoding='utf-8-sig') as f:
        code = f.read()

    print(f"Compilando {source_file}...")
    lexer = Lexer(code)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    bytecode, constants, line_map, functions = parser.compile()

    # Determine output name
    if output_file is None:
        base = os.path.splitext(os.path.basename(source_file))[0]
        output_file = base + ('.exe' if platform.system() == 'Windows' else '')

    # Generate Python wrapper
    py_source = _generate_py_script(bytecode, constants, line_map, functions)

    # Write to temp directory
    tmp_dir = tempfile.mkdtemp()
    gen_py = os.path.join(tmp_dir, 'main.py')
    with open(gen_py, 'w', encoding='utf-8') as f:
        f.write(py_source)

    # Copy the alvz package into the temp dir so PyInstaller finds it
    alvz_src = os.path.join(os.path.dirname(os.path.dirname(__file__)))
    alvz_dst = os.path.join(tmp_dir, 'alvz')
    shutil.copytree(alvz_src, alvz_dst, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', 'runtime'))

    out_dir = os.path.join(tmp_dir, 'dist')

    if opts.get('backend') == 'nuitka':
        return _build_nuitka(gen_py, output_file, tmp_dir, out_dir)
    else:
        return _build_pyinstaller(gen_py, output_file, tmp_dir, out_dir)


def _build_pyinstaller(gen_py, output_file, tmp_dir, out_dir):
    try:
        import PyInstaller.__main__
    except ImportError:
        print("Error: PyInstaller no esta instalado.")
        print("Instala con: pip install pyinstaller")
        shutil.rmtree(tmp_dir)
        return False

    print(f"Generando ejecutable via PyInstaller...")
    PyInstaller.__main__.run([
        '--onefile',
        '--distpath', out_dir,
        '--specpath', tmp_dir,
        '--workpath', os.path.join(tmp_dir, 'build'),
        '--name', os.path.splitext(os.path.basename(output_file))[0],
        '--noconsole',
        gen_py,
    ])

    # Locate the generated exe (platform-agnostic: PyInstaller adds .exe on Windows)
    exe_name = os.path.splitext(os.path.basename(output_file))[0]
    built_exe = os.path.join(out_dir, exe_name + ('.exe' if platform.system() == 'Windows' else ''))
    if not os.path.exists(built_exe):
        built_exe = os.path.join(out_dir, exe_name + '.exe')  # fallback
    if os.path.exists(built_exe):
        shutil.move(built_exe, os.path.abspath(output_file))
        print(f"[OK] Ejecutable generado: {os.path.abspath(output_file)}")
        success = True
    else:
        print("Error: No se pudo generar el ejecutable.")
        success = False

    # Cleanup
    shutil.rmtree(tmp_dir, ignore_errors=True)
    return success


def _build_nuitka(gen_py, output_file, tmp_dir, out_dir):
    """Build using Nuitka (Python-to-C++ compiler) for real native compilation."""
    import subprocess

    exe_name = os.path.splitext(os.path.basename(output_file))[0]
    nuitka_cmd = [
        sys.executable, '-m', 'nuitka',
        '--onefile',
        f'--output-dir={out_dir}',
        f'--output-filename={exe_name}',
        '--quiet',
        '--disable-ccache',
        gen_py,
    ]

    print(f"Generando ejecutable nativo via Nuitka (C++ → nativo)...")
    print(f"  Esto puede tomar varios minutos la primera vez.")
    try:
        result = subprocess.run(nuitka_cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            print(f"Error Nuitka: {result.stderr[:500]}")
            print("\nConsejo: Instala Nuitka con 'pip install nuitka'")
            print("  y asegurate de tener un compilador C (gcc, clang, o MSVC).")
            shutil.rmtree(tmp_dir)
            return False
    except FileNotFoundError:
        print("Error: Nuitka no esta instalado.")
        print("Instala con: pip install nuitka")
        print("  y asegurate de tener un compilador C (gcc/clang/MSVC).")
        shutil.rmtree(tmp_dir)
        return False
    except subprocess.TimeoutExpired:
        print("Error: La compilacion con Nuitka excedio el tiempo limite.")
        shutil.rmtree(tmp_dir)
        return False

    built_exe = os.path.join(out_dir, exe_name + ('.exe' if platform.system() == 'Windows' else ''))
    if os.path.exists(built_exe):
        import shutil as sh
        sh.move(built_exe, os.path.abspath(output_file))
        print(f"[OK] Ejecutable nativo generado: {os.path.abspath(output_file)}")
        size = os.path.getsize(os.path.abspath(output_file))
        print(f"     Tamano: {size / 1024 / 1024:.1f} MB")
        success = True
    else:
        print(f"Error: No se encontro el ejecutable en {built_exe}")
        success = False

    shutil.rmtree(tmp_dir, ignore_errors=True)
    return success


def cli():
    """CLI handler for 'alvz build'."""
    args = sys.argv[2:]  # skip 'build'
    source_file = None
    output_file = None
    opts = {}

    for i, arg in enumerate(args):
        if arg == '-o' and i + 1 < len(args):
            output_file = args[i + 1]
        elif arg == '--nuitka':
            opts['backend'] = 'nuitka'
        elif not arg.startswith('-'):
            source_file = arg

    if source_file is None:
        ext = '.exe' if platform.system() == 'Windows' else ''
        print(f"Uso: alvz build archivo.alvz [-o salida{ext}] [--nuitka]")
        print(f"")
        print(f"Opciones:")
        print(f"  --nuitka    Compila a nativo real via Nuitka (Python→C++→nativo)")
        print(f"              Requiere: pip install nuitka y un compilador C")
        print(f"  -o ARCHIVO  Nombre del ejecutable de salida")
        sys.exit(1)

    success = build(source_file, output_file, opts)
    sys.exit(0 if success else 1)
