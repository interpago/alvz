"""Tests para el gestor de paquetes de Alvz."""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

import pytest

from alvz.core.package_manager import (
    Package,
    fetch_registry,
    search_packages,
    install_package,
    uninstall_package,
    list_installed,
    get_package_path,
    _load_local_db,
    _save_local_db,
    _ensure_dirs,
    ALVZ_DIR,
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
