"""Tests für checks/throw_check.py – nur C# (TypeScript via ESLint + Review-Checkliste)"""
from conftest import make_input
from checks import throw_check

CS_FILE = "Server/Foo.cs"
CS_TEST = "Server.Tests/FooTests.cs"


# --- blockiert ---

def test_cs_argument_exception_blocked():
    inp = make_input(CS_FILE, 'throw new ArgumentException("x")')
    assert throw_check.check(inp) != []


# --- erlaubt ---

def test_cs_invalid_operation_exception_allowed():
    inp = make_input(CS_FILE, 'throw new InvalidOperationException("x")')
    assert throw_check.check(inp) == []

def test_cs_test_file_not_blocked():
    inp = make_input(CS_TEST, 'throw new ArgumentException("x")')
    assert throw_check.check(inp) == []
