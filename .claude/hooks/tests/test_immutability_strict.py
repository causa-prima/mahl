"""Tests für checks/immutability_strict.py"""
from conftest import make_input
from checks import immutability_strict

DOMAIN_FILE = "Shared/Foo.cs"
EXCLUDED_FILE = "Server/Data/DatabaseTypes/FooDbType.cs"


# --- blockiert ---

def test_class_without_record_blocked():
    inp = make_input(DOMAIN_FILE, "public class Foo")
    assert immutability_strict.check(inp) != []

def test_public_setter_blocked():
    inp = make_input(DOMAIN_FILE, "public string Name { get; set; }")
    assert immutability_strict.check(inp) != []

def test_both_violations_blocked():
    content = "public class Foo { public string Name { get; set; } }"
    inp = make_input(DOMAIN_FILE, content, tool="Write")
    result = immutability_strict.check(inp)
    assert len(result) == 1
    assert "class" in result[0]
    assert "set;" in result[0]


# --- erlaubt ---

def test_static_class_allowed():
    inp = make_input(DOMAIN_FILE, "public static class FooExtensions")
    assert immutability_strict.check(inp) == []

def test_excluded_path_allowed():
    inp = make_input(EXCLUDED_FILE, "public class FooDbType")
    assert immutability_strict.check(inp) == []

def test_init_setter_allowed():
    inp = make_input(DOMAIN_FILE, "public string Name { get; init; }")
    assert immutability_strict.check(inp) == []

def test_private_setter_allowed():
    inp = make_input(DOMAIN_FILE, "public string Name { get; private set; }")
    assert immutability_strict.check(inp) == []

def test_record_class_allowed():
    inp = make_input(DOMAIN_FILE, "public record class Foo")
    assert immutability_strict.check(inp) == []
