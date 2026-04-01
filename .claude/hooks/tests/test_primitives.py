"""Tests für checks/primitives.py"""
from conftest import make_input
from checks import primitives

DOMAIN_FILE = "Shared/Types/Foo.cs"
DTO_FILE = "Shared/Dtos/FooDto.cs"
ENDPOINT_FILE = "Server/Endpoints/Foo.cs"


# --- blockiert ---

def test_string_property_blocked():
    inp = make_input(DOMAIN_FILE, "public string Name { get; init; }")
    assert primitives.check(inp) != []

def test_string_property_write_blocked():
    inp = make_input(DOMAIN_FILE, "public string Name { get; init; }", tool="Write")
    assert primitives.check(inp) != []


# --- erlaubt ---

def test_dto_not_blocked():
    inp = make_input(DTO_FILE, "public string Name { get; init; }")
    assert primitives.check(inp) == []

def test_endpoint_mapping_line_not_blocked():
    inp = make_input(ENDPOINT_FILE, 'group.MapGet("/{id:int}", (int id, DbContext db) =>')
    assert primitives.check(inp) == []

def test_error_string_factory_method_not_blocked():
    inp = make_input(DOMAIN_FILE, "public static OneOf<Ingredient, Error<string>> Create(string name) =>")
    assert primitives.check(inp) == []

def test_string_param_without_error_string_still_blocked():
    inp = make_input(DOMAIN_FILE, "public static Ingredient From(string name) =>")
    assert primitives.check(inp) != []
