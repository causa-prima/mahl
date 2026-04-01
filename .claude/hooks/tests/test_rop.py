"""Tests für checks/rop.py"""
from conftest import make_input
from checks import rop

CS_ENDPOINT = "Server/Endpoints/Foo.cs"
CS_TEST = "Server.Tests/FooTests.cs"
TS_FILE = "Client/src/foo.ts"


# --- blockiert ---

def test_cs_isT0_blocked():
    inp = make_input(CS_ENDPOINT, "if (result.IsT0)")
    assert rop.check(inp) != []

def test_cs_asT1_blocked():
    inp = make_input(CS_ENDPOINT, "var x = result.AsT1;")
    assert rop.check(inp) != []

def test_cs_asT0_write_blocked():
    inp = make_input(CS_ENDPOINT, "result.AsT0", tool="Write")
    assert rop.check(inp) != []

def test_ts_isOk_blocked():
    inp = make_input(TS_FILE, "if (result.isOk())")
    assert rop.check(inp) != []


# --- erlaubt ---

def test_cs_test_file_not_blocked():
    inp = make_input(CS_TEST, "if (result.IsT0)")
    assert rop.check(inp) == []
