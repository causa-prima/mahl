"""Tests für checks/primitives.py"""
from conftest import make_input
from checks.primitives import check_blocking, check_nonblocking

DOMAIN_FILE = "Shared/Types/Foo.cs"
DTO_FILE = "Shared/Dtos/FooDto.cs"
ENDPOINT_FILE = "Server/Endpoints/Foo.cs"


# --- blocking: Properties ---

def test_string_property_blocked():
    inp = make_input(DOMAIN_FILE, "public string Name { get; init; }")
    assert check_blocking(inp) != []

def test_string_property_write_blocked():
    inp = make_input(DOMAIN_FILE, "public string Name { get; init; }", tool="Write")
    assert check_blocking(inp) != []

def test_dto_not_blocked():
    inp = make_input(DTO_FILE, "public string Name { get; init; }")
    assert check_blocking(inp) == []

def test_endpoint_mapping_line_not_blocked():
    inp = make_input(ENDPOINT_FILE, 'group.MapGet("/{id:int}", (int id, DbContext db) =>')
    assert check_blocking(inp) == []


# --- nonblocking: Parameter ---

def test_string_param_without_error_string_hints():
    inp = make_input(DOMAIN_FILE, "public static Ingredient From(string name) =>")
    assert check_nonblocking(inp) != []

def test_error_string_factory_method_not_hinted():
    inp = make_input(DOMAIN_FILE, "public static OneOf<Ingredient, Error<string>> Create(string name) =>")
    assert check_nonblocking(inp) == []

def test_string_property_not_hinted_by_nonblocking():
    # Properties werden von check_blocking abgedeckt, nicht check_nonblocking
    inp = make_input(DOMAIN_FILE, "public string Name { get; init; }")
    assert check_nonblocking(inp) == []
