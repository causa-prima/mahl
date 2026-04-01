"""Tests für check-dependency-allowlist.py"""
import importlib.util
import os

_hook_path = os.path.join(os.path.dirname(__file__), "..", "check-dependency-allowlist.py")
_spec = importlib.util.spec_from_file_location("check_dependency_allowlist", _hook_path)
_mod = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_mod)  # type: ignore[union-attr]

get_denial_reason = _mod.get_denial_reason


# --- blockiert ---

def test_package_json_blocked():
    assert get_denial_reason("Client/package.json") is not None

def test_package_json_absolute_path_blocked():
    assert get_denial_reason("/mnt/c/Users/kieritz/source/repos/mahl/Client/package.json") is not None

def test_csproj_blocked():
    assert get_denial_reason("Server/mahl.Server.csproj") is not None

def test_csproj_tests_blocked():
    assert get_denial_reason("Server.Tests/mahl.Server.Tests.csproj") is not None

def test_dependencies_md_blocked():
    assert get_denial_reason("docs/DEPENDENCIES.md") is not None

def test_dependencies_md_absolute_blocked():
    assert get_denial_reason("/repo/docs/DEPENDENCIES.md") is not None


# --- erlaubt ---

def test_other_json_not_blocked():
    assert get_denial_reason("appsettings.json") is None

def test_other_md_not_blocked():
    assert get_denial_reason("docs/ARCHITECTURE.md") is None

def test_cs_file_not_blocked():
    assert get_denial_reason("Server/Domain/Ingredient.cs") is None

def test_ts_file_not_blocked():
    assert get_denial_reason("Client/src/App.tsx") is None
