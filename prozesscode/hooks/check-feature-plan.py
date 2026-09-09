#!/usr/bin/env python3
"""PreToolUse-Poka-Yoke (blockierend): Bauplan der Feature-Dateien (ADR-S131-1).

Prüft bei jedem Edit an `**/*.feature`, dass der Lauf-Bauplan auflösbar bleibt:
- jeder Lauf trägt eine Phase (Datei-Direktive `# @phase:` oder `· Phase:<P>` am Run-Tag),
- jede `braucht:`-Kante zeigt auf einen existierenden Lauf,
- keine Kante bildet einen Zyklus,
- Direktiven stehen im Feature-Header und tragen einen bekannten Phasen-Wert.

Warum als Hook und nicht nur in `next_run.py --check`: Alle vier Fälle sind still. Ein Lauf ohne
Phase wird nie fällig, eine tote Kante hält ihren Lauf dauerhaft zurück, ein Zyklus sperrt alle
Beteiligten – und nichts schlägt fehl, es kommt nur nie etwas. Der Guard fängt sie im Moment der
Entstehung, wo der Kontext noch da ist.

Abgrenzung zu `check-e2e-scenario-ref.py`: Der hält Feature-Titel und E2E-`// Szenario:`-Kommentare
deckungsgleich (Mapping Spec ↔ Test). Hier geht es um die Konsistenz *innerhalb* der
Feature-Dateien. Die PreToolUse-Mechanik (Post-Edit-Inhalt simulieren, Exit 2, fail-open) ist
dieselbe und dort beschrieben.
"""
import json
import re
import sys
from pathlib import Path

from .._feature import find_malformed_run_comments
from ..next_run import check_dependencies, collect_runs, run_label
from ._hook_io import edit_zustand

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_FEATURES_DIR = _REPO_ROOT / "features"
_FEATURE_RE = re.compile(r"\.feature$")


def is_feature(file_path: str) -> bool:
    return bool(_FEATURE_RE.search(file_path))


def _other_feature_texts(edited_path: str) -> list[str]:
    """Alle Feature-Dateien außer der gerade bearbeiteten.

    Nötig, weil eine `braucht:`-Kante über Dateigrenzen zeigen darf: Ob `US-904/run-8` existiert,
    lässt sich an der bearbeiteten Datei allein nicht entscheiden.
    """
    edited = Path(edited_path).name
    texts: list[str] = []
    if not _FEATURES_DIR.exists():
        return texts
    for path in sorted(_FEATURES_DIR.glob("**/*.feature")):
        if path.name == edited:
            continue
        try:
            texts.append(path.read_text(encoding="utf-8"))
        except OSError:
            continue
    return texts


def validate(post_content: str, other_feature_texts: list[str]) -> list[str]:
    """Verstöße im Bauplan nach dem Edit – Format-, Phasen- und Kanten-Fehler.

    Die bearbeitete Datei steht an Index 0; gemeldet wird nur, was einen **ihrer** Läufe betrifft.
    Sonst blockierte eine Altlast in einer unbeteiligten Datei jede Änderung an jeder anderen.
    """
    violations = list(find_malformed_run_comments(post_content))
    groups = collect_runs([post_content, *other_feature_texts])
    eigene = {run_label(g) for g in groups if g["file_index"] == 0}
    violations += [v for v in check_dependencies(groups) if any(label in v for label in eigene)]
    return violations


def check(data: dict) -> str | None:
    """Dispatcher-Einstieg: Blockier-Grund oder None. Siehe dispatch-edit-write.py.

    Fail-open (Exception → None) liegt beim Dispatcher, damit ein Hook-Fehler
    nie einen Edit blockiert.
    """
    zustand = edit_zustand(data)
    if zustand is None:
        return None
    file_path, _pre, post = zustand
    if not is_feature(file_path):
        return None

    violations = validate(post, _other_feature_texts(file_path))
    if not violations:
        return None

    lines = "\n".join(f"  - {v}" for v in violations)
    return (
        "❌ Feature-Bauplan (Poka-Yoke, ADR-S131-1):\n"
        f"{lines}\n"
        "  Jeder Lauf braucht eine Phase (`# @phase: <SKELETON|MVP|V1>` im Feature-Header oder\n"
        "  `· Phase:<P>` am `# @run-N`-Tag) und auflösbare `braucht:`-Kanten (`run-8` in derselben\n"
        "  Datei, `US-904/run-8` datei-übergreifend). Bestand prüfen:\n"
        "  python3 -m prozesscode.next_run --check"
    )


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:  # noqa: BLE001 – kein parsbarer Input → nichts blocken
        sys.exit(0)
    reason = check(data)
    if reason:
        print(reason, file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
