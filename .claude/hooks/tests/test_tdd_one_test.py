"""Tests für checks/tdd_one_test.py"""
from conftest import make_input
from checks import tdd_one_test

TEST_FILE = "Server.Tests/FooTests.cs"
NON_TEST_FILE = "Server/Foo.cs"
# Relativer Pfad → existiert nicht auf Disk → OSError-Fallback (existing="")
# Muss _IS_TEST_FILE matchen: \.Tests\b.*\.cs$
NONEXISTENT_TEST_FILE = "Server.Tests/NonExistentFile.cs"


# --- blockiert ---

def test_two_tests_added_blocked():
    content = "[Test]\npublic async Task A(){}\n[Test]\npublic async Task B(){}"
    inp = make_input(TEST_FILE, content, old_content="")
    assert tdd_one_test.check(inp) != []

def test_two_testcases_added_blocked():
    content = '[TestCase("")]\n[TestCase("x")]\npublic async Task A(string x){}'
    inp = make_input(TEST_FILE, content, old_content="")
    assert tdd_one_test.check(inp) != []

def test_two_tests_write_blocked():
    content = "[Test]\npublic async Task A(){}\n[Test]\npublic async Task B(){}"
    inp = make_input(NONEXISTENT_TEST_FILE, content, tool="Write")
    assert tdd_one_test.check(inp) != []


# --- erlaubt ---

def test_one_test_added_allowed():
    content = "[Test]\npublic async Task A(){}"
    inp = make_input(TEST_FILE, content, old_content="")
    assert tdd_one_test.check(inp) == []

def test_one_testcase_added_allowed():
    content = '[TestCase("")]\npublic async Task A(string x){}'
    inp = make_input(TEST_FILE, content, old_content="")
    assert tdd_one_test.check(inp) == []

def test_replace_existing_test_allowed():
    # Delta = 0: Ein Test ersetzt einen anderen
    old = "[Test]\npublic async Task A(){}"
    new = "[Test]\npublic async Task B(){}"
    inp = make_input(TEST_FILE, new, old_content=old)
    assert tdd_one_test.check(inp) == []

def test_non_test_file_not_blocked():
    content = "[Test]\npublic async Task A(){}\n[Test]\npublic async Task B(){}"
    inp = make_input(NON_TEST_FILE, content, old_content="")
    assert tdd_one_test.check(inp) == []
