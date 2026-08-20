#!/usr/bin/env python3
"""PreToolUse-Poka-Yoke (blockierend): ein `**Fällig:**` bei offenen Fragen muss auswertbar sein.

Seit S119 (Beschluss E4 aus S118) liest `open_questions.py` das Feld nach derselben
Anker-Grammatik wie Tech-Debt (`.claude/scripts/td_anchors.py`). Ohne Schreibzeit-Prüfung
fiele ein Vertipper (`Phase-V1` statt `Phase:V1`) erst beim nächsten Session-Start auf – und
bis dahin wird die Frage **nicht vorgelegt**, obwohl sie fällig wäre. Genau der lautlose
Fehlermodus, den die Grammatik gerade beseitigt hat: `open_questions.py` kannte vorher nur
`S<NNN>`, alles andere fiel still auf die Alters-Regel zurück.

Der TD-Tracker hat diese Absicherung längst (`check-td-capture.py`); für offene Fragen fehlte
sie. Dieselbe Prüfung, andere Pflichtenlage:

- **`Fällig` ist Pflicht** (seit S121, OBS-S117-4). Vorher war das Feld optional und ein
  Eintrag ohne Termin fiel auf die Alters-Regel zurück – damit blieb eine seit Dutzenden
  Sessions treibende Frage von einer frisch gestellten ununterscheidbar. Die Alters-Regel
  in `open_questions.py` bleibt als Netz für Bestandseinträge, ist aber kein Zielzustand.
- **Der Anker muss tragen.** Ein gesetzter Anker unterdrückt die Alters-Regel; ein
  unauswertbarer oder nicht terminierender Anker ließe die Frage damit dauerhaft verwaisen –
  schlechter als gar kein Feld. Deshalb gelten dann die vollen Regeln aus `td_anchors.validiere`:
  Kopf maschinenlesbar, mindestens ein terminierter Anker, Referenziertes existiert.

Scope:
- **Nur** `docs/open-questions.md`; jede andere Datei passiert ungeprüft.
- Geprüft werden **neu hinzukommende und geänderte** Einträge. Unberührte Bestands-Einträge
  blocken einen Edit nie – man soll nicht fremde Altlast beheben müssen, um die eigene Frage
  zu parken.

Mechanik: PreToolUse läuft VOR der Anwendung; der Hook simuliert den Post-Edit-Inhalt und prüft ihn.
Exit 2 = blockieren. Fail-open: ein Hook-eigener Fehler blockiert nie einen Edit.
"""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import td_anchors  # noqa: E402
from _hook_io import compute_post_content, read_file_text  # noqa: E402

OQ_FILE = "docs/open-questions.md"

_ENTRY_SPLIT_RE = re.compile(r"^## (OQ-S\d{2,3}-\d+)", re.M)
_FAELLIG_RE = re.compile(r"^\*\*Fällig:\*\*(.*)$", re.M)


def is_oq_file(file_path: str) -> bool:
    """True nur für den OQ-Tracker selbst (absolut wie repo-relativ angegeben)."""
    return Path(file_path).as_posix().endswith(OQ_FILE)


def parse_oq_entries(content: str) -> dict[str, str]:
    """OQ-ID → Eintrags-Rumpf (alles zwischen dieser und der nächsten Eintrags-Überschrift)."""
    parts = _ENTRY_SPLIT_RE.split(content)
    return {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}


def faellig_of(body: str) -> str | None:
    """Wert des `**Fällig:**`-Feldes (None, wenn das optionale Feld fehlt)."""
    match = _FAELLIG_RE.search(body)
    return match.group(1).strip() if match else None


def check_entry(oq_id: str, body: str, ktx: td_anchors.Kontext | None = None) -> list[str]:
    """Begründungen, warum die Fälligkeit dieses Eintrags nicht trägt (leer = in Ordnung)."""
    faellig = faellig_of(body)
    if faellig is None:
        return ["`**Fällig:**` fehlt – jede offene Frage schuldet einen Termin oder ein "
                "auslösendes Ereignis. Ohne Feld greift nur die Alters-Regel, und die macht "
                "eine treibende Frage von einer frisch gestellten ununterscheidbar"]
    if not faellig:
        return ["`**Fällig:**` ist leer – Anker setzen (Termin `S<NNN>` oder Ereignis)"]
    return td_anchors.validiere(oq_id, faellig, ktx or td_anchors.Kontext())


def find_violations(pre: str, post: str,
                    ktx: td_anchors.Kontext | None = None) -> list[tuple[str, str]]:
    """(OQ-ID, Begründung) für jeden neuen oder geänderten Eintrag, der die Regeln verletzt."""
    before = parse_oq_entries(pre)
    return [
        (oid, " · ".join(reasons))
        for oid, body in parse_oq_entries(post).items()
        if before.get(oid) != body and (reasons := check_entry(oid, body, ktx))
    ]


def repo_root_for(oq_path: str) -> Path:
    """Repo-Wurzel, abgeleitet aus dem Pfad der bearbeiteten `open-questions.md`."""
    posix = Path(oq_path).as_posix()
    return Path(posix[: -len(OQ_FILE)] if posix.endswith(OQ_FILE) else ".")


def check(data: dict) -> str | None:
    """Dispatcher-Einstieg: Blockier-Grund oder None. Siehe dispatch-edit-write.py.

    Fail-open (Exception → None) liegt beim Dispatcher, damit ein Hook-Fehler
    nie einen Edit blockiert.
    """
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if tool not in ("Edit", "Write") or not file_path or not is_oq_file(file_path):
        return None

    pre = read_file_text(file_path)
    post = compute_post_content(tool, tool_input, pre)
    if post is None:
        return None

    try:
        ktx = td_anchors.lade_kontext(repo_root_for(file_path))
    except Exception:  # noqa: BLE001 – unvollständiger Kontext meldet weniger, blockt nie fälschlich
        ktx = td_anchors.Kontext()

    violations = find_violations(pre, post, ktx)
    if not violations:
        return None

    lines = "\n".join(f"  - {oid}: {reason}" for oid, reason in violations)
    return (
        "❌ OQ-Fälligkeit (Poka-Yoke): `**Fällig:**` fehlt oder trägt nicht:\n"
        f"{lines}\n"
        "  Das Feld ist optional – ohne es wird die Frage nach ~10 Sessions als überaltert "
        "vorgelegt. Ist es aber gesetzt, unterdrückt es genau diese Alters-Regel: Ein Anker, "
        "der nie eintritt oder nicht gelesen werden kann, lässt die Frage dauerhaft "
        "verwaisen – schlechter als gar kein Feld.\n"
        "  Anker-Vokabular: `jetzt`, `Phase:<NAME>`, `S<NNN>`, `Szenario:„<Titel>\"`, "
        "`US-<NNN>`, `TD-S<NNN>-<n>`; mehrere mit Komma, alles Erklärende hinter den "
        "Gedankenstrich. Kanonisch: `.claude/scripts/td_anchors.py`, Vorlage im Header von "
        f"`{OQ_FILE}`."
    )


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)  # kein parsbarer Input → nichts blocken

    try:
        reason = check(data)
        if reason:
            print(reason, file=sys.stderr)
            sys.exit(2)  # exit 2 = Edit blockieren
    except Exception as exc:  # noqa: BLE001 – Hook-Fehler darf nie einen Edit blockieren (fail-open)
        print(f"check-oq-capture: Fehler ({exc}) – Edit nicht blockiert.", file=sys.stderr)
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
