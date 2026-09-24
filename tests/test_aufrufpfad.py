"""Meta-Test: Jedes Werkzeug unter prozesscode/ hat einen Test über seinen ECHTEN Aufrufpfad.

Warum (LL-S128-1, CM-S133-1): 59 grüne Tests prüften eine Funktion, deren CLI-Parameter nie
verdrahtet war – der Hook ruft die Hülle, nicht den Kern. In S133 gemessen hatten rund 40 der
51 Werkzeuge keinen einzigen Test über den Weg, auf dem sie im Alltag aufgerufen werden.

Der echte Pfad je Klasse:
  - Hook im Edit-Dispatcher → `check(payload)`, denn so ruft der Dispatcher
  - alles andere (Kommandozeile, direkt registrierter Hook) → `main(...)` oder Prozessstart

Ein solcher Test DEKLARIERT sich: `@pytest.mark.aufrufpfad("obs", "td")`. Eine Heuristik über
den Testcode hätte f-Strings, Aliase und Hilfsfunktionen übersehen (in S133 passiert); der Marker
ist eindeutig. Damit er nicht nur behauptet, prüft dieser Test zusätzlich, dass der markierte
Test den Pfad wirklich aufruft.

Ausnahmen nur mit Grund in AUSNAHMEN – Ziel ist eine leere Liste (User-Vorgabe S133: auch die
Test-Wrapper, weil sie für die Entwicklung entscheidend sind).
"""
import ast
from importlib import import_module
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TESTS = Path(__file__).resolve().parent

AUSNAHMEN: dict[str, str] = {}


def werkzeuge(paket: Path = ROOT / "prozesscode") -> list[str]:
    """Jedes Modul mit eigenem Einstieg – Dateiname ohne Endung, Hooks eingeschlossen."""
    dateien = list(paket.glob("*.py")) + list(paket.glob("hooks/*.py"))
    return sorted(p.stem for p in dateien
                  if '__name__ == "__main__"' in p.read_text(encoding="utf-8"))


def dispatch_hooks() -> set[str]:
    return set(import_module("prozesscode.hooks.dispatch-edit-write").CHECKS)


def _funktionen(baum: ast.Module) -> dict[str, ast.FunctionDef]:
    return {k.name: k for k in baum.body if isinstance(k, ast.FunctionDef)}


GEMEINSAME_HELFER = _funktionen(ast.parse((TESTS / "conftest.py").read_text(encoding="utf-8")))


def _aufrufpfad_marker(knoten: ast.FunctionDef) -> list[str] | None:
    for deko in knoten.decorator_list:
        if (isinstance(deko, ast.Call) and isinstance(deko.func, ast.Attribute)
                and deko.func.attr == "aufrufpfad"):
            return [a.value for a in deko.args if isinstance(a, ast.Constant)]
    return None


def markierte_tests(quellen: dict[str, str]) -> list[tuple[str, list[ast.AST], list[str]]]:
    """(Testname, Syntaxknoten, deklarierte Werkzeuge) je markiertem Test.

    Die Knoten umfassen die Hilfsfunktionen, die der Test ruft – aus derselben Datei oder aus
    `conftest.py`: `_lauf(tmp_path, …)` ruft `main()` für ihn, und das ist der übliche Aufbau.
    """
    treffer = []
    for datei, quelle in quellen.items():
        baum = ast.parse(quelle)
        helfer = {**GEMEINSAME_HELFER, **_funktionen(baum)}
        for knoten in ast.walk(baum):
            namen = isinstance(knoten, ast.FunctionDef) and _aufrufpfad_marker(knoten)
            if not namen:
                continue
            gerufen = {c.func.id for c in ast.walk(knoten)
                       if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)}
            teile = [knoten] + [helfer[n] for n in sorted(gerufen & helfer.keys())]
            treffer.append((f"{datei}::{knoten.name}", teile, namen))
    return treffer


def ruft_den_pfad(knoten: list[ast.AST], ist_dispatch_hook: bool) -> bool:
    """Ob ein echter Aufruf-Knoten des Pfads vorkommt – `x.check(…)` beim Dispatcher-Hook,
    sonst `x.main(…)` oder `subprocess.run(…)`. Syntaxbaum statt Textsuche: Ein
    auskommentiertes `# modul.main(…)` ist kein Aufruf (Auditor-Befund S133)."""
    gesucht = {"check"} if ist_dispatch_hook else {"main", "run"}
    return any(isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)
               and c.func.attr in gesucht
               and (c.func.attr != "run" or getattr(c.func.value, "id", "") == "subprocess")
               for teil in knoten for c in ast.walk(teil))


def _abdeckung() -> dict[str, list[str]]:
    quellen = {p.name: p.read_text(encoding="utf-8") for p in TESTS.glob("test_*.py")}
    abgedeckt: dict[str, list[str]] = {}
    for name, _quelle, namen in markierte_tests(quellen):
        for werkzeug in namen:
            abgedeckt.setdefault(werkzeug, []).append(name)
    return abgedeckt


ABDECKUNG = _abdeckung()


@pytest.mark.parametrize("werkzeug", werkzeuge())
def test_werkzeug_hat_einen_test_ueber_den_echten_aufrufpfad(werkzeug):
    if werkzeug in AUSNAHMEN:
        pytest.skip(f"Ausnahme: {AUSNAHMEN[werkzeug]}")
    pfad = "check(payload)" if werkzeug in dispatch_hooks() else "main(...) oder Prozessstart"
    assert werkzeug in ABDECKUNG, (
        f"{werkzeug}: kein Test über den echten Aufrufpfad ({pfad}). Test schreiben und mit "
        f"@pytest.mark.aufrufpfad(\"{werkzeug}\") markieren – CGP-echtes-artefakt.")


def test_markierte_tests_rufen_den_pfad_wirklich():
    quellen = {p.name: p.read_text(encoding="utf-8") for p in TESTS.glob("test_*.py")}
    hooks = dispatch_hooks()
    falsch = [f"{name} ({', '.join(namen)})"
              for name, knoten, namen in markierte_tests(quellen)
              if not all(ruft_den_pfad(knoten, n in hooks) for n in namen)]
    assert not falsch, f"Marker ohne passenden Aufruf: {falsch}"


def test_marker_nennen_nur_existierende_werkzeuge():
    unbekannt = sorted(set(ABDECKUNG) - set(werkzeuge()))
    assert not unbekannt, f"Marker nennt kein Werkzeug mit Einstieg: {unbekannt}"


def test_ausnahmen_sind_weder_verwaist_noch_ueberholt():
    for werkzeug in AUSNAHMEN:
        assert werkzeug in werkzeuge(), f"Ausnahme {werkzeug}: Werkzeug gibt es nicht mehr"
        assert werkzeug not in ABDECKUNG, f"Ausnahme {werkzeug}: inzwischen gedeckt – streichen"


# --- Gegenprobe der Analyse selbst -------------------------------------------------
_BEISPIEL = '''
import pytest

@pytest.mark.aufrufpfad("obs")
def test_echt():
    modul.main(["add"])

@pytest.mark.aufrufpfad("td")
def test_nur_kern():
    td_entry.add("x")

def test_unmarkiert():
    modul.main([])

def _lauf(argv):
    return modul.main(argv)

@pytest.mark.aufrufpfad("oq")
def test_ueber_helfer():
    assert _lauf(["x"]) == 0

@pytest.mark.aufrufpfad("tracker")
def test_nur_im_kommentar():
    # modul.main(["x"]) – ein Kommentar ist kein Aufruf
    td_entry.add("x")
'''


def test_analyse_findet_nur_markierte_tests():
    namen = [n for _t, _q, n in markierte_tests({"t.py": _BEISPIEL})]
    assert namen == [["obs"], ["td"], ["oq"], ["tracker"]]


def test_analyse_erkennt_marker_ohne_aufruf():
    """Auditor-Befund S133: Die Textsuche hätte `# modul.main(` als Aufruf gewertet."""
    ergebnis = {n[0]: ruft_den_pfad(q, False) for _t, q, n in markierte_tests({"t.py": _BEISPIEL})}
    assert ergebnis == {"obs": True, "td": False, "oq": True, "tracker": False}


def test_dispatch_hook_braucht_check_statt_main():
    assert not ruft_den_pfad([ast.parse("hook.main()")], True)
    assert ruft_den_pfad([ast.parse("hook.check(payload)")], True)


def test_run_zaehlt_nur_als_prozessstart():
    """`runner.run()` ist kein Prozessstart – nur `subprocess.run(…)` ist einer."""
    assert not ruft_den_pfad([ast.parse("runner.run()")], False)
    assert ruft_den_pfad([ast.parse("subprocess.run(['x'])")], False)


def test_werkzeugsuche_findet_module_mit_einstieg(tmp_path):
    (tmp_path / "hooks").mkdir()
    (tmp_path / "mit.py").write_text('if __name__ == "__main__":\n    main()\n', encoding="utf-8")
    (tmp_path / "ohne.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "hooks" / "h.py").write_text('if __name__ == "__main__":\n    pass\n',
                                              encoding="utf-8")
    assert werkzeuge(tmp_path) == ["h", "mit"]
