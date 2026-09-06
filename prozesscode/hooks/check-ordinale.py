#!/usr/bin/env python3
"""PreToolUse-Poka-Yoke: keine neue selbstvergebene Gliederungsnummer.

Warum (S124): Die Anker-Migration (OBS-S112-7) ersetzte „Schritt 5" flächendeckend durch Namen,
weil die Nummer eine **zweite, ungeprüfte Adresse** neben dem Anker ist – sie wird bei
Umsortierung still falsch. Zwei bereits tote Verweise lagen im Bestand („kaizen Schritt 5" für
einen Schritt 7, „Script-Output Abschnitt 9" ohne Entsprechung). Danach hielt nichts den
Zustand: Nichts hinderte den nächsten Edit daran, wieder eine Nummer zu vergeben. Dieser Hook
tut es – dieselbe Bauform wie `check-anchors.py`, dessen Migration er absichert.

Zwei Klassen, bewusst verschieden scharf (Begründung in `ordinale.py`):
  - **blockierend**: nummerierte Überschrift, Nummer im Verweistext, ordinaler Absatz-Lead
  - **nur protokolliert**: Mengenangaben („alle vier Agenten") → `.claude/tmp/mengenangaben.log`

Der Log-Teil ist bewusst stumm. Am Bestand wären 65–75 % Fehlalarm, aber das misst den falschen
Gegenstand: Der Bestand ist über 124 Sessions gewachsen und besteht überwiegend aus
Code-Kommentaren, die selten neu entstehen. Was dieser Hook sieht, sind **neue** Zeilen, und
deren Quote ist unbekannt. Statt sie zu schätzen, sammelt das Log sie – nach ein paar Sessions
entscheidet die Messung, ob die Klasse scharf geschaltet wird oder rausfliegt.

Geprüft werden nur hinzugekommene Zeilen: Der Bestand enthält legitime Altfälle, und ein Edit
an einer solchen Datei darf nicht kollateral blockieren.

Zeilen-Ausnahme: `ordinal-ok` in der Zeile.
Mechanik: PreToolUse läuft VOR der Anwendung; der Hook simuliert den Post-Edit-Inhalt.
Exit 2 = blockieren. Fail-open: ein Hook-eigener Fehler blockt nie einen Edit.
"""
import json
import sys
from pathlib import Path


from ._hook_io import edit_zustand
from .. import anchors, ordinale

_LOG = Path(__file__).resolve().parent.parent / "tmp" / "mengenangaben.log"
_MAX_HITS = 10


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


def _ausschnitt(zeile: str, fund: str, breite: int = 160) -> str:
    """Fenster um die Fundstelle statt Zeilenanfang.

    Doku-Zeilen sind regelmäßig länger als das Log-Fenster; die ersten drei echten Einträge
    trugen deshalb nur Vorspann. Das Log existiert aber, um die Fehlalarmquote später zu
    beurteilen – und dafür ist die Umgebung des Treffers das Einzige, was zählt.
    """
    start = zeile.find(fund)
    if start < 0 or len(zeile) <= breite:
        return zeile[:breite]
    rand = max(0, (breite - len(fund)) // 2)
    links, rechts = max(0, start - rand), min(len(zeile), start + len(fund) + rand)
    return ("…" if links else "") + zeile[links:rechts] + ("…" if rechts < len(zeile) else "")


def _protokolliere(rel: str, funde: list[tuple[int, str, str]]) -> None:
    """Stumm sammeln. Ein Fehler hier darf den Edit nie verhindern (CM-S116-1)."""
    if not funde:
        return  # sonst legte `open("a")` ein leeres Log an und täuschte Aktivität vor
    try:
        _LOG.parent.mkdir(parents=True, exist_ok=True)
        with _LOG.open("a", encoding="utf-8") as f:
            for _nr, zeile, fund in funde:
                f.write(f"{rel}\t{fund}\t{_ausschnitt(zeile, fund)}\n")
    except OSError:
        pass


def check(data: dict) -> str | None:
    """Dispatcher-Einstieg: Blockier-Grund oder None. Siehe dispatch-edit-write.py."""
    zustand = edit_zustand(data, _zustaendig)
    if zustand is None:
        return None
    file_path, pre, post = zustand

    rel = _rel(file_path)
    markdown = rel.endswith(".md")
    _protokolliere(rel, ordinale.neue_mengenangaben(pre, post))

    funde = ordinale.ordinale_in(
        ordinale._neu_hinzugekommen(pre, post), markdown=markdown)
    if not funde:
        return None

    zeilen = "\n".join(f"  - {art}: `{zeile[:110]}`" for _nr, zeile, art in funde[:_MAX_HITS])
    return (
        "❌ Gliederungsnummer (Poka-Yoke): neue selbstvergebene Nummer/Buchstabe:\n"
        f"{zeilen}\n"
        "  Eine Nummer ist eine zweite Adresse neben dem Anker – nur der Anker wird geprüft, "
        "die Nummer wird bei Umsortierung still falsch (S124: zwei tote Verweise im Bestand).\n"
        "  Nimm den Namen: `## Findings präsentieren` statt `## 5. Findings`, "
        "`[Findings präsentieren](#KZN-…)` statt `[Schritt 5](#KZN-…)`.\n"
        "  Fremdbestimmte Nummerierung (RFC-Abschnitt o.ä.) oder bewusster Einzelfall → "
        "`ordinal-ok` in die Zeile.")


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)
    grund = check(data)
    if grund:
        print(grund, file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
