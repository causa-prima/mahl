"""Tests für check-code-quality-blocking.py – Einstieg über den Dispatcher-Weg.

Die einzelnen Regeln (throw, ROP, Immutability, Primitives) haben eigene Tests unter
`checks/`. Hier steht nur, dass `check(payload)` sie tatsächlich erreicht und blockt.
"""
from importlib import import_module

import pytest

hook = import_module("prozesscode.hooks.check-code-quality-blocking")


def _write(pfad, inhalt):
    return {"tool_name": "Write", "tool_input": {"file_path": pfad, "content": inhalt}}


@pytest.mark.aufrufpfad("check-code-quality-blocking")
def test_throw_im_produktionscode_blockt():
    grund = hook.check(_write("Server/Domain/Beispiel.cs",
                              "public static class B { public static void F() "
                              "{ throw new Exception(\"x\"); } }\n"))
    assert grund and "throw" in grund


def test_derselbe_code_im_test_passiert():
    """Gegenprobe: Tests sind ausgenommen – der Block oben liegt an der Regel, nicht am Text."""
    assert hook.check(_write("Server.Tests/BeispielTests.cs",
                             "public class T { void F() { throw new Exception(\"x\"); } }\n")) is None
