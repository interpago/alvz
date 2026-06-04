"""Tests para el gestor de paquetes de Alvz."""

import os
import tempfile
import shutil

import pytest

from alvz.core.package_manager import (
    Package,
    search_packages,
    install_package,
    uninstall_package,
    list_installed,
    get_package_path,
    _load_local_db,
    _save_local_db,
    _ensure_dirs,
)


@pytest.fixture
def temp_alvz_dir(monkeypatch):
    """Redirect .alvz to a temp directory for testing."""
    tmpdir = tempfile.mkdtemp()
    monkeypatch.setattr("alvz.core.package_manager.ALVZ_DIR", tmpdir)
    monkeypatch.setattr("alvz.core.package_manager.PACKAGES_DIR", os.path.join(tmpdir, "packages"))
    yield tmpdir
    shutil.rmtree(tmpdir)


class TestPackage:
    def test_to_dict_and_from_dict(self):
        p = Package("math", "1.0.0", "Math utils", "Alvz", "https://example.com/math.zip", "math.alvz", ["util"])
        d = p.to_dict()
        assert d["name"] == "math"
        assert d["version"] == "1.0.0"
        assert d["description"] == "Math utils"
        assert d["author"] == "Alvz"
        assert d["url"] == "https://example.com/math.zip"
        assert d["entry"] == "math.alvz"
        assert d["dependencies"] == ["util"]

        p2 = Package.from_dict(d)
        assert p2.name == "math"
        assert p2.version == "1.0.0"
        assert p2.dependencies == ["util"]

    def test_from_dict_defaults(self):
        p = Package.from_dict({"name": "foo", "version": "0.1", "url": "https://x.com/foo.alvz"})
        assert p.name == "foo"
        assert p.description == ""
        assert p.author == ""
        assert p.entry == "foo.alvz"
        assert p.dependencies == []


class TestLocalDB:
    def test_ensure_dirs(self, temp_alvz_dir):
        _ensure_dirs()
        assert os.path.exists(temp_alvz_dir)
        assert os.path.exists(os.path.join(temp_alvz_dir, "packages"))

    def test_save_and_load_db(self, temp_alvz_dir):
        db = {"math": {"name": "math", "version": "1.0"}}
        _save_local_db(db)
        loaded = _load_local_db()
        assert loaded == db

    def test_load_empty_db(self, temp_alvz_dir):
        db = _load_local_db()
        assert db == {}


class TestListInstalled:
    def test_empty_list(self, temp_alvz_dir, capsys):
        list_installed()
        captured = capsys.readouterr()
        assert "No hay paquetes instalados" in captured.out

    def test_with_packages(self, temp_alvz_dir, capsys):
        db = {"math": {"name": "math", "version": "1.0", "description": "Math utils"}}
        _save_local_db(db)
        list_installed()
        captured = capsys.readouterr()
        assert "math" in captured.out
        assert "1.0" in captured.out
        assert "Math utils" in captured.out


class TestGetPackagePath:
    def test_not_installed(self, temp_alvz_dir):
        result = get_package_path("nonexistent")
        assert result is None

    def test_installed(self, temp_alvz_dir):
        packages_dir = os.path.join(temp_alvz_dir, "packages")
        pkg_dir = os.path.join(packages_dir, "testpkg")
        os.makedirs(pkg_dir)
        entry = os.path.join(pkg_dir, "testpkg.alvz")
        with open(entry, "w") as f:
            f.write('imprimir("ok")\n')
        result = get_package_path("testpkg")
        assert result == entry


class TestUninstallPackage:
    def test_uninstall_not_installed(self, temp_alvz_dir, capsys):
        uninstall_package("nonexistent")
        captured = capsys.readouterr()
        assert "no esta instalado" in captured.out

    def test_uninstall_installed(self, temp_alvz_dir, capsys):
        packages_dir = os.path.join(temp_alvz_dir, "packages")
        pkg_dir = os.path.join(packages_dir, "testpkg")
        os.makedirs(pkg_dir)
        entry = os.path.join(pkg_dir, "testpkg.alvz")
        with open(entry, "w") as f:
            f.write("")
        db = {"testpkg": {"name": "testpkg", "version": "0.1"}}
        _save_local_db(db)

        uninstall_package("testpkg")
        assert not os.path.exists(pkg_dir)
        assert "testpkg" not in _load_local_db()
        captured = capsys.readouterr()
        assert "desinstalado" in captured.out


class TestSearchPackages:
    def test_no_registry(self, temp_alvz_dir, capsys, monkeypatch):
        """When registry fetch fails, it should print a message."""
        # Mock fetch_registry to return empty
        monkeypatch.setattr("alvz.core.package_manager.fetch_registry", lambda url=...,: [])
        search_packages("math")
        captured = capsys.readouterr()
        assert "No se pudo obtener el registro" in captured.out


class TestInstallPackage:
    def test_not_in_registry(self, temp_alvz_dir, capsys, monkeypatch):
        monkeypatch.setattr(
            "alvz.core.package_manager.fetch_registry",
            lambda url=...,: [Package("math", "1.0", "Math", "Alvz", "https://x.com/m.zip", "math.alvz")]
        )
        result = install_package("nonexistent")
        assert result is False
        captured = capsys.readouterr()
        assert "no encontrado" in captured.out

    def test_already_installed(self, temp_alvz_dir, capsys, monkeypatch):
        packages_dir = os.path.join(temp_alvz_dir, "packages")
        pkg_dir = os.path.join(packages_dir, "math")
        os.makedirs(pkg_dir)
        monkeypatch.setattr(
            "alvz.core.package_manager.fetch_registry",
            lambda url=...,: [Package("math", "1.0", "Math", "Alvz", "https://x.com/m.zip", "math.alvz")]
        )
        result = install_package("math")
        assert result is False
        captured = capsys.readouterr()
        assert "ya esta instalado" in captured.out


class TestFetchRegistry:
    def test_fetch_registry_error(self, capsys, monkeypatch):
        """fetch_registry should handle network errors gracefully."""
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda req, timeout=10: (_ for _ in ()).throw(urllib.error.URLError("timeout"))
        )
        import urllib.error
        from alvz.core.package_manager import fetch_registry
        result = fetch_registry()
        assert result == []

    def test_fetch_registry_json_error(self, capsys, monkeypatch):
        """fetch_registry should handle invalid JSON."""
        class FakeResponse:
            def read(self):
                return b"not valid json"
            def __exit__(self, *args):
                pass
            def __enter__(self):
                return self
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda req, timeout=10: FakeResponse()
        )
        from alvz.core.package_manager import fetch_registry
        result = fetch_registry()
        assert result == []


class TestSearchPackagesExtended:
    def test_search_found(self, temp_alvz_dir, capsys, monkeypatch):
        monkeypatch.setattr(
            "alvz.core.package_manager.fetch_registry",
            lambda url=...,: [
                Package("math", "1.0", "Matematicas", "Alvz", "https://x.com/m.zip", "math.alvz"),
                Package("texto", "1.0", "Texto utils", "Alvz", "https://x.com/t.zip", "texto.alvz"),
            ]
        )
        search_packages("math")
        captured = capsys.readouterr()
        assert "math" in captured.out
        assert "Matematicas" in captured.out

    def test_search_no_results(self, temp_alvz_dir, capsys, monkeypatch):
        monkeypatch.setattr(
            "alvz.core.package_manager.fetch_registry",
            lambda url=...,: [Package("math", "1.0", "Matematicas", "Alvz", "https://x.com/m.zip", "math.alvz")]
        )
        search_packages("nonexistent")
        captured = capsys.readouterr()
        assert "No se encontraron" in captured.out


class TestInstallPackageExtended:
    def test_install_single_file(self, temp_alvz_dir, capsys, monkeypatch):
        """Install a single-file package (not zip)."""
        def mock_fetch(url=...,):
            return [Package("testpkg", "0.1", "Test", "Me", "https://x.com/t.alvz", "testpkg.alvz")]
        monkeypatch.setattr("alvz.core.package_manager.fetch_registry", mock_fetch)

        class FakeResp:
            def read(self):
                return b'imprimir("ok")\n'
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=30: FakeResp())

        result = install_package("testpkg")
        assert result is True
        captured = capsys.readouterr()
        assert "instalado" in captured.out
        # Verify file was created
        path = get_package_path("testpkg")
        assert path is not None
        assert os.path.exists(path)

    def test_install_download_error(self, temp_alvz_dir, capsys, monkeypatch):
        """Install failure when URL download fails."""
        def mock_fetch(url=...,):
            return [Package("testpkg", "0.1", "Test", "Me", "https://x.com/t.alvz", "testpkg.alvz")]
        monkeypatch.setattr("alvz.core.package_manager.fetch_registry", mock_fetch)
        import urllib.error
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda req, timeout=30: (_ for _ in ()).throw(urllib.error.URLError("not found"))
        )
        result = install_package("testpkg")
        assert result is False
        captured = capsys.readouterr()
        assert "Error al descargar" in captured.out

    def test_install_fuzzy_match(self, temp_alvz_dir, capsys, monkeypatch):
        """Install with fuzzy name matching."""
        mock_packages = [Package("matematicas", "1.0", "Math", "Alvz", "https://x.com/m.alvz", "matematicas.alvz")]
        monkeypatch.setattr("alvz.core.package_manager.fetch_registry", lambda url=...,: mock_packages)
        class FakeResp:
            def read(self):
                return b''
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=30: FakeResp())
        result = install_package("mate")
        assert result is True

    def test_install_no_registry(self, temp_alvz_dir, capsys, monkeypatch):
        """Install when registry returns nothing."""
        monkeypatch.setattr("alvz.core.package_manager.fetch_registry", lambda url=...,: [])
        result = install_package("anything")
        assert result is False


class TestInfoPackage:
    def test_info_existing(self, capsys, monkeypatch):
        monkeypatch.setattr(
            "alvz.core.package_manager.fetch_registry",
            lambda url=...,: [Package("math", "1.0", "Matematicas", "Alvz", "https://x.com/m.zip", "math.alvz")]
        )
        from alvz.core.package_manager import info_package
        info_package("math")
        captured = capsys.readouterr()
        assert "math" in captured.out
        assert "Matematicas" in captured.out
        assert "Alvz" in captured.out

    def test_info_not_found(self, capsys, monkeypatch):
        monkeypatch.setattr(
            "alvz.core.package_manager.fetch_registry",
            lambda url=...,: [Package("math", "1.0", "Math", "Alvz", "https://x.com/m.zip", "math.alvz")]
        )
        from alvz.core.package_manager import info_package
        info_package("nonexistent")
        captured = capsys.readouterr()
        assert "no encontrado" in captured.out


class TestLoadLocalDB:
    def test_load_corrupt_json(self, temp_alvz_dir):
        """Corrupt JSON should return empty dict."""
        db_path = os.path.join(temp_alvz_dir, "installed.json")
        with open(db_path, "w", encoding="utf-8") as f:
            f.write("not valid json")
        result = _load_local_db()
        assert result == {}


class TestInfoPackageExtended:
    def test_info_no_registry(self, capsys, monkeypatch):
        monkeypatch.setattr("alvz.core.package_manager.fetch_registry", lambda url=...,: [])
        from alvz.core.package_manager import info_package
        info_package("anything")
        captured = capsys.readouterr()
        # No output when registry is empty
        assert captured.out == ""

    def test_info_with_deps(self, capsys, monkeypatch):
        monkeypatch.setattr(
            "alvz.core.package_manager.fetch_registry",
            lambda url=...,: [Package("math", "1.0", "Math", "Alvz", "https://x.com/m.alvz", "math.alvz", ["util"])]
        )
        from alvz.core.package_manager import info_package
        info_package("math")
        captured = capsys.readouterr()
        assert "util" in captured.out


class TestFetchRegistryExtended:
    def test_fetch_with_packages_as_list(self, capsys, monkeypatch):
        """fetch_registry works when the JSON is a list (not dict with 'packages' key)."""
        class FakeResponse:
            def read(self):
                return b'[{"name": "test", "version": "1.0", "description": "Test", "author": "Me", "url": "https://x.com/t.alvz", "entry": "test.alvz"}]'
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        monkeypatch.setattr("urllib.request.urlopen", lambda req, timeout=10: FakeResponse())
        from alvz.core.package_manager import fetch_registry
        result = fetch_registry()
        assert len(result) == 1
        assert result[0].name == "test"
