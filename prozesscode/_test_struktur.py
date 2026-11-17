"""Gliederungsregel für Komponenten-, Integrations- und Unit-Tests: `// Given`, `// When`, `// Then`.

Eine Quelle für zwei Prüfstellen: `check-test-spec-ref.py` prüft beim Schreiben eines neuen Tests,
`qa-check.py` beim Übergabelauf. Zwei getippte Kopien gingen beim nächsten Regelwechsel still
auseinander – die eine Stelle ließe durch, was die andere abweist.

Ein Marker gilt als vorhanden, wenn er als Teilstring in einer Zeile des Testrumpfs steht;
`// Given: die Zutat` zählt also, `// When / Then` dagegen nicht als `// Then`.
Guideline: CGC-/CGT-given-when-then.
"""
import re
from collections.abc import Sequence

GWT_MARKER = ("// Given", "// When", "// Then")

# Wegwerf-Probe – `*.probe.test.ts(x)` (etwa jsdom-Verhalten nachsehen) oder `*.probe.spec.ts` (etwa eine
# einmalige Messung im Browser): kein Test des Laufs. Dieselbe Quelle für alle Seiten der Ausnahme –
# check-test-spec-ref und check-e2e-scenario-ref lassen sie durch, qa-check bricht ab, solange eine liegt,
# .gitignore hält sie aus Commits heraus. Ein Muster je Seite liefe auseinander, und die Probe fiele durch
# die Lücke dazwischen.
PROBE_RE = re.compile(r"\.probe\.(?:test|spec)\.tsx?$")


def fehlende_gwt(zeilen: Sequence[str]) -> list[str]:
    """Die Marker, die in keiner Zeile des Testrumpfs stehen – in der Reihenfolge Given, When, Then."""
    return [m for m in GWT_MARKER if not any(m in z for z in zeilen)]
