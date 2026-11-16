"""Tests für check-code-quality-blocking.py – Einstieg über den Dispatcher-Weg.

Die einzelnen Regeln (throw, ROP, Immutability, Primitives) haben eigene Tests unter
`checks/`. Hier steht nur, dass `check(payload)` sie tatsächlich erreicht und blockt.
"""
from importlib import import_module

import pytest

from prozesscode.hooks.checks import guard_log

hook = import_module("prozesscode.hooks.check-code-quality-blocking")


def _write(pfad, inhalt):
    return {"tool_name": "Write", "tool_input": {"file_path": pfad, "content": inhalt}}


@pytest.mark.aufrufpfad("check-code-quality-blocking")
def test_throw_im_produktionscode_blockt():
    grund = hook.check(_write("Server/Domain/Beispiel.cs",
                              "public static class B { public static void F() "
                              "{ throw new Exception(\"x\"); } }\n"))
    assert grund and "throw" in grund


def test_unsichtbares_zeichen_in_einem_test_blockt():
    """Aufrufpfad für checks/unsichtbare_zeichen: registriert und über check() erreichbar."""
    grund = hook.check(_write("Client/src/pages/X.test.tsx", "const a = '" + chr(0x200B) + "'\n"))
    assert grund and "U+200B" in grund


def test_derselbe_code_im_test_passiert():
    """Gegenprobe: Tests sind ausgenommen – der Block oben liegt an der Regel, nicht am Text."""
    assert hook.check(_write("Server.Tests/BeispielTests.cs",
                             "public class T { void F() { throw new Exception(\"x\"); } }\n")) is None


def test_jeder_anschlagende_teilcheck_steht_unter_eigenem_namen_im_protokoll(monkeypatch):
    """Der Dispatcher zählt nur „check-code-quality-blocking". Ohne Teilcheck-Namen bliebe
    unsichtbar, welche der Regeln je angeschlagen hat – ein kaputter Teilcheck fiele nie auf."""
    # Given – zwei schlagen an, einer nicht; der Name hängt am Modul, also drei verschiedene
    for fn, modul in ((_meldet_a, "erster"), (_still, "zweiter"), (_meldet_b, "dritter")):
        monkeypatch.setattr(fn, "__module__", "prozesscode.hooks.checks." + modul)
    monkeypatch.setattr(hook, "CHECKS", [_meldet_a, _still, _meldet_b])
    # When
    hook.check(_write("Server/Domain/Beispiel.cs", "class B {}\n"))
    # Then
    assert guard_log.zaehlstand() == {hook.teilcheck_name(_meldet_a): 1,
                                      hook.teilcheck_name(_meldet_b): 1}


def test_teilcheck_name_ist_praefix_plus_kurzer_modulname():
    """Protokollschlüssel sind Verhalten: Ein geänderter Name hinterließe die alten
    Auslösungen als „nicht mehr definiert" und begänne die Zählung neu."""
    from prozesscode.hooks.checks import rop
    assert hook.teilcheck_name(rop.check) == "blockierend:rop"


def test_teilcheck_namen_sind_eindeutig_und_kollidieren_nicht_mit_den_hinweisen():
    """`primitives` steht in beiden Dispatchern; unter demselben Namen flössen die
    Auslösungen beider in eine Zahl."""
    hinweise = import_module("prozesscode.hooks.check-code-quality-nonblocking")
    namen = [hook.teilcheck_name(fn) for fn in hook.CHECKS]
    assert len(set(namen)) == len(hook.CHECKS)
    assert not set(namen) & {fn.__module__.rsplit(".", 1)[-1] for fn in hinweise.CHECKS}


def _meldet_a(_inp):
    return ["A"]


def _meldet_b(_inp):
    return ["B"]


def _still(_inp):
    return []


def _kaputt(_inp):
    raise ValueError("Regel kaputt")


def test_mehrere_befunde_getrennt_und_eine_kaputte_regel_gemeldet(monkeypatch, capsys):
    """Die übrigen Regeln laufen weiter; die kaputte steht mit Modul und Fehler in stderr."""
    monkeypatch.setattr(hook, "CHECKS", [lambda _inp: ["A"], _kaputt, lambda _inp: ["B"]])
    grund = hook.check(_write("Server/Domain/Beispiel.cs", "class B {}\n"))
    assert grund == "A" + hook._TRENNER + "B\n" + hook.BLOCKING_DISCUSSION_NOTE
    assert capsys.readouterr().err == (
        f"check-code-quality-blocking: Fehler in {_kaputt.__module__}: Regel kaputt\n")
