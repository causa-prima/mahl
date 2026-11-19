#!/usr/bin/env python3
"""Wohin geht das Read-Volumen? Aufgeschlüsselt nach Session-Art, Bereich und Datei.

Hintergrund: `Read` ist der mit Abstand größte Token-Posten (OBS-S109-1). Dieses Script
misst ihn an den Session-Logs statt ihn zu schätzen, und trennt dabei nach **Session-Art**
(implementierung / drain / retro / tooling …) – die Vorgänger-Messung aus S109 scannte nur
Sessions mit Subagenten und traf damit unbemerkt eine Aussage über allein
implementing-scenario-Sessions.

Warum als reguläres Script statt als Wegwerf-Code: Die S109-Fassung lag in `.claude/tmp/`,
wurde nach Gebrauch gelöscht und musste in S114 aus dem rohen Session-Log rekonstruiert
werden – dasselbe Muster, das OBS-S111-3 für den Stryker-Report beschreibt. Die
Wiedervorlagen von OBS-S085-3/-4 brauchen dieselbe Sorte Messung erneut.

Beispiele:
  python3 -m prozesscode.read-breakdown                  # Überblick je Session-Art
  python3 -m prozesscode.read-breakdown --by-area        # Bereiche, alle Arten
  python3 -m prozesscode.read-breakdown --by-area --type drain
  python3 -m prozesscode.read-breakdown --top 20         # größte Einzeldateien
  python3 -m prozesscode.read-breakdown --sessions       # erkannte Art je Session
  python3 -m prozesscode.read-breakdown --json
  python3 -m prozesscode.read-breakdown --by-agent --since 2026-10-24   # je Agententyp
  python3 -m prozesscode.read-breakdown --agent frontend-layer-implementer --top 15
  python3 -m prozesscode.read-breakdown --anker --since 2026-11-05     # Zitate/Abrufe je Anker

**Je Agent statt je Art (OBS-S109-1, OBS-S114-2):** Die Session-Art ist eine grobe Einheit
geworden – Sessions sind gemischt (Durchsicht und Drain, Querschnitt und Lauf) und enthalten
1–3 Läufe, ein Wert je Implementierungs-Session hängt also an der Zahl der Läufe darin. Ein
Subagenten-Aufruf hat genau einen Typ, und ein Implementer-Aufruf gehört zu genau einem Lauf.
Zwei Zeiträume vergleicht `--since … --until …`.

**Je Anker (OBS-S114-2):** Ob ein Abschnitt der Pflichtlektüre seinen Lesepreis wert ist, zeigt
sich daran, ob er je eine Regel für ein Finding liefert („Regel: <ANKER>", Pflicht seit S146)
oder gezielt abgerufen wird (`doc get`). Ohne Zitat kann ein Abschnitt trotzdem gelesen,
befolgt und nötig gewesen sein – die Liste der ungenutzten Anker benennt Kandidaten, kein Urteil.
"""
import argparse
import json
import sys
import textwrap
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


from . import anchors
from ._cli import Parser
from ._session_logs import (  # noqa: E402
    MAPPING_FILE,
    UNBEKANNT,
    agent_type,
    categorize,
    doc_abrufe,
    edited_paths,
    load_mapping,
    load_records,
    project_log_dir,
    read_events,
    regel_zitate,
    relative_path,
    session_datum,
    session_logs,
    session_type,
    skills_in,
)
from ._util import REPO_ROOT

# Der Kontext des Orchestrators – in der Auswertung je Agent neben den Subagententypen.
HAUPTSESSION = "hauptsession"
PFLICHT_ORDNER = ("docs/guidelines", "docs/process")
PFLICHT_BEREICHE = ("docs/guidelines (Pflichtlektüre)", "docs/process (Pflichtlektüre)")


class Totals:
    """Sammelt die Kennzahlen einer Auswertung."""

    def __init__(self) -> None:
        self.kontexte = 0          # ausgewertete Logs: je Subagenten-Aufruf bzw. Hauptsession eins
        self.zitate: Counter = Counter()   # „Regel: <ANKER>" im eigenen Text
        self.abrufe: Counter = Counter()   # `doc get <ANKER>`
        self.volume = 0
        self.calls = 0
        self.by_area: Counter = Counter()
        self.calls_by_area: Counter = Counter()
        self.by_file: Counter = Counter()
        self.pre_edit = 0          # Read auf eine Datei, die im selben Kontext editiert wird
        self.rereads = 0           # dieselbe Datei im selben Kontext erneut gelesen
        self.reread_calls = 0
        self.targeted = 0          # mit offset/limit gelesen, also bewusst nur ein Ausschnitt
        self.pre_edit_by_area: Counter = Counter()
        self.targeted_by_area: Counter = Counter()

    def add(self, path: str, size: int, is_pre_edit: bool, is_reread: bool,
            is_targeted: bool) -> None:
        self.volume += size
        self.calls += 1
        area = categorize(path)
        self.by_area[area] += size
        self.calls_by_area[area] += 1
        self.by_file[relative_path(path)] += size
        if is_pre_edit:
            self.pre_edit += size
            self.pre_edit_by_area[area] += size
        if is_targeted:
            self.targeted += size
            self.targeted_by_area[area] += size
        if is_reread:
            self.rereads += size
            self.reread_calls += 1


def scan_context(records: list[dict], sinks: list[Totals], mit_zitaten: bool = True) -> None:
    """Wertet einen Kontext (Hauptlog ODER ein Subagent-Log) aus und speist alle Senken.

    „Kontext" ist bewusst das einzelne Log: Ein Subagent startet frisch, seine Re-Reads und
    Vor-Edit-Reads sind seine eigenen und dürfen nicht mit denen des Orchestrators verrechnet
    werden. Regel-Zitate zählen nur in Subagenten-Logs (`mit_zitaten`): Der Orchestrator
    reicht Findings weiter – an den User, per SendMessage an den Implementer –, seine Zitate
    wären Kopien.
    """
    touched = edited_paths(records)
    zitate = regel_zitate(records) if mit_zitaten else Counter()
    abrufe = doc_abrufe(records)
    for sink in sinks:
        sink.kontexte += 1
        sink.zitate += zitate
        sink.abrufe += abrufe
    seen: set[str] = set()
    for path, size, targeted in read_events(records):
        is_reread = path in seen
        seen.add(path)
        for sink in sinks:
            sink.add(path, size, path in touched, is_reread, targeted)


@dataclass
class Messung:
    gesamt: Totals
    je_art: dict[str, Totals]
    sessions_je_art: dict[str, int]
    zuordnung: list[tuple[str, str, str]]
    # Je Subagententyp, dazu HAUPTSESSION. Feiner als die Art: Sessions sind gemischt und
    # enthalten 1–3 Läufe, ein Subagenten-Aufruf hat genau einen Typ.
    je_agent: dict[str, Totals]


def _im_fenster(tag: str | None, since: str | None, until: str | None) -> bool:
    # ISO-Datum: lexikographischer Vergleich ist chronologisch. Eine Session ohne Zeitstempel
    # fällt heraus, sobald ein Fenster gesetzt ist – sie einzurechnen hieße, sie ins gewählte
    # Fenster zu raten, und das Fenster ist der ganze Zweck des Filters.
    if tag is None:
        return False
    return not (since and tag < since) and not (until and tag > until)


def collect(log_dir: Path, since: str | None = None, until: str | None = None) -> Messung:
    """Misst alle Sessions – gesamt, je Session-Art und je Agententyp.

    `since`/`until` (`YYYY-MM-DD`, beide inklusiv) beschränken auf Sessions in diesem Fenster.
    Ohne diese Trennung lässt sich die Wirkung einer Maßnahme nicht messen: Der Aggregatwert
    über alle Sessions verdünnt jede Änderung, bis sie unsichtbar ist. Genau daran scheiterte
    die für S120 geplante Re-Messung zu OBS-S109-1 – seit der Maßnahme in S114 lief nur eine
    einzige Implementierungs-Session, gegen 24 im Gesamtwert. `until` macht zudem zwei
    Zeiträume vergleichbar (wächst das Lesen je Aufruf?).
    """
    mapping = load_mapping()
    gesamt = Totals()
    je_art: dict[str, Totals] = defaultdict(Totals)
    je_agent: dict[str, Totals] = defaultdict(Totals)
    sessions_je_art: Counter = Counter()
    zuordnung: list[tuple[str, str, str]] = []

    for session_id, main_log, sub_logs in session_logs(log_dir):
        if (since or until) and not _im_fenster(session_datum(main_log), since, until):
            continue
        haupt = load_records(main_log)
        sub_records = [load_records(p) for p in sub_logs]

        skills = skills_in(haupt)
        edits = edited_paths(haupt)
        for recs in sub_records:
            skills += skills_in(recs)
            edits |= edited_paths(recs)
        art, herkunft = session_type(session_id, skills, mapping, edits)

        zuordnung.append((session_id, art, herkunft))
        sessions_je_art[art] += 1
        scan_context(haupt, [gesamt, je_art[art], je_agent[HAUPTSESSION]], mit_zitaten=False)
        for pfad, recs in zip(sub_logs, sub_records, strict=True):
            scan_context(recs, [gesamt, je_art[art], je_agent[agent_type(pfad)]])

    return Messung(gesamt, dict(je_art), dict(sessions_je_art), zuordnung, dict(je_agent))


def pflicht_anker(root: Path = REPO_ROOT) -> dict[str, str]:
    """Anker der Pflichtlektüre (`docs/guidelines`, `docs/process`) → repo-relative Datei."""
    return {
        anker: datei.relative_to(root).as_posix()
        for ordner in PFLICHT_ORDNER
        for datei in sorted((root / ordner).glob("*.md"))
        for anker in anchors.anker_in(datei.read_text(encoding="utf-8"))
    }


def _bar(anteil: float, breite: int = 24) -> str:
    return "█" * round(anteil * breite)


def print_overview(gesamt: Totals, je_art: dict[str, Totals], sessions: dict[str, int]) -> None:
    print("=" * 78)
    print(f"READ-Volumen je Session-Art   ({gesamt.volume / 1000:.0f}k Zeichen, "
          f"{gesamt.calls} Aufrufe, {sum(sessions.values())} Sessions)")
    print("=" * 78)
    print(f"  {'Art':<18} {'Sess.':>6} {'Volumen':>10} {'Anteil':>8} {'Ø/Session':>11}")
    for art, totals in sorted(je_art.items(), key=lambda kv: -kv[1].volume):
        n = sessions[art]
        anteil = totals.volume / gesamt.volume if gesamt.volume else 0
        print(f"  {art:<18} {n:>6} {totals.volume / 1000:>9.0f}k {anteil * 100:>7.1f}% "
              f"{totals.volume / (n or 1) / 1000:>10.0f}k  {_bar(anteil)}")

    if gesamt.volume:
        print()
        print(f"  Vor-Edit-Reads (Harness-Zwang): {gesamt.pre_edit / 1000:.0f}k "
              f"({gesamt.pre_edit / gesamt.volume * 100:.1f}%) – der Rest ist Lektüre/Recherche")
        print(f"  Re-Reads derselben Datei:       {gesamt.rereads / 1000:.0f}k "
              f"({gesamt.rereads / gesamt.volume * 100:.1f}%, {gesamt.reread_calls} Aufrufe)")


def print_areas(totals: Totals, titel: str) -> None:
    print()
    print("=" * 78)
    print(f"Bereiche – {titel}   ({totals.volume / 1000:.0f}k Zeichen)")
    print("=" * 78)
    print(f"  {'Bereich':<38} {'Volumen':>8} {'Anteil':>7} {'Reads':>6} {'Ø':>7} "
          f"{'vor Edit':>9} {'gezielt':>8}")
    for area, value in totals.by_area.most_common():
        n = totals.calls_by_area[area]
        anteil = value / totals.volume if totals.volume else 0
        vor_edit = totals.pre_edit_by_area[area] / value * 100 if value else 0
        gezielt = totals.targeted_by_area[area] / value * 100 if value else 0
        print(f"  {area:<38} {value / 1000:>7.0f}k {anteil * 100:>6.1f}% "
              f"{n:>6} {value / (n or 1):>7.0f} {vor_edit:>8.0f}% {gezielt:>7.0f}%")
    print("\n  „vor Edit\" = die Datei wird im selben Kontext noch editiert (Harness verlangt "
          "den Read).\n  „gezielt\" = mit offset/limit gelesen statt vollständig.")


def print_top_files(totals: Totals, limit: int, titel: str) -> None:
    print()
    print("=" * 78)
    print(f"Größte gelesene Dateien – {titel}")
    print("=" * 78)
    for path, value in totals.by_file.most_common(limit):
        print(f"  {value / 1000:>7.0f}k  {path[:64]}")


def print_agents(je_agent: dict[str, Totals]) -> None:
    print()
    print("=" * 78)
    print("Je Agent   (Aufruf = ein Subagenten-Log bzw. eine Hauptsession)")
    print("=" * 78)
    print(f"  {'Agent':<34} {'Aufrufe':>7} {'Volumen':>8} {'Ø/Aufruf':>9} {'gezielt':>8} "
          f"{'Pflicht Ø':>10} {'doc get':>8}")
    for agent, t in sorted(je_agent.items(), key=lambda kv: -kv[1].volume):
        n = t.kontexte or 1
        gezielt = t.targeted / t.volume * 100 if t.volume else 0
        pflicht = sum(t.by_area[b] for b in PFLICHT_BEREICHE)
        print(f"  {agent:<34} {t.kontexte:>7} {t.volume / 1000:>7.0f}k {t.volume / n:>9.0f} "
              f"{gezielt:>7.0f}% {pflicht / n:>10.0f} {sum(t.abrufe.values()):>8}")
    print("\n  „Pflicht Ø\" = Zeichen aus docs/guidelines und docs/process je Aufruf.\n"
          "  Dateien eines Typs: --agent TYP --top N, Bereiche: --agent TYP --by-area.")


def print_anker(totals: Totals, titel: str, bestand: dict[str, str]) -> None:
    print()
    print("=" * 78)
    print(f"Anker – {titel}   (Zitate = „Regel: <ANKER>\" im Finding, Abrufe = doc get)")
    print("=" * 78)
    genutzt = (set(totals.zitate) | set(totals.abrufe)) - {"keine"}
    print(f"  {'Anker':<34} {'Zitate':>7} {'Abrufe':>7}  Datei")
    for anker in sorted(genutzt, key=lambda a: (-totals.zitate[a] - totals.abrufe[a], a)):
        datei = bestand.get(anker, "(nicht Pflichtlektüre)")
        print(f"  {anker:<34} {totals.zitate[anker]:>7} {totals.abrufe[anker]:>7}  {datei}")
    print(f"\n  Findings mit „Regel: keine\": {totals.zitate['keine']}")

    rest = sorted(set(bestand) - genutzt)
    print(f"\n  Pflichtlektüre-Anker nie zitiert und nie abgerufen: {len(rest)} von {len(bestand)}")
    print(textwrap.fill(", ".join(rest), width=76, initial_indent="    ",
                        subsequent_indent="    "))
    print("  Vorbehalt: Ohne Zitat kann ein Abschnitt trotzdem gelesen, befolgt und nötig gewesen sein.")


def print_sessions(zuordnung: list[tuple[str, str, str]]) -> None:
    print()
    print("=" * 78)
    print("Erkannte Art je Session   (Herkunft: mapping > skill > heuristik)")
    print("=" * 78)
    for session_id, art, herkunft in zuordnung:
        marker = "  ← manuell zuordnen" if art == UNBEKANNT else ""
        print(f"  {session_id[:8]}…  {art:<18} {herkunft}{marker}")
    offen = [s for s, art, _ in zuordnung if art == UNBEKANNT]
    if offen:
        print(f"\n  {len(offen)} Session(s) ohne Signal. Ergänze sie in {MAPPING_FILE.name}:")
        print('    { "%s": "drain" }' % offen[0][:8])


def main() -> None:
    parser = Parser(
        description="Read-Volumen nach Session-Art, Bereich und Datei.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--by-area", action="store_true", help="Aufschlüsselung nach Bereich")
    parser.add_argument("--top", type=int, metavar="N", help="Top-N Einzeldateien")
    parser.add_argument("--type", metavar="ART", help="nur eine Session-Art auswerten")
    parser.add_argument("--sessions", action="store_true", help="erkannte Art je Session zeigen")
    parser.add_argument("--json", action="store_true", help="maschinenlesbar")
    parser.add_argument("--since", metavar="YYYY-MM-DD",
                        help="nur Sessions ab diesem Tag – trennt vor/nach einer Maßnahme")
    parser.add_argument("--until", metavar="YYYY-MM-DD",
                        help="nur Sessions bis zu diesem Tag (inklusiv) – macht Zeiträume vergleichbar")
    parser.add_argument("--by-agent", action="store_true",
                        help="je Agententyp: Aufrufe, Volumen und Pflichtlektüre je Aufruf")
    parser.add_argument("--agent", metavar="TYP",
                        help="nur einen Agententyp auswerten (z.B. hauptsession, code-quality-auditor)")
    parser.add_argument("--anker", action="store_true",
                        help="Regel-Zitate und doc-get-Abrufe je Anker, dazu ungenutzte Pflichtlektüre")
    args = parser.parse_args()
    if args.agent and args.type:
        parser.error("--agent und --type schließen sich aus: ein Subagent gehört zu einer "
                     "Session, aber nicht jede Session-Art hat ihn")

    log_dir = project_log_dir()
    if not log_dir.exists():
        print(f"Keine Session-Logs unter {log_dir}", file=sys.stderr)
        sys.exit(1)

    m = collect(log_dir, since=args.since, until=args.until)
    if (args.since or args.until) and not sum(m.sessions_je_art.values()):
        fenster = " ".join(f"{wort} {tag}" for wort, tag in (("ab", args.since), ("bis", args.until)) if tag)
        print(f"Keine Sessions {fenster} – der Vergleich trägt nichts.", file=sys.stderr)
        sys.exit(1)

    gewaehlt, titel = m.gesamt, "alle Session-Arten"
    for wert, auswahl, wort in ((args.type, m.je_art, "Art"), (args.agent, m.je_agent, "Agent")):
        if not wert:
            continue
        if wert not in auswahl:
            print(f"Unbekannter Wert für {wort} '{wert}'. Verfügbar: {', '.join(sorted(auswahl))}",
                  file=sys.stderr)
            sys.exit(1)
        gewaehlt, titel = auswahl[wert], wert

    if args.json:
        print(json.dumps({
            "gesamt": {"volumen": m.gesamt.volume, "aufrufe": m.gesamt.calls},
            "je_art": {
                art: {"volumen": t.volume, "aufrufe": t.calls, "sessions": m.sessions_je_art[art]}
                for art, t in m.je_art.items()
            },
            "je_agent": {
                agent: {"volumen": t.volume, "aufrufe": t.calls, "kontexte": t.kontexte}
                for agent, t in m.je_agent.items()
            },
            "bereiche": dict(gewaehlt.by_area),
            "dateien": dict(gewaehlt.by_file.most_common(args.top or 20)),
            "zitate": dict(gewaehlt.zitate),
            "abrufe": dict(gewaehlt.abrufe),
            "zuordnung": {sid: {"art": art, "herkunft": h} for sid, art, h in m.zuordnung},
        }, ensure_ascii=False, indent=2))
        return

    print_overview(m.gesamt, m.je_art, m.sessions_je_art)
    if args.by_agent:
        print_agents(m.je_agent)
    if args.by_area:
        print_areas(gewaehlt, titel)
    if args.top:
        print_top_files(gewaehlt, args.top, titel)
    if args.anker:
        print_anker(gewaehlt, titel, pflicht_anker())
    if args.sessions:
        print_sessions(m.zuordnung)
    if not (args.by_area or args.top or args.sessions or args.by_agent or args.anker):
        print("\n  Mehr Tiefe: --by-area | --top N | --sessions | --type ART | --by-agent | "
              "--agent TYP | --anker")


if __name__ == "__main__":
    main()
