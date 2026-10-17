#!/usr/bin/env python3
"""PreToolUse-Poka-Yoke: keine neue selbstvergebene Gliederungsnummer.

Warum (S124): Die Anker-Migration (OBS-S112-7) ersetzte „Schritt 5" flächendeckend durch Namen,
weil die Nummer eine **zweite, ungeprüfte Adresse** neben dem Anker ist – sie wird bei
Umsortierung still falsch. Zwei bereits tote Verweise lagen im Bestand („kaizen Schritt 5" für
einen Schritt 7, „Script-Output Abschnitt 9" ohne Entsprechung). Danach hielt nichts den
Zustand: Nichts hinderte den nächsten Edit daran, wieder eine Nummer zu vergeben. Dieser Hook
tut es – dieselbe Bauform wie `check-anchors.py`, dessen Migration er absichert.

Blockierend sind nummerierte Überschrift, Nummer im Verweistext und ordinaler Absatz-Lead.
Mengenangaben („alle vier Agenten") erkennt `ordinale.py` ebenfalls, gemeldet werden sie aber
nicht hier, sondern als Warnung nach dem Edit (`checks/mengenangaben.py`): Zum Blocken sind sie
zu selten echt (S133 gesichtet), und ein PreToolUse-Hook kann nur blocken oder schweigen.

Geprüft werden nur hinzugekommene Zeilen: Der Bestand enthält legitime Altfälle, und ein Edit
an einer solchen Datei darf nicht kollateral blockieren.

Zeilen-Ausnahme: `ordinal-ok` in der Zeile.
Mechanik: PreToolUse läuft VOR der Anwendung; der Hook simuliert den Post-Edit-Inhalt.
Fail-open: ein Hook-eigener Fehler blockt nie einen Edit.
"""
from pathlib import Path


from ._hook_io import edit_zustand
from .. import anchors, ordinale

_MAX_HITS = 10
_MAX_ZEICHEN = 110  # je zitierter Zeile

_KOPF = "❌ Gliederungsnummer (Poka-Yoke): neue selbstvergebene Nummer/Buchstabe:\n"
_HINWEIS = (
    "  Eine Nummer ist eine zweite Adresse neben dem Anker – nur der Anker wird geprüft, "
    "die Nummer wird bei Umsortierung still falsch (S124: zwei tote Verweise im Bestand).\n"
    "  Nimm den Namen: `## Findings präsentieren` statt `## 5. Findings`, "
    "`[Findings präsentieren](#KZN-…)` statt `[Schritt 5](#KZN-…)`.\n"
    "  Fremdbestimmte Nummerierung (RFC-Abschnitt o.ä.) oder bewusster Einzelfall → "
    "`ordinal-ok` in die Zeile."
)


def _rel(file_path: str) -> str | None:
    try:
        return Path(file_path).resolve().relative_to(anchors.REPO_ROOT).as_posix()
    except ValueError:
        return None


def _zustaendig(file_path: str) -> bool:
    """Geht diese Datei den Hook an? Entschieden am PFAD, vor dem Lesen der Datei.

    Zweite Stufe derselben Regel wie im Bestandsprüfer: Wo die Muster Eingabedatum sind,
    blockiert der Hook nicht – sonst wäre jeder Edit an den Werkzeug-Tests gesperrt.
    """
    rel = _rel(file_path)
    if rel is None or not anchors.wird_geprueft(rel):
        return False
    return "ordinal" not in anchors.ausnahmen_fuer(rel)


def check(data: dict) -> str | None:
    """Dispatcher-Einstieg: Blockier-Grund oder None. Siehe dispatch-edit-write.py."""
    zustand = edit_zustand(data, _zustaendig)
    if zustand is None:
        return None
    file_path, pre, post = zustand

    rel = _rel(file_path)
    markdown = rel.endswith(".md")

    funde = ordinale.ordinale_in(
        ordinale._neu_hinzugekommen(pre, post), markdown=markdown)
    if not funde:
        return None

    zeilen = "\n".join(f"  - {art}: `{zeile[:_MAX_ZEICHEN]}`" for _nr, zeile, art in funde[:_MAX_HITS])
    return f"{_KOPF}{zeilen}\n{_HINWEIS}"
