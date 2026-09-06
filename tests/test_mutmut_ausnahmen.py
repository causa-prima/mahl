"""Tests für die mutmut-Ausnahmeliste in conftest.py.

Die Liste nimmt Tests aus, die im Mutantenbaum von mutmut prinzipiell nicht laufen können.
Jeder Eintrag kostet Mutationsabdeckung genau dort, wo er steht – die Tests hier sind das
Gegengewicht: Sie belegen, dass die Ausnahme nur unter mutmut greift und dass kein Eintrag
ins Leere zeigt. Eine Ausnahme, die niemand mehr prüft, wird zur Formalie (OBS-S112-8).
"""
import pathlib

import conftest


class _Item:
    """Minimales Stand-in für ein pytest-Item – mehr braucht der Mechanismus nicht."""

    def __init__(self, nodeid: str) -> None:
        self.nodeid = nodeid
        self.marker = []

    def add_marker(self, marker) -> None:
        self.marker.append(marker)


EIN_EINTRAG = next(iter(conftest.UNTER_MUTMUT_UEBERSPRUNGEN))


def test_ohne_mutmut_greift_die_ausnahme_nicht(monkeypatch):
    """Im normalen Lauf muss jeder gelistete Test ganz normal laufen."""
    monkeypatch.delenv("MUTANT_UNDER_TEST", raising=False)
    item = _Item(EIN_EINTRAG)
    conftest.pytest_collection_modifyitems(None, [item])
    assert item.marker == []


def test_unter_mutmut_wird_der_gelistete_test_uebersprungen(monkeypatch):
    monkeypatch.setenv("MUTANT_UNDER_TEST", "stats")
    item = _Item(EIN_EINTRAG)
    conftest.pytest_collection_modifyitems(None, [item])
    assert len(item.marker) == 1


def test_unter_mutmut_bleibt_alles_andere_unberuehrt(monkeypatch):
    """GEGENPROBE: Die Ausnahme darf nicht die halbe Suite stilllegen."""
    monkeypatch.setenv("MUTANT_UNDER_TEST", "stats")
    item = _Item("tests/test_anchors.py::test_irgendwas_anderes")
    conftest.pytest_collection_modifyitems(None, [item])
    assert item.marker == []


def test_jeder_eintrag_zeigt_auf_einen_existierenden_test():
    """Ein Eintrag ohne Ziel ist eine tote Ausnahme – sie erklärt eine Lücke, die es
    nicht mehr gibt, und verdeckt beim nächsten Lesen die Frage, ob sie noch nötig ist."""
    tests_dir = pathlib.Path(__file__).parent
    for nodeid in conftest.UNTER_MUTMUT_UEBERSPRUNGEN:
        datei, _, testname = nodeid.partition("::")
        pfad = tests_dir / pathlib.Path(datei).name
        assert pfad.is_file(), f"{nodeid}: Datei {datei} gibt es nicht"
        assert f"def {testname}(" in pfad.read_text(encoding="utf-8"), \
            f"{nodeid}: Test {testname} gibt es nicht mehr"


def test_jeder_eintrag_traegt_eine_begruendung():
    for nodeid, grund in conftest.UNTER_MUTMUT_UEBERSPRUNGEN.items():
        assert len(grund) > 40, f"{nodeid}: Begründung zu knapp für eine spätere Prüfung"
