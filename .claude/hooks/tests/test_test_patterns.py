"""Tests für checks/test_patterns.py"""
from conftest import make_input
from checks import test_patterns

TEST_FILE = "/Server.Tests/FooTests.cs"
NON_TEST_FILE = "Server/Foo.cs"


# --- blockiert ---

def test_have_count_blocked():
    inp = make_input(TEST_FILE, "items.Should().HaveCount(1)", old_content="")
    assert test_patterns.check(inp) != []

def test_contain_single_blocked():
    inp = make_input(TEST_FILE, "items.Should().ContainSingle()", old_content="")
    assert test_patterns.check(inp) != []

def test_have_count_write_blocked():
    inp = make_input(TEST_FILE, "items.Should().HaveCount(1)", tool="Write")
    assert test_patterns.check(inp) != []


# --- erlaubt ---

def test_no_new_occurrences_allowed():
    # Delta = 0: Gleicher Inhalt in old und new
    content = "items.Should().HaveCount(1)"
    inp = make_input(TEST_FILE, content, old_content=content)
    assert test_patterns.check(inp) == []

def test_non_test_file_not_blocked():
    inp = make_input(NON_TEST_FILE, "items.Should().HaveCount(1)", old_content="")
    assert test_patterns.check(inp) == []


# --- ExcludingMissingMembers ---

def test_excluding_missing_members_blocked():
    inp = make_input(TEST_FILE, "o => o.ExcludingMissingMembers()", old_content="")
    assert test_patterns.check(inp) != []

def test_excluding_missing_members_write_blocked():
    inp = make_input(TEST_FILE, "o => o.ExcludingMissingMembers()", tool="Write")
    assert test_patterns.check(inp) != []

def test_excluding_missing_members_no_new_occurrence_allowed():
    content = "o => o.ExcludingMissingMembers()"
    inp = make_input(TEST_FILE, content, old_content=content)
    assert test_patterns.check(inp) == []

def test_excluding_missing_members_non_test_file_allowed():
    inp = make_input(NON_TEST_FILE, "o => o.ExcludingMissingMembers()", old_content="")
    assert test_patterns.check(inp) == []

def test_excluding_property_allowed():
    # Excluding(x => x.Id) ist explizit und erlaubt
    inp = make_input(TEST_FILE, "o => o.Excluding(x => x.Id)", old_content="")
    assert test_patterns.check(inp) == []


# --- Should().Contain() ---

def test_contain_blocked():
    inp = make_input(TEST_FILE, 'body.Should().Contain("Butter")', old_content="")
    assert test_patterns.check(inp) != []

def test_contain_write_blocked():
    inp = make_input(TEST_FILE, 'body.Should().Contain("message")', tool="Write")
    assert test_patterns.check(inp) != []

def test_contain_no_new_occurrence_allowed():
    content = 'body.Should().Contain("Butter")'
    inp = make_input(TEST_FILE, content, old_content=content)
    assert test_patterns.check(inp) == []
