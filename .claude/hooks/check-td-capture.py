#!/usr/bin/env python3
"""PreToolUse-Poka-Yoke (blockierend): jeder TD-Eintrag schuldet eine Fälligkeit.

Ein Eintrag in `docs/tech-debt.md` muss `**Fällig:**`, `**Problem:**` und `**Behebung:**`
tragen. Die frühere Vorlage kannte statt der ersten beiden ein kombiniertes
`**Behebung/Trigger:** <geplante Behebung ODER auslösende Bedingung>` – das „oder" ließ
Einträge vollständig aussehen, die nur beschrieben, *wie* behoben wird, ohne dass jemand
einen Zeitpunkt schuldete (OBS-S112-1). Daneben stand ein `**Priorität:**`-Feld, das im
gesamten Tooling keinen einzigen Leser hatte und entsprechend nichts steuerte (OBS-S112-2):
TD-S089-1 lag rund 22 Sessions mit „Hoch" unbearbeitet.

`**Fällig:** jetzt` verlangt zusätzlich, dass die TD-ID in `docs/AGENT_MEMORY.md` auftaucht.
Das ist keine Formalie, sondern der einzige nachweislich wirksame Weg: `tech-debt.md` wird
nur situativ gelesen (Architektur-Check in `implementing-scenario`), `AGENT_MEMORY.md`
dagegen bei jedem Session-Start injiziert. Ein „jetzt" ohne diesen Eintrag bewegt nichts.

Warum syntaktisch statt per Lese-Disziplin: OBS-S112-1 hält fest, dass das Muster dem
Orchestrator beim Neuschreiben eines Eintrags erneut unterlief, unmittelbar nachdem es in
derselben Session besprochen worden war.

Scope:
- **Nur** `docs/tech-debt.md`; jede andere Datei passiert ungeprüft.
- Geprüft werden **neu hinzukommende und geänderte** Einträge. Unberührte Bestands-Einträge
  blocken einen Edit nie – man soll nicht fremde Altlast beheben müssen, um den eigenen
  Eintrag zu schreiben.

Bewusst KEINE abschließende Feldliste (anders als `check-obs-capture.py`): TD-Einträge führen
legitime fettgesetzte Prosa-Absätze (`**Zusammenhang:**`, `**Schärfer beim zweiten Toast:**`).
Geprüft wird deshalb nur auf Anwesenheit der Pflichtfelder und Abwesenheit der abgeschafften.

Format-Kopplung: Eintrags-Heading `## TD-S<NNN>-<n>` und die Feld-Präfixe sind im Header von
`tech-debt.md` kanonisch festgelegt.

Mechanik: PreToolUse läuft VOR der Anwendung; der Hook simuliert den Post-Edit-Inhalt und prüft ihn.
Exit 2 = blockieren. Fail-open: ein Hook-eigener Fehler blockiert nie einen Edit.
"""
import dataclasses
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import td_anchors  # noqa: E402

TD_FILE = "docs/tech-debt.md"
MEMORY_FILE = "docs/AGENT_MEMORY.md"

_ENTRY_SPLIT_RE = re.compile(r"^## (TD-S\d+-\d+)", re.M)
# Feld-Zeile = fettgesetzter Name mit Doppelpunkt am Zeilenanfang.
_FIELD_RE = re.compile(r"^\*\*([^:*\n]{1,40}?):\*\*", re.M)
REQUIRED_FIELDS = ("Fällig", "Problem", "Behebung")

# Abgeschaffte Felder → warum sie weg sind (wird im Blockier-Text gezeigt).
RETIRED_FIELDS = {
    "Priorität": (
        "hatte im gesamten Tooling keinen Leser und steuerte nichts (OBS-S112-2); "
        "was es vorgab zu regeln, trägt `**Fällig:**`"
    ),
    "Behebung/Trigger": (
        "vermischte „wie behoben wird\" und „wann\" in einem Feld und ließ das „wann\" "
        "per „oder\" weg (OBS-S112-1); jetzt getrennt: `**Behebung:**` + `**Fällig:**`"
    ),
}

_NOW_RE = re.compile(r"^jetzt\b", re.I)


def is_td_file(file_path: str) -> bool:
    """True nur für den TD-Tracker selbst (absolut wie repo-relativ angegeben)."""
    return Path(file_path).as_posix().endswith(TD_FILE)


def parse_td_entries(content: str) -> dict[str, str]:
    """TD-ID → Eintrags-Rumpf (alles zwischen dieser und der nächsten Eintrags-Überschrift)."""
    parts = _ENTRY_SPLIT_RE.split(content)
    return {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}


def field_names(body: str) -> list[str]:
    """Namen der Feld-Zeilen eines Eintrags, in Vorkommens-Reihenfolge."""
    return [name.strip() for name in _FIELD_RE.findall(body)]


def value_of(body: str, field: str) -> str | None:
    """Wert eines Feldes (None, wenn das Feld fehlt)."""
    match = re.search(rf"^\*\*{re.escape(field)}:\*\*(.*)$", body, re.M)
    return match.group(1).strip() if match else None


def is_now(faellig: str) -> bool:
    """True, wenn die Fälligkeit „jetzt" ist (ggf. mit nachgestellter Begründung)."""
    return bool(_NOW_RE.match(faellig.strip()))


def check_entry(td_id: str, body: str, memory_text: str,
                ktx: td_anchors.Kontext | None = None) -> list[str]:
    """Begründungen, warum dieser Eintrag die Format-Regeln verletzt."""
    reasons = []
    names = field_names(body)

    reasons += [f"abgeschafftes Feld `**{name}:**` – {why}"
                for name, why in RETIRED_FIELDS.items() if name in names]
    reasons += [f"Pflichtfeld `**{name}:**` fehlt" for name in REQUIRED_FIELDS if name not in names]

    faellig = value_of(body, "Fällig")
    if faellig is not None and not faellig:
        reasons.append("`**Fällig:**` ist leer – zulässig ist `jetzt` oder ein benennbares "
                       "auslösendes Ereignis")
    elif faellig:
        if is_now(faellig) and td_id not in memory_text:
            reasons.append(
                f"`**Fällig:** jetzt`, aber {td_id} steht nicht in `{MEMORY_FILE}` – "
                "ohne Eintrag in „Nächste Prioritäten\" wird der Posten nie vorgelegt"
            )
        # Anker-Grammatik: Kopf maschinenlesbar, mindestens ein terminierter Anker,
        # Referenziertes existiert. Kanonisch in `.claude/scripts/td_anchors.py`.
        reasons += td_anchors.validiere(td_id, faellig, ktx or td_anchors.Kontext())

    return reasons


def find_violations(pre: str, post: str, memory_text: str,
                    ktx: td_anchors.Kontext | None = None) -> list[tuple[str, str]]:
    """(TD-ID, Begründung) für jeden neuen oder geänderten Eintrag, der die Regeln verletzt."""
    before = parse_td_entries(pre)
    return [
        (tid, " · ".join(reasons))
        for tid, body in parse_td_entries(post).items()
        if before.get(tid) != body and (reasons := check_entry(tid, body, memory_text, ktx))
    ]


def read_file_text(file_path: str) -> str:
    """Aktueller Datei-Inhalt; "" wenn die Datei (noch) nicht existiert."""
    path = Path(file_path)
    return path.read_text(encoding="utf-8") if path.exists() else ""


def repo_root_for(td_path: str) -> Path:
    """Repo-Wurzel, abgeleitet aus dem Pfad der bearbeiteten `tech-debt.md`."""
    posix = Path(td_path).as_posix()
    return Path(posix[: -len(TD_FILE)] if posix.endswith(TD_FILE) else ".")


def kontext_for(td_path: str, post: str) -> td_anchors.Kontext:
    """Auflöse-Kontext für die Anker-Prüfung.

    Die TD-Fälligkeiten kommen aus dem **simulierten Post-Inhalt**, nicht von der Platte:
    Fügt ein Edit einen Eintrag hinzu, auf den ein anderer per `TD-`-Anker zeigt, wäre er im
    Vor-Zustand noch nicht da und der Anker fälschlich als dangling gemeldet.
    """
    ktx = td_anchors.lade_kontext(repo_root_for(td_path))
    return dataclasses.replace(ktx, td_faelligkeiten=td_anchors.td_faelligkeiten(post))


def memory_text_for(td_path: str) -> str:
    """Inhalt der `AGENT_MEMORY.md`, die neben der bearbeiteten `tech-debt.md` liegt.

    Leerer String, wenn sie fehlt – dann greift die „jetzt"-Kopplung nicht (fail-open:
    ein fehlendes Nachbardokument darf keinen Edit blocken).
    """
    posix = Path(td_path).as_posix()
    root = posix[: -len(TD_FILE)] if posix.endswith(TD_FILE) else ""
    return read_file_text(str(Path(root) / MEMORY_FILE))


def compute_post_content(tool: str, tool_input: dict, pre: str) -> str | None:
    """Simuliert den Datei-Inhalt nach Anwendung des Edits/Writes."""
    if tool == "Write":
        return tool_input.get("content", "")
    if tool == "Edit":
        old = tool_input.get("old_string", "")
        new = tool_input.get("new_string", "")
        if old and old in pre:
            count = -1 if tool_input.get("replace_all") else 1
            return pre.replace(old, new, count)
        return pre  # old_string nicht gefunden → echter Edit schlägt ohnehin fehl
    return None


def check(data: dict) -> str | None:
    """Dispatcher-Einstieg: Blockier-Grund oder None. Siehe dispatch-edit-write.py.

    Fail-open (Exception → None) liegt beim Dispatcher, damit ein Hook-Fehler
    nie einen Edit blockiert.
    """
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if tool not in ("Edit", "Write") or not file_path or not is_td_file(file_path):
        return None

    pre = read_file_text(file_path)
    post = compute_post_content(tool, tool_input, pre)
    if post is None:
        return None

    violations = find_violations(pre, post, memory_text_for(file_path),
                                 kontext_for(file_path, post))
    if not violations:
        return None

    lines = "\n".join(f"  - {tid}: {reason}" for tid, reason in violations)
    return (
        "❌ TD-Format (Poka-Yoke): Eintrag ohne belastbare Fälligkeit:\n"
        f"{lines}\n"
        "  Die Vorlage lautet:\n"
        "    **Fällig:** <Anker>[, <Anker>…] – <Freitext-Erläuterung>\n"
        "    **Problem:** <was ist die Schuld>\n"
        "    **Behebung:** <wie behoben wird>\n"
        "  1. `**Fällig:**` ist Pflicht. Ein Eintrag, der nur sagt, WIE behoben wird, schuldet "
        "niemandem einen Zeitpunkt.\n"
        "  2. Der Kopf vor dem Gedankenstrich ist maschinenlesbar. Anker-Vokabular:\n"
        "       jetzt            sofort\n"
        "       Phase:MVP        Phasenwechsel (auch V1/V2)\n"
        "       S130             Spätestens-Termin (Session)\n"
        "       Szenario:„…\"     ein Gherkin-Szenario aus features/ (Titel exakt)\n"
        "       US-602           eine Story – nur solange sie noch keine Szenarien hat\n"
        "       TD-S089-1        ein anderer Eintrag (Kette muss terminieren, zyklenfrei)\n"
        "     Alles Erklärende gehört HINTER den Gedankenstrich und bleibt dort erhalten.\n"
        "  3. Mindestens ein Anker muss **terminiert** sein, also sagen WANN. Terminiert: "
        "`jetzt`, `Phase:`, `S<NNN>`, `Szenario:` mit `# @run-N`-Zuordnung. Nicht terminiert: "
        "`US-NNN` und ein Szenario ohne Lauf – die brauchen einen Backstop dazu "
        "(`Szenario:„…\", Phase:MVP`). Ein Anker, der nur eintreten *kann*, lässt den Eintrag "
        "verwaisen (OBS-S099-1).\n"
        "  4. `jetzt` verlangt einen Punkt in `docs/AGENT_MEMORY.md` unter „Nächste "
        "Prioritäten\" – nur das wird bei jedem Session-Start gelesen. Trag ihn dort zuerst "
        "ein, dann greift diese Prüfung.\n"
        "  5. Verletzt der Eintrag eine HEUTE geltende Regel (NFR, Guideline, DoD), ist die "
        "Fälligkeit immer `jetzt` – eine geltende Regel wartet auf keine Bedingung. Soll sie "
        "doch warten, ist das eine Entscheidung über die Regel: Regel ändern, oder die "
        "Abweichung als **dauerhafte** Ausnahme per ADR festschreiben – dann ist sie "
        "entschieden und der Eintrag entfällt. Was es nicht gibt: eine ADR, die dem Eintrag "
        "nur erlaubt zu warten (Hybrid – s. `CLAUDE.md`, „Ablage: ADR, TD oder offene "
        "Frage?\"). Ein ungeprüfter Verdacht ist keine Verletzung – dann ist die Prüfung die "
        "Behebung und bekommt eine eigene Fälligkeit."
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
        print(f"check-td-capture: Fehler ({exc}) – Edit nicht blockiert.", file=sys.stderr)
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
