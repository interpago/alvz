"""
Gestor de paquetes para Alvz Language.

Registro de paquetes vía index online.
Instalacion local en ~/.alvz/packages/.
"""

import json
import os
import sys
import urllib.request
import urllib.error
import zipfile
import io
import shutil


REGISTRY_URL = "https://raw.githubusercontent.com/interpago/alvz-packages/main/index.json"
ALVZ_DIR = os.path.join(os.path.expanduser("~"), ".alvz")
PACKAGES_DIR = os.path.join(ALVZ_DIR, "packages")


class Package:
    def __init__(self, name, version, description, author, url, entry, dependencies=None):
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.url = url
        self.entry = entry
        self.dependencies = dependencies or []

    def to_dict(self):
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "url": self.url,
            "entry": self.entry,
            "dependencies": self.dependencies,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"],
            version=data["version"],
            description=data.get("description", ""),
            author=data.get("author", ""),
            url=data["url"],
            entry=data.get("entry", f"{data['name']}.alvz"),
            dependencies=data.get("dependencies", []),
        )


def _ensure_dirs():
    os.makedirs(PACKAGES_DIR, exist_ok=True)


def _local_db_path():
    return os.path.join(ALVZ_DIR, "installed.json")


def _load_local_db():
    path = _local_db_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_local_db(db):
    _ensure_dirs()
    path = _local_db_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)


def fetch_registry(url=REGISTRY_URL):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Alvz-Package-Manager/0.1"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return [Package.from_dict(p) for p in data.get("packages", data).values()] if isinstance(data, dict) else [Package.from_dict(p) for p in data]
    except (urllib.error.URLError, json.JSONDecodeError, Exception) as e:
        print(f"Error al conectar con el registro: {e}")
        return []


def search_packages(query):
    packages = fetch_registry()
    if not packages:
        print("No se pudo obtener el registro de paquetes.")
        return
    query_lower = query.lower()
    results = [p for p in packages if query_lower in p.name.lower() or query_lower in p.description.lower()]
    if not results:
        print(f"No se encontraron paquetes para: {query}")
        return
    print(f"\nPaquetes encontrados ({len(results)}):")
    print("-" * 50)
    for p in results:
        print(f"  {p.name} v{p.version} - {p.description}")
        print(f"    Autor: {p.author}")


def install_package(name, registry_url=REGISTRY_URL):
    _ensure_dirs()
    packages = fetch_registry(registry_url)
    if not packages:
        return False

    match = None
    for p in packages:
        if p.name == name:
            match = p
            break
    if match is None:
        # Try fuzzy search
        for p in packages:
            if name.lower() in p.name.lower():
                match = p
                break
    if match is None:
        print(f"Paquete '{name}' no encontrado en el registro.")
        return False

    pkg_dir = os.path.join(PACKAGES_DIR, match.name)
    if os.path.exists(pkg_dir):
        print(f"El paquete '{match.name}' ya esta instalado.")
        return False

    # Install dependencies first
    for dep in match.dependencies:
        print(f"Instalando dependencia: {dep}...")
        install_package(dep, registry_url)

    # Download package
    print(f"Descargando {match.name} v{match.version}...")
    try:
        req = urllib.request.Request(match.url, headers={"User-Agent": "Alvz-Package-Manager/0.1"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
    except urllib.error.URLError as e:
        print(f"Error al descargar {match.name}: {e}")
        return False

    # Extract if zip
    if match.url.endswith(".zip"):
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                zf.extractall(pkg_dir)
        except zipfile.BadZipFile as e:
            print(f"Error al extraer {match.name}: {e}")
            return False
    else:
        # Single file download
        os.makedirs(pkg_dir, exist_ok=True)
        entry_path = os.path.join(pkg_dir, match.entry)
        with open(entry_path, "wb") as f:
            f.write(data)

    # Save to local db
    db = _load_local_db()
    db[match.name] = match.to_dict()
    _save_local_db(db)

    print(f"[OK] Paquete '{match.name}' v{match.version} instalado correctamente.")
    return True


def uninstall_package(name):
    pkg_dir = os.path.join(PACKAGES_DIR, name)
    if not os.path.exists(pkg_dir):
        print(f"El paquete '{name}' no esta instalado.")
        return False

    shutil.rmtree(pkg_dir)
    db = _load_local_db()
    if name in db:
        del db[name]
        _save_local_db(db)
    print(f"[OK] Paquete '{name}' desinstalado correctamente.")
    return True


def list_installed():
    db = _load_local_db()
    if not db:
        print("No hay paquetes instalados.")
        return
    print(f"\nPaquetes instalados ({len(db)}):")
    print("-" * 50)
    for name, info in db.items():
        print(f"  {name} v{info.get('version', '?')} - {info.get('description', '')}")


def get_package_path(name):
    pkg_dir = os.path.join(PACKAGES_DIR, name)
    entry_file = os.path.join(pkg_dir, f"{name}.alvz")
    if os.path.exists(entry_file):
        return entry_file
    return None


def info_package(name):
    """Muestra informacion detallada de un paquete en el registro."""
    packages = fetch_registry()
    if not packages:
        return
    for p in packages:
        if p.name == name:
            print(f"\n{'-'*50}")
            print(f"  Nombre: {p.name}")
            print(f"  Version: {p.version}")
            print(f"  Descripcion: {p.description}")
            print(f"  Autor: {p.author}")
            print(f"  URL: {p.url}")
            print(f"  Entry: {p.entry}")
            if p.dependencies:
                print(f"  Dependencias: {', '.join(p.dependencies)}")
            else:
                print("  Dependencias: ninguna")
            print(f"{'-'*50}")
            return
    print(f"Paquete '{name}' no encontrado en el registro.")


def publish_package(pkg_dir):
    """Empaqueta un directorio como paquete Alvz publicable."""
    import zipfile
    import json
    import io

    meta_path = os.path.join(pkg_dir, 'alvz.json')
    if not os.path.isfile(meta_path):
        print(f"Error: no se encuentra '{meta_path}'")
        print("Debes crear un archivo alvz.json con la metadata del paquete:")
        print('  { "name": "mi-paquete", "version": "1.0.0",')
        print('    "description": "...", "author": "...",')
        print('    "entry": "main.alvz", "dependencies": [] }')
        return False

    with open(meta_path, 'r', encoding='utf-8-sig') as f:
        meta = json.load(f)

    name = meta.get('name', os.path.basename(pkg_dir))
    version = meta.get('version', '0.1.0')
    entry = meta.get('entry', f'{name}.alvz')

    entry_path = os.path.join(pkg_dir, entry)
    if not os.path.isfile(entry_path):
        print(f"Error: archivo de entrada '{entry}' no encontrado en {pkg_dir}")
        return False

    zip_name = f'{name}-{version}.zip'
    zip_path = os.path.join(os.getcwd(), zip_name)

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(pkg_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, pkg_dir)
                zf.write(file_path, arcname)

    print(f"\n[OK] Paquete creado: {zip_path}")
    print(f"\nPara publicarlo en el registro oficial:")
    print(f"  1. Sube el archivo a GitHub Releases o un servidor HTTP")
    print(f"  2. Agrega una entrada en el registro:")
    print(f"     https://github.com/interpago/alvz-packages")
    print(f"  3. El formato de entrada es:")
    print(f'     {{ "name": "{name}", "version": "{version}",')
    print(f'        "url": "<url_del_zip>",')
    print(f'        "entry": "{entry}",')
    print(f'        "dependencies": {json.dumps(meta.get("dependencies", []))} }}')
    return True


def cli():
    if len(sys.argv) < 3:
        print("Uso: alvz install <paquete>[@version]")
        print("      alvz uninstall <paquete>")
        print("      alvz publish <directorio>")
        print("      alvz list-packages")
        print("      alvz search <consulta>")
        print("      alvz info <paquete>")
        sys.exit(1)

    command = sys.argv[1]
    if command == "install":
        spec = sys.argv[2]
        version = None
        if '@' in spec:
            name, version = spec.split('@', 1)
        else:
            name = spec
        install_package(name)
    elif command == "uninstall":
        name = sys.argv[2]
        uninstall_package(name)
    elif command == "publish":
        publish_package(sys.argv[2])
    elif command == "search":
        query = sys.argv[2]
        search_packages(query)
    elif command == "list-packages":
        list_installed()
    elif command == "info":
        info_package(sys.argv[2])
    else:
        print(f"Comando desconocido: {command}")
        print("Comandos: install, uninstall, publish, search, list-packages, info")
        sys.exit(1)
