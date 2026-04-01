"""Tests für checks/constructors.py"""
import pytest
from conftest import make_input
from checks import constructors

DOMAIN_FILE = "Shared/Types/Foo.cs"
EXCLUDED_FILE = "Server/Data/DatabaseTypes/FooDbType.cs"


# --- blockiert ---

def test_public_ctor_with_params_blocked():
    inp = make_input(DOMAIN_FILE, "public Foo(string name)")
    assert constructors.check(inp) != []

def test_public_ctor_with_params_write_blocked():
    inp = make_input(DOMAIN_FILE, "public Foo(string x) {}", tool="Write")
    assert constructors.check(inp) != []

def test_public_parameterless_ctor_without_throw_blocked():
    # Parameterloser public Ctor ohne throw ist NICHT das erlaubte record-struct-Muster
    inp = make_input(DOMAIN_FILE, "    public Foo()\n    {\n    }")
    assert constructors.check(inp) != []


# --- erlaubt ---

def test_class_declaration_not_blocked():
    # Typ-Deklaration darf nicht als Konstruktor erkannt werden
    inp = make_input(DOMAIN_FILE, "public class Foo")
    assert constructors.check(inp) == []

def test_excluded_path_not_blocked():
    inp = make_input(EXCLUDED_FILE, "public FooDbType()")
    assert constructors.check(inp) == []

def test_test_file_not_blocked():
    inp = make_input("Server.Tests/FooTests.cs", "public Foo(string name)")
    assert constructors.check(inp) == []

def test_private_ctor_not_blocked():
    inp = make_input(DOMAIN_FILE, "private Foo(string name)")
    assert constructors.check(inp) == []

# --- readonly record struct Pflicht-Muster ---

def test_throwing_parameterless_ctor_singleline_allowed():
    # public Ctor() => throw new InvalidOperationException(...) – einzeilig
    content = 'public Foo() => throw new InvalidOperationException("Use Create().");'
    inp = make_input(DOMAIN_FILE, content)
    assert constructors.check(inp) == []

def test_throwing_parameterless_ctor_twoline_allowed():
    # public Ctor() auf einer Zeile, => throw ... auf der nächsten
    content = (
        "    public Foo()\n"
        '        => throw new InvalidOperationException("Use Create().");'
    )
    inp = make_input(DOMAIN_FILE, content)
    assert constructors.check(inp) == []

def test_throwing_parameterless_ctor_with_private_ctor_below_allowed():
    # Typisches readonly record struct: public throw-Ctor + private Factory-Ctor
    content = (
        'public Foo() => throw new InvalidOperationException("Use Create().");\n'
        "private Foo(string value) { _value = value; }"
    )
    inp = make_input(DOMAIN_FILE, content)
    assert constructors.check(inp) == []
