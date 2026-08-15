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


# --- Drei-Ebenen-Regel: Entity vs. Constraint-/Domänentyp (§2) ---------------
# Beide Ebenen liegen in Server/Domain/, haben aber gegensätzliche Regeln. Unterschieden
# wird an der `Value`-Property: Wer den Primitive kapselt, darf ihn annehmen.

ENTITY_FILE = "Server/Domain/Ingredient.cs"
DOMAIN_TYPE_FILE = "Server/Domain/IngredientName.cs"

_VALUE_WRAPPER = (
    "private readonly Bounded<NonEmpty<TrimmedString>, Max30> _value;\n"
    "public string Value => _value.Value;\n"
    "public static OneOf<IngredientName, IngredientValidationError> Create(string input) =>\n"
)
_ENTITY = (
    "public IngredientName Name => _name;\n"
    "public static Ingredient Create(Guid id, IngredientName name, Unit defaultUnit) =>\n"
)


def test_entity_with_raw_guid_param_is_blocked():
    inp = make_input(ENTITY_FILE, _ENTITY)
    assert check_blocking(inp) != []


def test_domain_type_taking_primitive_is_allowed():
    # IngredientName.Create(string) IST die Validierungsebene – Blocken wäre falsch.
    inp = make_input(DOMAIN_TYPE_FILE, _VALUE_WRAPPER)
    assert check_blocking(inp) == []


def test_value_property_itself_is_not_a_leak():
    inp = make_input(DOMAIN_TYPE_FILE, "public string Value => _value.Value;")
    assert check_blocking(inp) == []


def test_expression_bodied_property_without_value_is_blocked():
    # Regression: bis S119 matchte nur `{ get; }`, Domain-Typen nutzen aber `=>`.
    inp = make_input(ENTITY_FILE, "public Guid Id => _id;")
    assert check_blocking(inp) != []


def test_entity_param_is_not_reported_twice():
    # In einer Entity ist der Parameter blockierend – der Hinweis muss dann schweigen.
    inp = make_input(ENTITY_FILE, _ENTITY)
    assert check_nonblocking(inp) == []


def test_domain_type_param_is_silent_not_merely_unblocked():
    # Ein Signal, das bei JEDEM guideline-konformen `Create(string)` anspringt, wird gelesen
    # wie keines. Der Value-Wrapper nimmt Primitives per Konstruktion – weder Block noch Hinweis.
    inp = make_input(DOMAIN_TYPE_FILE, _VALUE_WRAPPER + "public static IngredientName Of(string i) =>")
    assert check_blocking(inp) == []
    assert check_nonblocking(inp) == []


def test_hint_still_fires_outside_domain_and_wrapper():
    # Gegenstück: ohne Value-Property und außerhalb von Domain/ bleibt der Hinweis erhalten.
    inp = make_input("Server/Services/Foo.cs", "public static Foo Of(string raw) =>")
    assert check_blocking(inp) == []
    assert check_nonblocking(inp) != []


# --- Sum-Types (ADR-S018-1): dritte Kategorie neben Entity und Value-Wrapper -------------
# Ihre Value-Träger-Subtypen führen den Payload bewusst als Primitive. Ohne Ausnahme sperrte
# der Check `IngredientValidationError.cs` vollständig (im Review verifiziert, nicht vermutet).

SUM_TYPE_FILE = "Server/Domain/IngredientValidationError.cs"
_SUM_TYPE = (
    "internal abstract record IngredientValidationError\n"
    "{\n"
    "    private sealed record NameDuplicateCase(string EnteredName) : IngredientValidationError;\n"
)


def test_sum_type_payload_case_is_not_misclassified_as_entity():
    inp = make_input(SUM_TYPE_FILE, _SUM_TYPE, tool="Write")
    assert check_blocking(inp) == []
    assert check_nonblocking(inp) == []


def test_sum_type_factory_with_primitive_is_allowed(tmp_path):
    # Fragment-Fall: die `abstract record`-Zeile steht nur in der Datei, nicht im Ausschnitt.
    path = _cs_file(tmp_path, "IngredientValidationError.cs", _SUM_TYPE)
    inp = make_input(path, "    public static IngredientValidationError NameDuplicate(string n) =>")
    assert check_blocking(inp) == []


def test_match_method_alone_marks_a_sum_type():
    inp = make_input(SUM_TYPE_FILE, "    public T Match<T>(\n        Func<string, T> onNameDuplicate)")
    assert check_blocking(inp) == []


# --- Edit-Fragment vs. ganze Datei -------------------------------------------
# Bei `Edit` enthält new_content nur den geänderten Ausschnitt. Die Rolle des Typs
# (Entity vs. Value-Wrapper) steht aber in der Datei – sonst gäbe es Fehlalarm, sobald
# jemand in einem Domänentyp nur die Create-Zeile anfasst.

def _cs_file(tmp_path, name: str, body: str) -> str:
    domain = tmp_path / "Server" / "Domain"
    domain.mkdir(parents=True, exist_ok=True)
    target = domain / name
    target.write_text(body, encoding="utf-8")
    return str(target)


def test_value_property_is_found_in_file_not_only_in_fragment(tmp_path):
    path = _cs_file(tmp_path, "IngredientName.cs", _VALUE_WRAPPER)
    # Fragment ohne Value-Property – die Rolle steht nur in der Datei.
    inp = make_input(path, "public static OneOf<IngredientName, Err> Create(string input) =>")
    assert check_blocking(inp) == []


def test_entity_fragment_still_blocks_when_file_has_no_value_property(tmp_path):
    path = _cs_file(tmp_path, "Ingredient.cs", "internal readonly record struct Ingredient { }")
    inp = make_input(path, "public static Ingredient Create(Guid id, IngredientName name) =>")
    assert check_blocking(inp) != []


def test_missing_file_falls_back_to_fragment(tmp_path):
    # Neue Datei (Write auf noch nicht existierenden Pfad) – nur das Fragment ist verfügbar.
    path = str(tmp_path / "Server" / "Domain" / "Neu.cs")
    inp = make_input(path, _VALUE_WRAPPER, tool="Write")
    assert check_blocking(inp) == []
