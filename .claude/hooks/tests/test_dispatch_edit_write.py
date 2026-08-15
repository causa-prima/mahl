"""Tests für dispatch-edit-write.py – PreToolUse-Dispatcher für den Matcher Edit|Write.

Der Dispatcher ersetzt die sechs zuvor einzeln in settings.json registrierten Checks
(OBS-S088-1). Geprüft wird der Dispatcher-Vertrag, nicht die Check-Logik selbst –
die hat je Check eigene Tests.
"""
import os
import sys
from importlib import import_module

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
dispatcher = import_module("dispatch-edit-write")


# --- Vertrag: jedes registrierte Modul ist ladbar und bietet check() ----------
def test_every_registered_check_is_importable_and_has_check():
    for name in dispatcher.CHECKS:
        mod = import_module(name)
        assert hasattr(mod, "check"), f"{name} hat keine check()-Funktion"
        assert callable(mod.check)


def test_registry_covers_every_registered_check():
    # Regression: verhindert, dass ein Check bei einem Refactor still aus der
    # Liste fällt und damit wirkungslos wird, ohne dass etwas rot wird.
    assert set(dispatcher.CHECKS) == {
        "check-dependency-allowlist",
        "check-code-quality-blocking",
        "check-index-length",
        "check-e2e-scenario-ref",
        "check-ref-direction",
        "check-obs-capture",
        "check-td-capture",
        "check-adr-capture",
        "check-oq-capture",
        "check-dangling-refs",
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
    monkeypatch.setattr(dispatcher, "import_module", lambda name: mods[name])

    assert dispatcher.collect_reasons({}) == ["Grund A", "Grund C"]


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
    monkeypatch.setattr(dispatcher, "import_module", lambda name: mods[name])

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
