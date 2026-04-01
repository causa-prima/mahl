"""Tests für den domain_visibility-Check."""
import pytest
from checks.domain_visibility import check
from checks.common import HookInput


def make_input(file_path: str, new_content: str, is_test: bool = False) -> HookInput:
    return HookInput(
        tool="Edit",
        file_path=file_path,
        new_content=new_content,
        old_content="",
        is_cs=file_path.endswith(".cs"),
        is_ts=False,
        is_test=is_test,
        is_domain_excluded=False,
    )


# ── Violations ────────────────────────────────────────────────────────────────

def test_public_class_in_domain_is_violation():
    inp = make_input(
        "Server/Domain/Ingredient.cs",
        "public readonly record struct Ingredient { }"
    )
    result = check(inp)
    assert len(result) == 1
    assert "DOMAIN VISIBILITY" in result[0]


def test_public_class_in_endpoints_is_violation():
    inp = make_input(
        "Server/Endpoints/IngredientsEndpoints.cs",
        "public static class IngredientsEndpoints { }"
    )
    result = check(inp)
    assert len(result) == 1


def test_public_class_in_dtos_is_violation():
    inp = make_input(
        "Server/Dtos/CreateIngredientDto.cs",
        "public record CreateIngredientDto(string Name);"
    )
    result = check(inp)
    assert len(result) == 1


def test_multiple_public_types_reports_each():
    inp = make_input(
        "Server/Domain/Foo.cs",
        "public class A { }\npublic record B(int X);"
    )
    result = check(inp)
    assert len(result) == 2


# ── No violations ─────────────────────────────────────────────────────────────

def test_internal_type_is_ok():
    inp = make_input(
        "Server/Domain/Ingredient.cs",
        "internal readonly record struct Ingredient { }"
    )
    assert check(inp) == []


def test_file_scoped_type_is_ok():
    inp = make_input(
        "Server/Endpoints/IngredientsEndpoints.cs",
        "file static class IngredientMappings { }"
    )
    assert check(inp) == []


def test_infrastructure_public_type_is_ok():
    inp = make_input(
        "Infrastructure/DatabaseTypes/IngredientDbType.cs",
        "public class IngredientDbType { }"
    )
    assert check(inp) == []


def test_test_file_is_ignored():
    inp = make_input(
        "Server.Tests/IngredientsEndpointsTests.cs",
        "public class IngredientsEndpointsTests { }",
        is_test=True,
    )
    assert check(inp) == []


def test_non_cs_file_is_ignored():
    inp = make_input(
        "Server/Domain/foo.ts",
        "export class Foo { }"
    )
    assert check(inp) == []


def test_comment_with_public_is_not_flagged():
    inp = make_input(
        "Server/Domain/Ingredient.cs",
        "// public class OldIngredient – removed\ninternal readonly record struct Ingredient { }"
    )
    assert check(inp) == []


def test_public_property_inside_internal_type_is_not_flagged():
    inp = make_input(
        "Server/Domain/Ingredient.cs",
        "internal readonly record struct Ingredient\n{\n    public string Name { get; init; }\n}"
    )
    assert check(inp) == []
