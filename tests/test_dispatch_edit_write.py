"""Tests für dispatch-edit-write.py – PreToolUse-Dispatcher für den Matcher Edit|Write.

Der Dispatcher ersetzt die sechs zuvor einzeln in settings.json registrierten Checks
(OBS-S088-1). Geprüft wird der Dispatcher-Vertrag, nicht die Check-Logik selbst –
die hat je Check eigene Tests.
"""
import io
import json
import sys
from importlib import import_module
from pathlib import Path

import pytest

from prozesscode.hooks.checks import guard_log

dispatcher = import_module("prozesscode.hooks.dispatch-edit-write")

REPO_ROOT = Path(__file__).resolve().parents[1]


# --- Vertrag: jedes registrierte Modul ist ladbar und bietet check() ----------
def test_every_registered_check_is_importable_and_has_check():
    for name in dispatcher.CHECKS:
        mod = import_module(dispatcher.PAKET + name)
        assert hasattr(mod, "check"), f"{name} hat keine check()-Funktion"
        assert callable(mod.check)


def test_every_hook_file_is_registered_somewhere():
    """Die Gegenrichtung zum Registry-Test unten – und die Lücke, durch die S131 fast rutschte.

    Der Registry-Test vergleicht `CHECKS` gegen eine feste Liste **im Test**: Legt jemand eine
    neue `check-*.py` an und registriert sie nirgends, bleiben beide konsistent und nichts wird
    rot. Ein Guard ohne Aufrufer prüft nichts, und sein Ausfall löst per Definition nichts aus –
    von außen ist er nicht von einem zu unterscheiden, der nur nie angeschlagen hat.

    Zwei Registrierungsorte, weil es zwei Aufrufwege gibt: der Dispatcher (`CHECKS`) für
    Edit|Write, und `settings.json` direkt für alles andere (Bash-Permission, PostToolUse).
    """
    settings = (REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8")
    hooks = sorted((REPO_ROOT / "prozesscode" / "hooks").glob("check-*.py"))
    unregistriert = [p.stem for p in hooks
                     if p.stem not in dispatcher.CHECKS and p.stem not in settings]
    assert unregistriert == [], (
        f"Guard ohne Aufrufer: {unregistriert} – in dispatch-edit-write.CHECKS aufnehmen "
        f"oder in .claude/settings.json registrieren."
    )


def test_registry_covers_every_registered_check():
    # Regression: verhindert, dass ein Check bei einem Refactor still aus der
    # Liste fällt und damit wirkungslos wird, ohne dass etwas rot wird.
    assert set(dispatcher.CHECKS) == {
        "check-dependency-allowlist",
        "check-code-quality-blocking",
        "check-e2e-scenario-ref",
        "check-test-spec-ref",
        "check-feature-plan",
        "check-ref-direction",
        "check-obs-capture",
        "check-td-capture",
        "check-adr-capture",
        "check-oq-capture",
        "check-dangling-refs",
        "check-anchors",
        "check-ordinale",
    }


# --- Sammeln statt Abbrechen -------------------------------------------------
def test_collects_reasons_from_all_checks_not_only_the_first(monkeypatch):
    class FakeMod:
        def __init__(self, reason):
            self.reason = reason

        def check(self, data):
            return self.reason

    mods = {"a": FakeMod("Grund A"), "b": FakeMod(None), "c": FakeMod("Grund C")}
    monkeypatch.setattr(dispatcher, "CHECKS", ["a", "b", "c"])
    monkeypatch.setattr(dispatcher, "import_module",
                        lambda name: mods[name.removeprefix(dispatcher.PAKET)])

    assert dispatcher.collect_reasons({}) == ["Grund A", "Grund C"]


def test_ausgelassene_checks_laufen_nicht(monkeypatch):
    # // Given zwei anschlagende Checks
    class FakeMod:
        def __init__(self, reason):
            self.reason = reason

        def check(self, data):
            return self.reason

    mods = {"a": FakeMod("Grund A"), "c": FakeMod("Grund C")}
    monkeypatch.setattr(dispatcher, "CHECKS", ["a", "c"])
    monkeypatch.setattr(dispatcher, "import_module",
                        lambda name: mods[name.removeprefix(dispatcher.PAKET)])
    # // When einer davon ausdrücklich ausgelassen wird (tracker_diff bei --trotz-verweisen)
    # // Then meldet nur der andere
    assert dispatcher.collect_reasons({}, ohne=frozenset({"a"})) == ["Grund C"]


def test_eine_unbekannte_auslassung_wirft_statt_still_nichts_zu_tun(monkeypatch):
    # // Given eine Prüfkette ohne Check namens „check-vertippt“
    monkeypatch.setattr(dispatcher, "CHECKS", ["a"])
    # // When ein Aufrufer genau diesen auslassen will
    # // Then ist das ein Programmierfehler, der laut wird – sonst liefe die Auslassung ins Leere
    #   (zwei auf einmal: die Meldung nennt jeden, nicht nur den ersten)
    with pytest.raises(ValueError, match="check-auch-falsch, check-vertippt$"):
        dispatcher.collect_reasons({}, ohne=frozenset({"check-vertippt", "check-auch-falsch"}))


def test_no_reasons_when_all_checks_pass(monkeypatch):
    class Passing:
        def check(self, data):
            return None

    monkeypatch.setattr(dispatcher, "CHECKS", ["x"])
    monkeypatch.setattr(dispatcher, "import_module", lambda name: Passing())

    assert dispatcher.collect_reasons({}) == []


# --- Fail-open: ein defekter Check reißt die übrigen nicht mit ---------------
def test_broken_check_is_skipped_and_others_still_run(monkeypatch):
    class Broken:
        def check(self, data):
            raise RuntimeError("kaputt")

    class Working:
        def check(self, data):
            return "Grund W"

    mods = {"broken": Broken(), "working": Working()}
    monkeypatch.setattr(dispatcher, "CHECKS", ["broken", "working"])
    monkeypatch.setattr(dispatcher, "import_module",
                        lambda name: mods[name.removeprefix(dispatcher.PAKET)])

    # Der defekte Check darf weder blockieren noch den nachfolgenden verhindern.
    assert dispatcher.collect_reasons({}) == ["Grund W"]


def test_unimportable_check_is_skipped(monkeypatch):
    def raising_import(name):
        raise ImportError("gibt es nicht")

    monkeypatch.setattr(dispatcher, "CHECKS", ["fehlt"])
    monkeypatch.setattr(dispatcher, "import_module", raising_import)

    assert dispatcher.collect_reasons({}) == []


# --- Echte Checks: harmloser Edit wird nicht blockiert ------------------------
def test_real_checks_pass_on_an_unrelated_file():
    data = {
        "tool_name": "Edit",
        "tool_input": {
            "file_path": "/tmp/irgendwas.txt",
            "old_string": "a",
            "new_string": "b",
        },
    }
    assert dispatcher.collect_reasons(data) == []


# --- main(): was bei Claude Code ankommt ---------------------------------------
class _Grund:
    def __init__(self, grund):
        self.grund = grund

    def check(self, data):
        return self.grund


def _main(monkeypatch, gruende: dict, stdin: str) -> int:
    monkeypatch.setattr(dispatcher, "CHECKS", list(gruende))
    monkeypatch.setattr(dispatcher, "import_module",
                        lambda name: _Grund(gruende[name.removeprefix(dispatcher.PAKET)]))
    monkeypatch.setattr(sys, "stdin", io.StringIO(stdin))
    try:
        dispatcher.main()
    except SystemExit as ende:
        return ende.code
    return 0


@pytest.mark.parametrize("werkzeug", ["Edit", "Write"])
def test_main_gibt_alle_gruende_als_deny_im_hook_format_aus(monkeypatch, capsys, werkzeug):
    code = _main(monkeypatch, {"a": "Grund A", "b": None, "c": "Grund C"},
                 json.dumps({"tool_name": werkzeug, "tool_input": {}}))
    assert code == 0  # Den Block trägt das JSON, nicht der Exit-Code.
    assert json.loads(capsys.readouterr().out) == {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": "Grund A\n" + "─" * 60 + "\nGrund C",
    }}


@pytest.mark.parametrize("stdin, grund", [
    (json.dumps({"tool_name": "Read", "tool_input": {}}), "Grund A"),  # anderes Werkzeug
    (json.dumps({"tool_input": {}}), "Grund A"),                       # ohne Werkzeugnamen
    ("kein JSON", "Grund A"),
    (json.dumps({"tool_name": "Edit", "tool_input": {}}), None),       # kein Einwand
])
def test_main_ohne_einwand_gibt_nichts_aus(monkeypatch, capsys, stdin, grund):
    assert _main(monkeypatch, {"a": grund}, stdin) == 0
    assert capsys.readouterr().out == ""


def test_fehler_eines_checks_geht_mit_namen_auf_stderr(monkeypatch, capsys):
    def wirft(name):
        raise ImportError("gibt es nicht")

    monkeypatch.setattr(dispatcher, "CHECKS", ["check-fehlt"])
    monkeypatch.setattr(dispatcher, "import_module", wirft)
    dispatcher.collect_reasons({})
    assert capsys.readouterr().err == (
        "dispatch-edit-write: Fehler in check-fehlt (gibt es nicht) – Check übersprungen.\n")


def test_protokolliert_den_blockierenden_check(monkeypatch):
    monkeypatch.setattr(dispatcher, "CHECKS", ["check-still", "check-blockt"])
    monkeypatch.setattr(dispatcher, "import_module", lambda name: _Grund(
        "Grund" if name.endswith("blockt") else None))
    dispatcher.collect_reasons({})
    assert guard_log.zaehlstand() == {"check-blockt": 1}
