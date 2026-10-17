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

@pytest.mark.parametrize("pfad", [
    "Directory.Packages.props",
    "/home/kieritz/repos/mahl/Directory.Packages.props",
    "C:\\repos\\mahl\\Directory.Packages.props",
])
def test_directory_packages_props_blocked(pfad):
    assert get_denial_reason(pfad) is not None

def test_directory_packages_props_nur_als_ganzer_dateiname():
    assert get_denial_reason("MyDirectory.Packages.props") is None

@pytest.mark.parametrize("pfad, dateiname", [
    ("Client/package.json", "package.json"),
    ("Server/mahl.Server.csproj", ".csproj"),
    ("Directory.Packages.props", "Directory.Packages.props"),
    ("docs/reference/dependencies.md", "dependencies.md"),
])
def test_meldung_nennt_die_geschuetzte_datei(pfad, dateiname):
    assert f"({dateiname})" in get_denial_reason(pfad)

def test_meldung_nennt_den_ort_der_nuget_versionen():
    assert "Version in Directory.Packages.props" in get_denial_reason("Server/mahl.Server.csproj")


# --- Directory.Build.*: Build-Einstellungen frei, Paketreferenzen nicht ---

@pytest.mark.parametrize("pfad", ["Directory.Build.props", "/repo/Directory.Build.targets"])
@pytest.mark.parametrize("neuer_text", [
    '<PackageReference Include="Npgsql" Version="10.0.2" />',
    '<PackageReference Update="Npgsql" />',
    '<PackageVersion Include="Npgsql" Version="10.0.2" />',
    '<GlobalPackageReference Include="Meziantou.Analyzer" Version="3.0.43" />',
])
def test_directory_build_mit_paketreferenz_blocked(pfad, neuer_text):
    assert get_denial_reason(pfad, neuer_text) is not None

@pytest.mark.parametrize("neuer_text", [
    "<LangVersion>latest</LangVersion>",
    "<PackageReference>\n\t<PrivateAssets>compile</PrivateAssets>\n</PackageReference>",
    '<_DirectPackage Include="@(PackageReference)" />',
])
def test_directory_build_ohne_paketreferenz_not_blocked(neuer_text):
    assert get_denial_reason("Directory.Build.props", neuer_text) is None


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
def test_check_blockt_edit_an_package_json_mit_absolutem_pfad():
    """Der Dispatcher liefert absolute Pfade – die Muster tragen sie ohne Kürzung."""
    daten = {"tool_name": "Edit", "tool_input": {"file_path": "/repo/Client/package.json"}}
    assert _hook.check(daten) is not None


@pytest.mark.parametrize("daten", [
    {"tool_name": "Edit"},
    {"tool_name": "Edit", "tool_input": {}},
    {"tool_name": "Write", "tool_input": {"file_path": "Directory.Build.props"}},  # ohne Text
])
def test_check_ohne_pfad_oder_text_blockt_nicht(daten):
    assert _hook.check(daten) is None


@pytest.mark.parametrize("tool_input", [
    {"file_path": "/repo/Directory.Build.props", "new_string": '<PackageReference Include="Npgsql" />'},
    {"file_path": "/repo/Directory.Build.targets", "content": '<PackageVersion Include="Npgsql" />'},
])
def test_check_prueft_neuen_text_von_edit_und_write(tool_input):
    tool_name = "Write" if "content" in tool_input else "Edit"
    assert _hook.check({"tool_name": tool_name, "tool_input": tool_input}) is not None


def test_check_ignoriert_andere_werkzeuge():
    daten = {"tool_name": "Read", "tool_input": {"file_path": "Client/package.json"}}
    assert _hook.check(daten) is None
