#!/usr/bin/env python3
"""obs-drain.py – berechnet den Session-Start-Drain-Satz.

Konsumenten: der SessionStart-Hook (Injektion des Vorschlags) und der Skill `draining-observations`
(autoritativer Satz beim Abarbeiten). Mechanismus & Begründung: docs/kaizen/process.md, Abschnitt
"Backlog-Abbau: kontinuierlicher Drain".

Drei Lanes + zwei Zusatz-Marker (Begriffe kanonisch in process.md, Abschnitt "Backlog-Abbau"):
  - Wert-Lane: behandlungswürdige Einheiten (Score ≥ WUERDIG_AB) nach Score, bis KAPAZITAET Einträge.
  - Alters-Lane: alle NEU-Items älter als ALT_AB, sonst das älteste (Entscheidung erzwungen).
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
    OBS_FILE, WUERDIG_AB, current_session, parse_entries, repo_root, score,
    is_parked, is_due_parked, is_resolved,
)

FAR_PARK = 20  # Soft-Cap: Wiedervorlage > ~2 Retro-Perioden voraus (Schnitt ~8, jüngste ~10 Sessions/Periode → großzügig aufgerundet) → Vertipp-/Vanish-Schutz.

# Steuergrößen des Drains (S122). Herleitung kanonisch in docs/kaizen/process.md,
# Abschnitt "Backlog-Abbau: kontinuierlicher Drain".
ALT_AB = 15        # Sessions bis zur Alters-Lane. Steuert NICHT den Durchsatz (der entspricht im
                   # Gleichgewicht dem Zufluss), sondern den stehenden Bestand ≈ Zufluss × ALT_AB.
TOP_N = 5          # Einheiten in der Trigger-Summe – die gemessene Kapazität einer Drain-Session
                   # (S109…S121: 7/5/5/5/3/1/3). Was mehr wert ist, als eine Session abarbeiten
                   # kann, darf nicht mittriggern; sonst löst eine lange Liste Bagatellen dieselbe
                   # Summe aus wie ein schwerer Befund. Nur die Trigger-FRAGE ist so gedeckelt –
                   # der Satz selbst zeigt alles Behandlungswürdige, sonst versteckte er Arbeit.
TRIGGER_WERT = 9   # = KRITISCH × gelegentlich: der kleinste Einzelbefund, der eine Session allein
                   # rechtfertigt.
TRIGGER_ALT = 4    # Einträge über ALT_AB, ab denen der Drain auch ohne Wert beansprucht.


def cluster(drainable):
    """Einheiten bilden: transitive Hülle über das `Zusammen-erledigen:`-Feld, nur unter drainbaren Einträgen.

    Eine Einheit wird gemeinsam priorisiert *und* gemeinsam bearbeitet – wer an einem Thema
    dran ist, nimmt die verwandten Punkte mit. Kanten zu erledigten/geparkten Einträgen bilden
    bewusst keine Einheit (sonst addierte ein längst gelöster Eintrag Score zu einem offenen);
    als Kontext beim Bearbeiten bleiben sie über das Feld trotzdem auffindbar.
    """
    nach_id = {e["id"]: e for e in drainable}
    nachbarn = {e["id"]: set() for e in drainable}
    for e in drainable:
        for ziel in e["zusammen"]:
            if ziel in nach_id and ziel != e["id"]:
                nachbarn[e["id"]].add(ziel)
                nachbarn[ziel].add(e["id"])
            elif ziel != e["id"]:
                # Nicht stumm verwerfen: Solche Kanten entstehen zwangsläufig, sobald der
                # Partner aufgelöst und archiviert wird. Lautlos wäre der Ausfall von
                # „hatte nie eine Kante" nicht unterscheidbar – und ein Vertipper, den die
                # Schreibprüfung nicht abgefangen hat, bliebe für immer unsichtbar.
                print(f"WARNUNG: {e['id']} nennt {ziel} unter Zusammen-erledigen, aber der "
                      f"Eintrag ist nicht (mehr) drainbar – Kante wirkungslos, ggf. entfernen "
                      f"(`obs.py set {e['id']} --zusammen-erledigen …`).", file=sys.stderr)

    gesehen, einheiten = set(), []
    for e in sorted(drainable, key=lambda x: (x["session"], x["sub"])):
        if e["id"] in gesehen:
            continue
        stapel, gruppe = [e["id"]], []
        while stapel:
            aktuell = stapel.pop()
            if aktuell in gesehen:
                continue
            gesehen.add(aktuell)
            gruppe.append(nach_id[aktuell])
            stapel.extend(nachbarn[aktuell] - gesehen)
        einheiten.append(sorted(gruppe, key=lambda x: (x["session"], x["sub"])))
    return einheiten


def unit_score(einheit) -> float:
    return sum(score(e) for e in einheit)


def _alter(cur, e):
    return (cur - e["session"]) if cur is not None else 0


def wert_einheiten(drainable):
    """Behandlungswürdige Einheiten, nach Score absteigend (Tie-break: ältere zuerst)."""
    wuerdig = [u for u in cluster(drainable) if unit_score(u) >= WUERDIG_AB]
    wuerdig.sort(key=lambda u: (-unit_score(u), u[0]["session"], u[0]["sub"]))
    return wuerdig


def compute(entries, cur=None):
    # Drainable = Status NEU. IN BEOBACHTUNG = geparkt, UMGESETZT/VERWORFEN = erledigt → nicht im Pool.
    # (Ein LL-/OBS-/CM-Bezug ist nur ein Querverweis, kein Drain-Ausschluss.)
    drainable = [e for e in entries if e["status"].upper().startswith("NEU")]
    b = len(drainable)
    if b == 0:
        return [], [], 0, []

    # Wert-Lane: ALLE behandlungswürdigen Einheiten. Bewusst ungedeckelt – ein Deckel begrenzte
    # nur den Vorschlag, nicht die Arbeit, und versteckte Behandlungswürdiges. Für verdauliche
    # Portionen sorgt der Skill (er legt wenige Einheiten auf einmal vor), nicht dieser Satz.
    wert = wert_einheiten(drainable)

    # Alters-Lane: alles über ALT_AB – sonst (oder wenn das Alter unbestimmbar ist) das älteste.
    # Ohne den Vollzugriff bliebe bei einem gewachsenen Altbestand ein Eintrag je Drain übrig,
    # während mehr als einer pro Session nachaltert.
    gewaehlt = {e["id"] for u in wert for e in u}
    rest = [e for e in drainable if e["id"] not in gewaehlt]
    alt = [e for e in rest if _alter(cur, e) > ALT_AB]
    if not alt and rest:
        alt = [min(rest, key=lambda e: (e["session"], e["sub"]))]
    alt.sort(key=lambda e: (e["session"], e["sub"]))
    return wert, alt, b, drainable


def triggers(entries, cur) -> bool:
    """Beansprucht der Drain diese Session? Zwei Lanes, zwei Auslöser (ODER-verknüpft).

    Der Alters-Auslöser ist kein Beiwerk: Ohne ihn hinge die Alters-Lane am Wert-Trigger und
    käme genau dann nie zum Zug, wenn sie am nötigsten ist – wenn nur noch Bagatellen übrig sind.
    Kalibrierung und Herleitung: process.md, „Lanes und Trigger".
    """
    drainable = [e for e in entries if e["status"].upper().startswith("NEU")]
    top = sum(unit_score(u) for u in wert_einheiten(drainable)[:TOP_N])
    alt = sum(1 for e in drainable if _alter(cur, e) > ALT_AB)
    return top >= TRIGGER_WERT or alt >= TRIGGER_ALT


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


def _vtag(entry) -> str:
    """Marker für ein vorhandenes `Vorprägung`-Feld (OBS-S112-8).

    Das Feld ist beim normalen `get` verborgen, damit es die Kandidatenbildung nicht prägt –
    genau deshalb muss auf seine Existenz hingewiesen werden, sonst wäre es so verloren wie
    ein getilgtes. Abzurufen ist es erst NACH der eigenen Kandidatenbildung.
    """
    return "  +Vorprägung" if entry.get("vorpraegung") else ""


# Offene Fragen hingen bis S116 hier mit dran – als der Drain-Vorschlag der einzige
# Session-Start-Vorlage-Mechanismus war. Seit `session-agenda.py` sind sie ein eigenes
# Geschwister-Modul (`open_questions.py`): anderer Tracker, anderer Ausgang (mit dem User
# klären statt im Drain entscheiden). Dieses Script trägt wieder nur den OBS-Drain.


def render(root: Path, entries):
    cur = current_session(root)
    wert, alt, b, drainable = compute(entries, cur)
    warn_far_parks(entries, cur)
    due = due_parked(entries, cur)
    resolved = [e for e in entries if is_resolved(e["status"])]

    # "Leer" nur wenn es WIRKLICH nichts zu tun gibt – fällige Wiedervorlagen und
    # aufgelöst-aber-unarchivierte Items müssen auch ohne NEU-Backlog erscheinen.
    if b == 0 and not due and not resolved:
        return "OBS-Drain – Backlog leer (keine drainbaren NEU-Items), kein Drain nötig."

    count = sum(len(u) for u in wert) + len(alt)
    selected = {e["id"] for u in wert for e in u} | {e["id"] for e in alt}
    # Eine Eskalationszeile („⚠ Backlog überfüllt … priorisieren") stand hier bis S117. Sie
    # sollte den Drain zum Tagesauftrag machen und hat das nie geschafft – das leistet die
    # Rangfolge in `session-agenda.py`, die den Drain bei erfülltem `triggers()` als Aufgabe zeigt.
    wuerdig = sum(len(u) for u in wert_einheiten(drainable))
    lines = [f"OBS-Drain – Backlog: {b} drainbar (NEU), davon {wuerdig} behandlungswürdig "
             f"(Score ≥ {WUERDIG_AB:g}) → heute {count} vorgeschlagen."]
    if wert:
        lines += ["", "Wert-Lane (nach Score; verwandte Einträge bilden eine Einheit):"]
        for u in wert:
            if len(u) > 1:
                lines.append(f"  - Einheit [Σ {unit_score(u):g}] – gemeinsam bearbeiten, "
                             f"Zusammengehörigkeit am Volltext prüfen:")
            for e in u:
                praefix = "    · " if len(u) > 1 else "  - "
                coloc = colocation(e, drainable, selected)
                ctag = f"  +Koloc: {', '.join(c['id'] for c in coloc)}" if coloc else ""
                lines.append(f"{praefix}{e['id']}  [{e['impact_raw']} × {e['freq_raw']} = "
                             f"{score(e):g}]  {e['title']}{ctag}{_vtag(e)}")
    if alt:
        titel = (f"Alters-Lane (älter als {ALT_AB} Sessions, Entscheidung erzwungen):"
                 if any(_alter(cur, e) > ALT_AB for e in alt)
                 else "Alters-Lane (ältestes, Entscheidung erzwungen):")
        lines += ["", titel]
        for e in alt:
            coloc = colocation(e, drainable, selected)
            ctag = f"  +Koloc: {', '.join(c['id'] for c in coloc)}" if coloc else ""
            lines.append(f"  - {e['id']}  (Alter ~{_age(cur, e['session'])} Sessions)  "
                         f"{e['title']}{ctag}{_vtag(e)}")
    if due:
        lines += ["", "Fällige Wiedervorlagen (geparkt, Termin erreicht → entscheiden):"]
        for e in due:
            bis = f"bis S{e['wiedervorlage']}" if e["wiedervorlage"] else "ohne Datum"
            lines.append(f"  - {e['id']}  (war geparkt {bis})  {e['title']}")
    if resolved:
        lines += ["", "Aufgelöst, noch in observations.md → ins Archiv verschieben"
                  " (`python3 .claude/scripts/obs-archive.py`): "
                  + ", ".join(e["id"] for e in resolved) + "."]
    lines += ["", "→ Skill `draining-observations` zum Abarbeiten (umsetzen / verwerfen / aufschieben)."]
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
