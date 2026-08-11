#!/usr/bin/env python3
"""Fällig gewordene technische Schuld aus `docs/tech-debt.md`.

Der Backstop für **Waisen-TD** (OBS-S099-1): Schuld in Bereichen, zu denen nie ein Lauf kommt.
`implementing-scenario` Schritt 0 P5 sichtet TD **bereichsgebunden** und schließt den Rest
ausdrücklich aus („TD ohne Bezug zu den berührten Bereichen bleibt bewusst außen vor"). Genau
dieses Komplement deckt dieses Modul ab – es prüft nicht, ob ein Lauf hinkommt, sondern ob der
im `**Fällig:**`-Kopf genannte **Anker eingetreten** ist.

Bewusst NICHT alters-basiert: Im Bestand ist TD-S044-1 rund 73 Sessions alt und wartet völlig
zu Recht auf US-602. Jede Alters-Schwelle ≤ 16 flaggte 15 von 17 Einträgen und produzierte
dieselben drei nicht-handlungsfähigen Zeilen bei jedem Session-Start.

Vier Sorten von Meldungen, alle aus `td_anchors.faellig_gruende`:
  - der Anker ist eingetreten (Phase erreicht, Story aktuell, Termin erreicht, Vorgänger behoben)
  - der Story-Anker ist ungültig geworden (die Story hat inzwischen Szenarien → umhängen)
  - das referenzierte Szenario existiert nicht mehr (Titel gedriftet)
  - das Szenario ist implementiert, die Schuld wurde beim Lauf nicht mitgenommen

Die letzte ist die wertvollste: Sie fängt den Fall „der Lauf ist durch, der Eintrag blieb
liegen", den sonst niemand bemerkt – nachweislich vorgekommen, als ein Lauf den Toast-Bereich
veränderte, während der zugehörige TD-Eintrag unbemerkt liegen blieb.
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import td_anchors  # noqa: E402

TD_FILE = "docs/tech-debt.md"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def faellige(root: Path) -> list[tuple[str, list[str]]]:
    """(TD-ID, Gründe) für jeden Eintrag, dessen Anker eingetreten oder defekt ist."""
    pfad = root / TD_FILE
    if not pfad.is_file():
        return []
    ktx = td_anchors.lade_kontext(root)
    return [
        (tid, gruende)
        for tid, wert in td_anchors.td_faelligkeiten(pfad.read_text(encoding="utf-8")).items()
        if (gruende := td_anchors.faellig_gruende(tid, wert, ktx))
    ]


def fuer_szenarien(root: Path, titel: list[str]) -> list[tuple[str, str]]:
    """(TD-ID, Fällig-Wert) für Einträge, die auf eines der gegebenen Szenarien ankern.

    Aufrufstelle: `implementing-scenario` Schritt 6.1 – nach einem erledigten Lauf mit dessen
    Szenario-Titeln aufgerufen, damit der TD-Abgleich mechanisch statt aus Lese-Disziplin
    passiert.
    """
    pfad = root / TD_FILE
    if not pfad.is_file():
        return []
    gesucht = set(titel)
    treffer = []
    for tid, wert in td_anchors.td_faelligkeiten(pfad.read_text(encoding="utf-8")).items():
        anker, _ = td_anchors.parse(wert)
        if any(a.art == td_anchors.SZENARIO and a.wert in gesucht for a in anker):
            treffer.append((tid, wert))
    return treffer


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--szenarien", nargs="+", metavar="TITEL",
                    help="TD-Einträge listen, die auf diese Szenario-Titel ankern "
                         "(implementing-scenario Schritt 6.1, nach einem erledigten Lauf)")
    args = ap.parse_args()
    root = repo_root()

    if args.szenarien:
        treffer = fuer_szenarien(root, args.szenarien)
        if not treffer:
            print("(kein TD-Eintrag ankert auf diesen Szenarien)")
            return 0
        print("TD-Einträge, die auf Szenarien dieses Laufs ankern – je entscheiden, ob der Lauf "
              "sie behoben hat (dann Eintrag entfernen) oder nicht (dann begründen):")
        for tid, wert in treffer:
            print(f"  - {tid}: {wert}")
        return 0

    treffer = faellige(root)
    if not treffer:
        print("(keine fällige technische Schuld)")
        return 0
    for tid, gruende in treffer:
        print(f"  - {tid}: {'; '.join(gruende)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
