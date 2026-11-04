"""Die beiden Code-Quality-Dispatcher teilen sich keinen Check.

Der blockierende läuft über `dispatch-edit-write` VOR dem Schreiben, der nicht-blockierende
danach. Ein Check in beiden Listen ist im zweiten unerreichbar: Ein Verstoß wird vorne
abgewiesen, die Datei nie geschrieben – hinten sieht er ihn nie. Die Guard-Statistik meldet ihn
dann als „nie gefeuert", und jede Retro prüft einen Guard, der nicht kaputt, nur tot ist.
"""
from importlib import import_module


def _checks(modul: str) -> set:
    return set(import_module(f"prozesscode.hooks.{modul}").CHECKS)


def test_kein_check_steht_in_beiden_dispatchern():
    # Given
    blockierend = _checks("check-code-quality-blocking")
    hinweisend = _checks("check-code-quality-nonblocking")
    # When
    doppelt = {f.__module__ for f in blockierend & hinweisend}
    # Then
    assert doppelt == set()
