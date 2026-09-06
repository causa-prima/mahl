"""Tests für prozesscode/hooks/check-dependency-allowlist.py"""
from importlib import import_module

get_denial_reason = import_module(
    "prozesscode.hooks.check-dependency-allowlist").get_denial_reason


# --- blockiert ---

def test_package_json_blocked():
    assert get_denial_reason("Client/package.json") is not None

def test_package_json_absolute_path_blocked():
    assert get_denial_reason("/home/kieritz/repos/mahl/Client/package.json") is not None

def test_csproj_blocked():
    assert get_denial_reason("Server/mahl.Server.csproj") is not None

def test_csproj_tests_blocked():
    assert get_denial_reason("Server.Tests/mahl.Server.Tests.csproj") is not None

def test_dependencies_md_blocked():
    assert get_denial_reason("docs/reference/dependencies.md") is not None

def test_dependencies_md_absolute_blocked():
    assert get_denial_reason("/repo/docs/reference/dependencies.md") is not None


# --- erlaubt ---

def test_other_json_not_blocked():
    assert get_denial_reason("appsettings.json") is None

def test_other_md_not_blocked():
    assert get_denial_reason("docs/reference/architecture.md") is None

def test_cs_file_not_blocked():
    assert get_denial_reason("Server/Domain/Ingredient.cs") is None

def test_ts_file_not_blocked():
    assert get_denial_reason("Client/src/App.tsx") is None
