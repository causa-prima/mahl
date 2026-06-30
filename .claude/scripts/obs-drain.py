#!/usr/bin/env python3
"""obs-drain.py – berechnet den Session-Start-Drain-Satz.

Konsumenten: der SessionStart-Hook (Injektion des Vorschlags) und der Skill `draining-observations`
(autoritativer Satz beim Abarbeiten). Mechanismus & Begründung: docs/kaizen/process.md, Abschnitt
"Backlog-Abbau: kontinuierlicher Drain".

Drei Lanes + zwei Zusatz-Marker (Begriffe kanonisch in process.md, Abschnitt "Backlog-Abbau"):
  - Wert-Lane: Top nach Impact*Häufigkeit. Rate clamp(round(0.4*B), 3, 7), gedeckelt auf B.
  - Alters-Lane: ältestes NEU-Item (1 Slot, Entscheidung erzwungen).
  - Wiedervorlage-Lane: fällige geparkte Items (IN BEOBACHTUNG bis S<NNN>, Termin erreicht)
    → garantiert (nicht rate-gedeckelt). Ersetzt den früheren Retro-Backstop.
  - Kolokation (Marker): andere drainbare OBS an derselben Datei.
  - Hygiene (Marker): aufgelöste (UMGESETZT/VERWORFEN), noch nicht archivierte Items → Verschiebe-Reminder.
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from obs_parse import (  # noqa: E402
    OBS_FILE, current_session, parse_entries, repo_root, is_parked, is_due_parked, is_resolved,
)

P, LO, HI = 0.40, 3, 7
FAR_PARK = 20  # Soft-Cap: Wiedervorlage > ~2 Retro-Perioden voraus (Schnitt ~8, jüngste ~10 Sessions/Periode → großzügig aufgerundet) → Vertipp-/Vanish-Schutz.


def compute(entries):
    # Drainable = Status NEU. IN BEOBACHTUNG = geparkt, UMGESETZT/VERWORFEN = erledigt → nicht im Pool.
    # (Ein LL-/OBS-/CM-Bezug ist nur ein Querverweis, kein Drain-Ausschluss.)
    drainable = [e for e in entries if e["status"].upper().startswith("NEU")]
    b = len(drainable)
    if b == 0:
        return [], None, 0, []
    count = min(max(LO, min(HI, round(P * b))), b)

    # Alters-Lane: ältestes (kleinste session, sub). 1 Slot.
    oldest = sorted(drainable, key=lambda e: (e["session"], e["sub"]))[0]

    # Wert-Lane: Top nach Priorität (Impact*Häufigkeit), Tie-break älter zuerst; ohne das Alters-Item.
    rest = [e for e in drainable if e["id"] != oldest["id"]]
    rest.sort(key=lambda e: (-(e["impact"] * e["freq"]), e["session"], e["sub"]))
    wert = rest[: max(0, count - 1)]
    return wert, oldest, b, drainable


def due_parked(entries, cur):
    # Geparkte Items, deren Wiedervorlage (IN BEOBACHTUNG bis S<NNN>) erreicht ist → zurück in
    # den Drain. Garantierte Lane (nicht rate-gedeckelt): der gewählte Termin MUSS surfacen.
    return sorted((e for e in entries if is_due_parked(e, cur)),
                  key=lambda e: (e["session"], e["sub"]))


def colocation(item, drainable, exclude=frozenset()):
    # Nur Items ausweisen, die NOCH NICHT im Drain-Satz stehen (exclude = bereits selektierte IDs) –
    # ein „+Koloc" auf ein ohnehin vorgeschlagenes Item wäre irreführend.
    if not item["files"]:
        return []
    return [e for e in drainable
            if e["id"] != item["id"] and e["id"] not in exclude and (item["files"] & e["files"])]


def warn_far_parks(entries, cur):
    # Non-blocking stderr-Warnung: ein weit in die Zukunft geparktes Item (bis S200 statt S100) ist
    # meist ein Vertipper und verschwände ohne Cap still. cur None → Alter unbestimmbar, keine Warnung.
    if cur is None:
        return
    for e in entries:
        wv = e.get("wiedervorlage")
        if is_parked(e["status"]) and wv is not None and wv - cur > FAR_PARK:
            print(f"WARNUNG: {e['id']} ist bis S{wv} geparkt ({wv - cur} Sessions voraus, > {FAR_PARK}) "
                  f"– sinnvoll? (Vertipper?)", file=sys.stderr)


def _age(cur, session):
    return (cur - session) if cur is not None else "?"


def render(root: Path, entries):
    wert, oldest, b, drainable = compute(entries)
    cur = current_session(root)
    warn_far_parks(entries, cur)
    due = due_parked(entries, cur)
    resolved = [e for e in entries if is_resolved(e["status"])]

    # "Leer" nur wenn es WIRKLICH nichts zu tun gibt – fällige Wiedervorlagen und
    # aufgelöst-aber-unarchivierte Items müssen auch ohne NEU-Backlog erscheinen.
    if b == 0 and not due and not resolved:
        return "=== OBS-Drain ===\nBacklog leer (keine drainbaren NEU-Items) – kein Drain nötig.\n================="

    count = len(wert) + (1 if oldest else 0)
    selected = {e["id"] for e in wert} | ({oldest["id"]} if oldest else set())
    lines = ["=== OBS-Drain vorgeschlagen ===",
             f"Backlog: {b} drainbar (NEU; gesund ≤ 8) → heute {count} vorgeschlagen."]
    if b > 12:  # 1,5× Gleichgewicht: der Drain ist advisory → Überfüllung sichtbar machen.
        lines.append(f"  ⚠ Backlog überfüllt (B={b}, gesund ≤ 8) – Drain-Ausführung priorisieren.")
    if wert:
        lines += ["", "Wert-Lane (nach Impact × Häufigkeit):"]
        for e in wert:
            prio = e["impact"] * e["freq"]
            coloc = colocation(e, drainable, selected)
            ctag = f"  +Koloc: {', '.join(c['id'] for c in coloc)}" if coloc else ""
            lines.append(f"  - {e['id']}  [{e['impact_raw']} × {e['freq_raw']} = {prio:g}]  {e['title']}{ctag}")
    if oldest:
        coloc = colocation(oldest, drainable, selected)
        ctag = f"  +Koloc: {', '.join(c['id'] for c in coloc)}" if coloc else ""
        lines += ["", "Alters-Lane (ältestes, Entscheidung erzwungen):",
                  f"  - {oldest['id']}  (Alter ~{_age(cur, oldest['session'])} Sessions)  {oldest['title']}{ctag}"]
    if due:
        lines += ["", "Fällige Wiedervorlagen (geparkt, Termin erreicht → entscheiden):"]
        for e in due:
            bis = f"bis S{e['wiedervorlage']}" if e["wiedervorlage"] else "ohne Datum"
            lines.append(f"  - {e['id']}  (war geparkt {bis})  {e['title']}")
    if resolved:
        lines += ["", "Aufgelöst, noch in observations.md → ins Archiv verschieben"
                  " (`python3 .claude/scripts/obs-archive.py`): "
                  + ", ".join(e["id"] for e in resolved) + "."]
    lines += ["", "→ Skill `draining-observations` zum Abarbeiten (umsetzen / verwerfen / aufschieben).",
              "==============================="]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Berechnet den OBS-Drain-Satz.")
    ap.add_argument("--file", help="Pfad zu observations.md (Default: Repo-Standard)")
    args = ap.parse_args()
    root = repo_root()
    obs = Path(args.file) if args.file else root / OBS_FILE
    if not obs.is_file():
        # Non-zero, damit der SessionStart-Hook (|| echo …) den Ausfall sichtbar meldet –
        # eine leere Ausgabe wäre sonst von "Backlog leer" ununterscheidbar.
        print(f"FEHLER: {obs} nicht gefunden – OBS-Drain übersprungen.", file=sys.stderr)
        return 1
    print(render(root, parse_entries(obs.read_text(encoding="utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
