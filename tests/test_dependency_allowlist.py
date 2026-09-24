"""Tests für prozesscode/hooks/check-dependency-allowlist.py"""
from importlib import import_module

import pytest

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


# --- Einstieg über den Dispatcher-Weg ---
_hook = import_module("prozesscode.hooks.check-dependency-allowlist")


@pytest.mark.aufrufpfad("check-dependency-allowlist")
def test_check_blockt_edit_an_package_json_mit_absolutem_pfad(monkeypatch):
    """Der Dispatcher liefert absolute Pfade; `check` kürzt sie um CLAUDE_PROJECT_DIR."""
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", "/repo")
    daten = {"tool_name": "Edit", "tool_input": {"file_path": "/repo/Client/package.json"}}
    assert _hook.check(daten) is not None


def test_check_ignoriert_andere_werkzeuge():
    daten = {"tool_name": "Read", "tool_input": {"file_path": "Client/package.json"}}
    assert _hook.check(daten) is None
