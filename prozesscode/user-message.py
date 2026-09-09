#!/usr/bin/env python3
"""SessionStart-Nachricht an den USER – der einzige Kanal, der nicht über den Agenten läuft.

Die fünf Agenda-Blöcke geben Plain-Text aus. Der landet bei `SessionStart` im **Agenten**-Kontext
(Hook-Doku: „adds plain-text stdout as context that Claude can see and act on"). Für Blöcke,
deren Zweck die Weitergabe an den User ist – die fälligen offenen Fragen –, hängt das Ankommen
damit allein an der Disziplin des Agenten; kein Mechanismus prüft die Übergabe (OBS-S117-2, in
S117 real durchgerutscht).

Dieses Modul nutzt den anderen Weg: `systemMessage` (Feldort s. `ausgabe`). Empirisch in S131
gemessen – der User sieht die Zeile (`SessionStart:clear says: …`), der Agent bekommt sie
**nicht**. Beides ist gewollt: Die Nachricht ist eine Quittung für den User, keine zweite Kopie
für den Agenten. Gemessen werden musste es, weil die Hook-Doku `SessionStart` unter den Events
führt, bei denen die Nachricht „shown to Claude" sei – real ist es umgekehrt. Wer den Kanal
ändert, misst neu, statt der Tabelle zu glauben.

Bewusst ein eigener Hook-Eintrag neben den fünf Agenda-Blöcken: Sobald ein Hook JSON ausgibt,
wird es als JSON geparst und nicht mehr als Plain-Text-Kontext behandelt. Die Blöcke umzubauen
hieße, den funktionierenden Teil des Session-Starts anzufassen.

Bewusst **nur** die offenen Fragen: `td-due` und `ungeclusterte-szenarien` sind Nachrang-Stubs,
die ausdrücklich nicht vorgelegt werden sollen. Eine Zeile, die bei jedem Start erscheint,
bedeutet nichts mehr.
"""
import json
import sys
from pathlib import Path

from . import open_questions, td_anchors
from .repo_kontext import current_session

ROOT = Path(__file__).resolve().parent.parent

ABRUF = "python3 -m prozesscode.session-agenda --only open-questions"


def faellige_fragen() -> list[dict]:
    """Die fälligen offenen Fragen – dieselbe Quelle und Fälligkeitslogik wie die Agenda."""
    fragen = open_questions.parse((ROOT / open_questions.OQ_FILE).read_text(encoding="utf-8"))
    return open_questions.due(fragen, td_anchors.lade_kontext(ROOT), current_session(ROOT))


def nachricht(faellig: list[dict]) -> str | None:
    """Quittung für den User, oder None wenn nichts fällig ist.

    Bewusst knapp: ID und Titel genügen, um nachzufassen. Der Volltext steht im Agenten-Kontext
    (Agenda-Block `open-questions`) und in der Datei – hier zählt, dass der User **erfährt**,
    dass etwas vorzulegen war, auch wenn der Agent es übergeht.
    """
    if not faellig:
        return None
    zeilen = [f"   {f['id']} — {f['title']}" for f in faellig]
    return (
        f"🔔 {len(faellig)} offene Frage(n) fällig – der Agent sollte sie dir vorlegen "
        f"(nicht selbst entscheiden):\n"
        + "\n".join(zeilen)
        + f"\n   Übergeht er sie: {ABRUF}"
    )


def ausgabe(text: str) -> str:
    """Hook-JSON mit `systemMessage`.

    **Top-level, nicht in `hookSpecificOutput`.** Die JSON-Output-Tabelle führt `systemMessage`
    als universelles Feld neben `hookSpecificOutput`; letzteres trägt nur event-spezifische
    Entscheidungsfelder. Verschachtelt liest es niemand – der Hook liefe grün und wirkte nicht.
    """
    # ensure_ascii=False: Umlaute und Emoji bleiben lesbar, statt als \uXXXX zu reisen – der
    # Text wird angezeigt, nicht weiterverarbeitet.
    return json.dumps({"systemMessage": text}, ensure_ascii=False)


def main() -> int:
    try:
        text = nachricht(faellige_fragen())
    except Exception as exc:  # noqa: BLE001 – fail-open: ein Nebenkanal bremst keinen Start
        print(f"user-message: übersprungen ({exc})", file=sys.stderr)
        return 0
    if text:
        sys.stdout.write(ausgabe(text))
    return 0


if __name__ == "__main__":
    sys.exit(main())
