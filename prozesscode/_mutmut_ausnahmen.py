"""Tests, die im Mutantenbaum von mutmut prinzipiell nicht laufen können.

mutmut kopiert das Repo nach `mutants/` und lässt die Suite dort laufen – aber nur mit
dem, was `also_copy` in `setup.cfg` mitnimmt. Ein Test, der etwas außerhalb davon braucht,
scheitert dort, und zwar bevor ein einziger Mutant bewertet ist, weil mutmut seinen
Stats-Lauf mit `-x` fährt. Subprozess-Tests gehören seit mutmut 3.8 nicht mehr dazu: Sie
laufen im Baum durch.

Die Liste ist KEIN Freibrief: Jeder Eintrag kostet Mutationsabdeckung genau dort, wo er
steht. Aufgenommen wird nur, was sich nicht beheben lässt.

Zwei Mechanismen halten sie ehrlich: `tests/conftest.py` wendet sie an und
`tests/test_mutmut_ausnahmen.py` prüft, dass kein Eintrag ins Leere zeigt; `mutmut-run.py`
nennt sie in jedem Verdikt, damit sie nicht still wächst.

Hier statt in `conftest.py`, weil beide Seiten dieselbe Quelle brauchen – der Wrapper darf
keinen Testcode importieren.
"""

UNTER_MUTMUT_UEBERSPRUNGEN: dict[str, str] = {
    "tests/test_aufrufpfad_wrapper.py::test_stryker_guard_suite_ist_gruen":
        "Die Suite prüft `resolve_mutate` gegen die echten Verzeichnisse Server/ und Client/; "
        "mutmut kopiert sie nicht in den Mutantenbaum (`also_copy` in setup.cfg – Client/ "
        "brächte node_modules mit). Außerhalb von mutmut läuft der Test im Werkzeug-Gate.",
}
