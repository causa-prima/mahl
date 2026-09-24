"""Tests, die im Mutantenbaum von mutmut prinzipiell nicht laufen können.

mutmut kopiert das Repo nach `mutants/` und instrumentiert jede Funktion mit einem
Trampolin, das seine Laufzeitkonfiguration braucht. Ein **Subprozess** erbt sie nicht und
stirbt an `'NoneType' object has no attribute 'max_stack_depth'` – und zwar bevor ein
einziger Mutant bewertet ist, weil mutmut seinen Stats-Lauf mit `-x` fährt.

Die Liste ist KEIN Freibrief: Jeder Eintrag kostet Mutationsabdeckung genau dort, wo er
steht. Aufgenommen wird nur, was sich nicht beheben lässt – ein Test, der den Subprozess als
ALTLAST startet, wird umgebaut (so geschehen bei `session-agenda.py` und dem
Bash-Permission-Runner in S129), nicht eingetragen.

Zwei Mechanismen halten sie ehrlich: `tests/conftest.py` wendet sie an und
`tests/test_mutmut_ausnahmen.py` prüft, dass kein Eintrag ins Leere zeigt; `mutmut-run.py`
nennt sie in jedem Verdikt, damit sie nicht still wächst.

Hier statt in `conftest.py`, weil beide Seiten dieselbe Quelle brauchen – der Wrapper darf
keinen Testcode importieren.
"""

UNTER_MUTMUT_UEBERSPRUNGEN: dict[str, str] = {
    "tests/test_session_agenda.py::test_die_cli_liefert_je_blockname_verschiedene_bloecke":
        "Der Subprozess IST hier der Prüfgegenstand: Der Test belegt, dass der Weg des "
        "Hooks (`python3 -m prozesscode.session-agenda --block <name>`) je Block einen "
        "anderen Text liefert – in-process aufgerufen prüfte er die Funktion statt die "
        "Wirkung, und genau diese Lücke hat er aufgedeckt.",
    **{
        f"tests/test_erfassung_cli.py::test_add_verlangt_den_aufschubgrund[{modul}]":
            "Der Subprozess IST der Prüfgegenstand: Der Test belegt, dass die CLI das Pflichtfeld "
            "Aufschubgrund verlangt (LL-S128-1: getestete Funktion, unverdrahtete CLI). Den "
            "Kern prüfen die in-process-Tests der Eintragsmodule und Hooks."
        for modul in ("obs", "td", "oq")
    },
    "tests/test_aufrufpfad_wrapper.py::test_stryker_guard_suite_ist_gruen":
        "Die Suite prüft `resolve_mutate` gegen die echten Verzeichnisse Server/ und Client/; "
        "mutmut kopiert sie nicht in den Mutantenbaum (`also_copy` in setup.cfg – Client/ "
        "brächte node_modules mit). Außerhalb von mutmut läuft der Test im Werkzeug-Gate.",
}
