"""Tests für checks/immutability.py"""
from conftest import make_input
from checks import immutability

DOMAIN_FILE = "Shared/Foo.cs"
EXCLUDED_FILE = "Server/Data/DatabaseTypes/FooDbType.cs"


# --- blockiert ---

def test_list_property_blocked():
    inp = make_input(DOMAIN_FILE, "public List<int> Items { get; init; }")
    assert immutability.check(inp) != []

def test_dictionary_property_blocked():
    inp = make_input(DOMAIN_FILE, "public Dictionary<string, int> Map { get; init; }")
    assert immutability.check(inp) != []

def test_blocking_message_format():
    inp = make_input(DOMAIN_FILE, "public List<int> Items { get; init; }")
    result = immutability.check(inp)
    assert result != []
    assert "⛔" in result[0]
    assert "blockierend" in result[0]


# --- erlaubt ---

def test_local_new_list_allowed():
    inp = make_input(DOMAIN_FILE, "var items = new List<int>()")
    assert immutability.check(inp) == []

def test_excluded_path_allowed():
    inp = make_input(EXCLUDED_FILE, "public List<int> Items { get; set; }")
    assert immutability.check(inp) == []
