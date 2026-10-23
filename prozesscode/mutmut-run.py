#!/usr/bin/env python3
"""
Mutationstest des Prozess-Codes (mutmut) – mit Verdikt statt Rohausgabe.

Verwendung:
  python3 -m prozesscode.mutmut-run --mutate prozesscode.hooks.check-td-capture
  python3 -m prozesscode.mutmut-run --mutate prozesscode.anchors.pruefe
  python3 -m prozesscode.mutmut-run                 # alles (Stunden – siehe unten)
  python3 -m prozesscode.mutmut-run --verbose

`--mutate` nimmt einen Mutanten-Namensraum, keinen Dateipfad: mutmut adressiert Mutanten
über den **Modulpfad** (`prozesscode.hooks.check-td-capture.x_pruefe__mutmut_3`). Genau
deshalb liegt der Prozess-Code seit S129 in einem Paket – unter `.claude/` war er für
mutmut unerreichbar, weil `.claude` wegen des führenden Punkts kein gültiger Paketname ist.

**Der Volllauf ist kein Gate** (siehe `coding-guideline-python.md`, „Was nicht gilt"): Er
mutiert 15.000 Zeilen gegen eine 1.000er-Suite; das ist eine Sichtung für die Retro oder für
eine gezielte Frage an ein Modul. Gate ist nur die Sperrklinke je geändertem Modul (unten).

**`--ratchet` – die Sperrklinke.** Ein einzelner Lauf sagt, dass 34 Mutanten überleben,
aber nicht, ob es beim letzten Mal 12 waren. `--ratchet` hält den Score je Modul in
`mutation-baseline.json` fest und meldet einen Rückschritt als `✗`. Zwei Festlegungen:
Gleichstand geht durch (sonst wäre es eine Steigerungspflicht), und eine Verbesserung zieht
die Baseline nach (sonst friert sie beim ersten Glücksfall ein). Verglichen wird als Bruch,
nicht in gerundeten Prozenten.

Grenze des Bruchs: Zieht ein Refactoring gut getestete Logik in ein anderes Modul, verliert
das Quellmodul getötete Mutanten, seine Überlebenden bleiben – der Anteil sinkt ohne jeden
Güteverlust (S133: Feldwert-Regex aus zwei Capture-Hooks nach `eintrag_felder`). Dann die
Überlebenden vor/nach vergleichen und, wenn sie gleich sind, `mutation-baseline.json` von Hand
auf den neuen Stand setzen – mit Begründung in der Commit-Nachricht.

**Pflicht vor jedem Commit**, der ein Modul des Prozess-Codes ändert (Skill `committing`),
aber kein Hook je Edit; Grund und Laufzeiten in `docs/process/dev-workflow.md#DEV-python-werkzeuge`.

**Was die Statusarten bedeuten** – die Unterscheidung trägt die ganze Aussage:
  survived   Der Mutant lief, alle Tests blieben grün. Eine Lücke im Test, nicht im Code.
  no tests   Kein Test berührt die Stelle. Eine Lücke in der Abdeckung.
  timeout    Der Mutant erzeugte eine Endlosschleife o.ä. – oder die Tests liefen länger als
             mutmut schätzte (Grenze: `timeout_constant` in setup.cfg). Sagt nichts über die
             Testgüte; häufen sich Timeouts bei grünen Mutanten, ist die Grenze zu knapp.
  suspicious Lief ungewöhnlich lange, ohne zu scheitern. Wie timeout: kein Befund.
"""
import argparse
import json
import resource
import shutil
import subprocess
import sys
import tokenize
from pathlib import Path

from ._mutmut_ausnahmen import UNTER_MUTMUT_UEBERSPRUNGEN
from ._wrapper_output import emit

ROOT = Path(__file__).resolve().parent.parent
MUTMUT = ROOT / ".venv" / "bin" / "mutmut"

# Die festgehaltenen Scores der Sperrklinke. Getrackt, weil der Vergleich über Sessions
# hinweg tragen muss – eine Baseline im gitignorierten `mutants/` wäre nach jedem
# `--frisch` weg und die Klinke damit stumm.
BASELINE = Path(__file__).resolve().parent / "mutation-baseline.json"

# Hochzählen, sobald der Wrapper anders wertet, welche Mutanten zählen – wie ein mutmut-Update
# ändert das den Nenner, und die Klinke muss neu ansetzen statt zu vergleichen (s. `ratchet`).
# Stand 2: jeder Mutant zählt; Ausnahmen stehen im Code (Modulkonstante, Pragma).
# Stand 3: SIGXCPU (-24) ist ein Timeout wie bei mutmut 3.8, kein getöteter Mutant.
WERTUNG_STAND = 3

# Ein Volllauf kann Stunden dauern; der Deckel ist eine Reißleine, keine Erwartung.
TIMEOUT_S = 4 * 60 * 60

MAX_ZEILEN = 15

# Exit-Code eines Mutantenlaufs → Status. Nachbau von `mutmut.stats.status_by_exit_code`,
# bewusst hier und nicht importiert: mutmut liegt im venv, die Werkzeuge laufen auch unter dem
# System-Python – und vor 3.8 fehlte in mutmuts Tabelle -9, `results` starb daran mitten in der
# Ausgabe. Der Nachbau altert mit der Version; ein Test hält ihn gegen die installierte Tabelle.
STATUS_JE_EXIT_CODE: dict[int | None, str] = {
    1: "killed", 3: "killed",
    0: "survived",
    5: "no tests", 33: "no tests",
    2: "check was interrupted by user",
    34: "skipped", 35: "suspicious",
    36: "timeout", 255: "timeout",
    -24: "timeout", 24: "timeout", 152: "timeout",   # SIGXCPU – Zeitlimit, kein Testbefund
    37: "caught by type check",
    # Hart beendet (Endlosschleife, Speicherfraß) – über die Tests sagt das nichts.
    -11: "segfault", -9: "segfault",
    None: "not checked",
}

# Ein Code, den auch dieser Nachbau nicht kennt. Er darf höchstens einen Mutanten
# unbewertbar machen, nie die Auswertung aller übrigen (genau das war der mutmut-Bug).
UNBEKANNT = "unbekannt"

# Mutanten außerhalb des gelaufenen Ausschnitts. Sie gehören in keinen Nenner – sie wurden
# nicht gemessen.
NICHT_BEWERTET = "not checked"

# Der Normalfall. Steht in keiner Liste: 130 grüne Zeilen wären reines Rauschen.
GETOETET = "killed"

# Ein Befund ist nur, was eine Lücke belegt. Timeout und suspicious sagen etwas über den
# Mutanten aus, nicht über die Tests – sie als „überlebt" zu zählen wäre ein Fehlbefund.
BEFUND = ("survived", "no tests")

_ABBRUCH = (
    "✗ mutmut ist abgebrochen (Exit {code}): {zeile}\n"
    "  Kein Ergebnis dieses Laufs – die Ursache steht davor: --verbose.\n"
    "  Häufig ein Fehler im Testcode, der nur im Mutantenbaum auftritt (Import, Pfad).\n"
    "  Nennt sie eine Datei, die es im Repo nicht mehr gibt: --frisch (s. raeume_baum)."
)
_FEHLT = (
    "✗ Werkzeug-Umgebung fehlt ({pfad}).\n"
    "  Herstellen:\n"
    "    python3 -m venv .venv\n"
    "    .venv/bin/pip install -r requirements-dev.txt"
)


def lies_ergebnisse(ausschnitt: str | None = None) -> list[tuple[str, str]]:
    """(Mutantenname, Status) aus den `.meta`-Dateien des Mutantenbaums.

    **Nicht** über `mutmut results`, obwohl das dieselbe Quelle liest: Ein Mutant mit
    Exit `-9` (SIGKILL) bringt jenen Befehl mit `KeyError: -9` zu Fall – und zwar MITTEN
    in der Ausgabe. Der Wrapper las daraufhin 86 statt 646 Mutanten und bildete daraus
    einen Score, ohne etwas zu merken. Direkt gelesen entfällt der Absturz, der Subprozess
    über 11.000 Zeilen ebenfalls.

    `ausschnitt` beschränkt auf einen Namensraum. Nötig, weil der Baum kumulativ ist: Er
    hält, was JE bewertet wurde – ohne den Filter meldete ein Lauf auf Modul B die
    Überlebenden des vorigen Laufs auf Modul A als frischen Befund mit.

    Fail-open je Datei: Eine unlesbare `.meta` kostet ihr Modul, nicht alle.
    """
    paare: list[tuple[str, str]] = []
    for pfad in sorted((ROOT / "mutants").rglob("*.py.meta")):
        try:
            daten = json.loads(pfad.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for name, code in daten.get("exit_code_by_key", {}).items():
            paare.append((name, STATUS_JE_EXIT_CODE.get(code, UNBEKANNT)))

    if ausschnitt is None:
        return paare
    return [(name, status) for name, status in paare
            if name == ausschnitt or name.startswith(ausschnitt + ".")]


def _ist_mutantenname(ausschnitt: str) -> bool:
    """`…x_f__mutmut_3` benennt genau einen Mutanten, `prozesscode.anchors` einen Namensraum."""
    return "__mutmut_" in ausschnitt


def baue_verdikt(eintraege: list[tuple[str, str]],
                 pragmas: int = 0) -> tuple[str, list[str] | None]:
    """Verdikt und Detailzeilen aus den Ergebnissen.

    Nenner ist die Zahl der tatsächlich BEWERTETEN Mutanten – `not checked` lag außerhalb
    des Ausschnitts und ist nicht gemessen worden.

    `pragmas` sind die per `# pragma: no mutate` ausgenommenen Zeilen. mutmut erzeugt dort
    keine Mutanten und zählt sie nirgends – ungenannt wüchse die Ausnahme unbemerkt.
    """
    bewertet = [(n, s) for n, s in eintraege if s != NICHT_BEWERTET]
    auffaellig = [(n, s) for n, s in bewertet if s != GETOETET]

    nach_status: dict[str, list[str]] = {}
    for name, status in auffaellig:
        nach_status.setdefault(status, []).append(name)

    befunde = [(n, s) for n, s in auffaellig if s in BEFUND]
    umfang = f"{len(bewertet)} Mutant{'' if len(bewertet) == 1 else 'en'} bewertet"
    # Ein Lauf über ein großes Modul kommt nicht in einem Durchgang durch (gemessen: 242 von
    # 646 bei `check-bash-permission`). Ungenannt läse sich der Nenner wie das ganze Modul,
    # und der Score gälte für einen Ausschnitt, dessen Größe niemand kennt.
    offen = sum(1 for _n, s in eintraege if s == NICHT_BEWERTET)
    if offen:
        umfang += f", {offen} offen (weiterer Lauf nötig)"
    if pragmas:
        umfang += f", {pragmas} Zeile{'' if pragmas == 1 else 'n'} per Pragma ausgenommen"

    if not bewertet:
        # Keine Messung ist kein bestandener Lauf – „keiner überlebt" über eine leere Menge
        # wäre falsch-grün (S133: `--mutate …x_main` traf nichts).
        return (f"✗ mutmut: {umfang} – der Ausschnitt trifft keinen Mutanten. Die Namen haben "
                f"die Form `<paket>.<modul>.x_<funktion>__mutmut_<n>`; `--mutate` nimmt einen "
                f"Modul-Namensraum wie `prozesscode.anchors`."), None

    zeilen = [f"  {status:11s} {name}" for name, status in auffaellig][:MAX_ZEILEN]
    if len(auffaellig) > MAX_ZEILEN:
        zeilen.append(f"  … und {len(auffaellig) - MAX_ZEILEN} weitere")

    if not befunde:
        offen = sum(len(v) for k, v in nach_status.items() if k not in BEFUND)
        verdikt = f"✓ mutmut: {umfang}, keiner überlebt"
        if offen:
            verdikt += f" ({offen} ohne Aussage: timeout/suspicious)"
        return verdikt, zeilen or None

    teile = []
    if nach_status.get("survived"):
        teile.append(f"{len(nach_status['survived'])} überlebt")
    if nach_status.get("no tests"):
        teile.append(f"{len(nach_status['no tests'])} ohne deckenden Test")
    zeilen.append(
        "  „überlebt\" heißt: die Änderung an dieser Stelle bricht keinen Test – die Lücke "
        "liegt im Test.\n"
        "  „ohne deckenden Test\" heißt: kein Test berührt die Stelle überhaupt.\n"
        "  Eine Stelle ansehen: python3 -m prozesscode.mutmut-run --show <name>\n"
        "  Liegt sie in einem Meldungstext: als Modulkonstante auslagern (dort mutiert mutmut "
        "nicht) oder eigene Anweisung mit `# pragma: no mutate – <Grund>` am Ende (mitten "
        "in einem mehrzeiligen Ausdruck liest mutmut es nicht)."
    )
    return f"✗ mutmut: {umfang}, {', '.join(teile)}", zeilen


# --- Ausnahmen per Pragma ----------------------------------------------------

def pragma_zeilen(modul: str) -> int:
    """Zahl der `# pragma: no mutate`-Kommentare in der Quelle eines Moduls.

    Gezählt werden Kommentar-Token, nicht Textzeilen: mutmut liest das Pragma nur aus
    Kommentaren, ein String oder Docstring, der es erwähnt, nimmt nichts aus. Und nur außerhalb
    von Klammern – am Ende einer Anweisung oder auf eigener Zeile davor; mitten in einem
    mehrzeiligen Ausdruck übergeht mutmut den Kommentar.
    Fail-open: Eine fehlende oder unlesbare Quelle zählt null, statt den Lauf abzubrechen.
    """
    pfad = ROOT / (modul.replace(".", "/") + ".py")
    tiefe = anzahl = 0
    try:
        with pfad.open(encoding="utf-8") as quelle:
            for token in tokenize.generate_tokens(quelle.readline):
                if token.type == tokenize.OP and token.string in ("(", "[", "{"):
                    tiefe += 1
                elif token.type == tokenize.OP and token.string in (")", "]", "}"):
                    tiefe -= 1
                elif (token.type == tokenize.COMMENT and tiefe == 0
                      and "pragma:" in token.string and "no mutate" in token.string):
                    anzahl += 1
    except (OSError, SyntaxError, tokenize.TokenError):
        return 0
    return anzahl


# --- Sperrklinke -------------------------------------------------------------

def score(eintraege: list[tuple[str, str]]) -> tuple[int, int]:
    """(getötet, beurteilbar) – der Bruch, in dem die Testgüte eines Moduls gemessen wird.

    Beurteilbar sind getötete und überlebende Mutanten sowie die ohne deckenden Test:
    Bei allen dreien hat der Lauf etwas über die Tests erfahren. `timeout` und `suspicious`
    sagen etwas über den Mutanten aus, `not checked` gar nichts – beide stehen außerhalb
    des Bruchs, sonst verschöben sie den Score, ohne dass sich an den Tests etwas ändert.
    """
    beurteilbar = [s for _n, s in eintraege if s == GETOETET or s in BEFUND]
    return sum(1 for s in beurteilbar if s == GETOETET), len(beurteilbar)


def nach_modul(eintraege: list[tuple[str, str]]) -> dict[str, tuple[int, int]]:
    """{Modulpfad: (getötet, beurteilbar)} – die Baseline lebt je Modul, nicht je Lauf.

    Je Modul, weil mutmut dateigranular invalidiert: Eine geänderte Zeile wirft die
    Ergebnisse genau einer Datei weg, und genau deren Score ist danach neu zu vergleichen.
    """
    je_modul: dict[str, list[tuple[str, str]]] = {}
    for name, status in eintraege:
        je_modul.setdefault(name.rsplit(".", 1)[0], []).append((name, status))
    return {modul: score(paare) for modul, paare in je_modul.items()}


def offene_je_modul(eintraege: list[tuple[str, str]]) -> dict[str, int]:
    """{Modulpfad: Zahl der nicht bewerteten Mutanten} – der Nenner-Vorbehalt der Klinke.

    Je Modul und nicht je Lauf, aus demselben Grund wie `nach_modul`: Ein Teillauf in einem
    Modul darf die Aussage über ein anderes nicht entwerten.
    """
    je_modul: dict[str, int] = {}
    for name, status in eintraege:
        modul = name.rsplit(".", 1)[0]
        je_modul[modul] = je_modul.get(modul, 0) + (1 if status == NICHT_BEWERTET else 0)
    return je_modul


def _prozent(getoetet: int, beurteilbar: int) -> str:
    return f"{100 * getoetet / beurteilbar:.1f} %" if beurteilbar else "–"


def messung() -> str:
    """Kennung des Messinstruments: mutmut-Version und Stand des Textfilters.

    Die Version steht im Namen des `dist-info`-Ordners im venv – der Wrapper läuft unter dem
    System-Python, das mutmut nicht importieren kann. Fail-open: ohne Ordner `mutmut ?`.
    """
    venv_lib = MUTMUT.parent.parent / "lib"
    ordner = sorted(venv_lib.glob("python*/site-packages/mutmut-*.dist-info"))
    version = ordner[-1].name.removeprefix("mutmut-").removesuffix(".dist-info") if ordner else "?"
    return f"mutmut {version}, Wertung {WERTUNG_STAND}"


def ratchet(gemessen: dict[str, tuple[int, int]],
            baseline: dict,
            offen: dict[str, int] | None = None,
            messung: str | None = None) -> tuple[list[str], bool, dict | None]:
    """Vergleicht die gemessenen Scores gegen die Baseline.

    Rückgabe: (Meldezeilen, verschlechtert, fortzuschreibende Baseline oder None).

    Zwei Festlegungen, die den Mechanismus ausmachen:
    **Gleichstand geht durch** – sonst wäre es keine Sperrklinke, sondern eine
    Steigerungspflicht, und jede Änderung an einem Modul müsste dessen Score erhöhen.
    **Verbesserung wird fortgeschrieben** – sonst friert die Klinke beim ersten Glücksfall
    ein und deckt jede spätere Verschlechterung bis auf das alte Niveau.

    Verglichen wird als **Bruch**, nicht in gerundeten Prozenten: 100/300 und 33/100 sind
    auf zwei Nachkommastellen gleich, als Bruch ist das zweite kleiner. Eine Klinke, die
    kleine Rückschritte wegrundet, fängt genau die, die niemand bemerkt, nicht.

    **Ein unvollständiger Lauf wird nicht verglichen** (`offen`, S130). Kam der Lauf nicht
    durch alle Mutanten, steht der Score über einem anderen Nenner als die Baseline – die
    Differenz misst dann den Ausschnitt, nicht die Tests. Belegt an
    `check-bash-permission`: 237 bewertet gegen eine Baseline von 241, gemeldet als
    „53.5 % → 53.0 % VERSCHLECHTERT". Eine erfundene Verschlechterung ist teurer als keine
    Aussage – sie lässt Tests schreiben, die keine Lücke schließen, und stumpft die Klinke
    für den echten Fall ab. Fortgeschrieben wird dann ebenfalls nicht, auch keine
    Verbesserung: Ein günstiger Ausschnitt als neue Messlatte deckte jeden späteren
    Rückschritt bis auf dieses Niveau.

    **Ein anderes Messinstrument wird nicht verglichen** (`messung`): mutmut 3.8 erzeugte
    für dasselbe Modul 94 statt 39 Mutanten. Weicht die Kennung der Baseline ab (oder fehlt
    sie), wird neu gesetzt und das so benannt – ein Rückschritt, der zeitgleich mit dem
    Wechsel entstand, bleibt dabei unentdeckt; ein Vergleich über zwei Instrumente fände ihn
    aber ebenso wenig. `None` prüft keine Kennung.
    """
    offen = offen or {}
    zeilen: list[str] = []
    verschlechtert = False
    neu = dict(baseline)  # fremde Module bleiben unberührt – ein Ausschnitt löscht nichts
    geaendert = False
    kennung = {"messung": messung} if messung is not None else {}

    for modul in sorted(gemessen):
        getoetet, beurteilbar = gemessen[modul]
        if not beurteilbar:
            zeilen.append(f"  {modul}: kein bewerteter Mutant – nichts zu vergleichen")
            continue

        if offen.get(modul):
            zeilen.append(f"  {modul}: {_prozent(getoetet, beurteilbar)} über "
                          f"{beurteilbar} von {beurteilbar + offen[modul]} Mutanten – "
                          f"Lauf unvollständig, kein Vergleich mit der Baseline")
            zeilen.append("    Erneut laufen lassen; bleibt die Zahl stehen, kommt mutmut "
                          "auf diesem Modul nicht durch – dann ist die Klinke hier ohne "
                          "Aussage, und das Modul braucht eine eigene Untersuchung.")
            continue

        vorher = baseline.get(modul)
        if vorher is None:
            zeilen.append(f"  {modul}: {_prozent(getoetet, beurteilbar)} – neu aufgenommen")
            neu[modul] = {"getoetet": getoetet, "beurteilbar": beurteilbar, **kennung}
            geaendert = True
            continue

        if messung is not None and vorher.get("messung") != messung:
            zeilen.append(f"  {modul}: {_prozent(getoetet, beurteilbar)} – Baseline neu gesetzt "
                          f"(Messung {vorher.get('messung', 'ohne Kennung')} → {messung}), "
                          f"kein Vergleich")
            neu[modul] = {"getoetet": getoetet, "beurteilbar": beurteilbar, **kennung}
            geaendert = True
            continue

        alt_g, alt_b = vorher["getoetet"], vorher["beurteilbar"]
        # Kreuzmultiplikation statt Division: exakt, ohne Float-Rundung.
        links, rechts = getoetet * alt_b, alt_g * beurteilbar
        if links < rechts:
            verschlechtert = True
            zeilen.append(f"  {modul}: {_prozent(alt_g, alt_b)} → "
                          f"{_prozent(getoetet, beurteilbar)}  VERSCHLECHTERT")
        elif links > rechts:
            zeilen.append(f"  {modul}: {_prozent(alt_g, alt_b)} → "
                          f"{_prozent(getoetet, beurteilbar)}  (Baseline nachgezogen)")
            neu[modul] = {"getoetet": getoetet, "beurteilbar": beurteilbar, **kennung}
            geaendert = True
        else:
            zeilen.append(f"  {modul}: {_prozent(getoetet, beurteilbar)} – unverändert")

    # Eine gerissene Klinke schreibt NIE fort: Sonst wäre der schlechtere Stand beim
    # nächsten Lauf die neue Messlatte, und der Rückschritt hätte sich selbst legalisiert.
    if verschlechtert or not geaendert:
        return zeilen, verschlechtert, None
    return zeilen, verschlechtert, neu


def klinken_verdikt(befund: str, *, schlechter: bool, nachgezogen: bool,
                    ohne_aussage: list[str] | None = None) -> tuple[str, int]:
    """Bei `--ratchet` entscheidet die Klinke über ✓/✗, nicht die Zahl der Befunde.

    Ein Modul mit 31 überlebenden Mutanten ist ein bekannter Zustand, kein neuer Fehler –
    die Klinke fragt, ob er SCHLECHTER geworden ist. Bliebe das Befund-✗ stehen, meldete
    `--ratchet` auf jedem Modul mit Altlast dauerhaft rot und gäbe kein Signal mehr, das
    sich vom Rauschen abhebt. Der Befund selbst bleibt als Zeile darunter sichtbar.

    **Nicht verglichen ist nicht gehalten** (`ohne_aussage`): Kam der Lauf in einem
    Modul nicht durch, wird es nicht verglichen (siehe `ratchet`) – ein ✓ läse sich dann als
    Beleg für Tests, die nie gegen den fehlenden Teil liefen. Ein Rückschritt in einem
    vollständigen Modul geht trotzdem vor: Er ist ein Befund, der Teillauf nur keiner.
    """
    nackt = befund.lstrip("✓✗ ")
    if schlechter:
        return (f"✗ Sperrklinke gerissen – die Testgüte ist unter den festgehaltenen "
                f"Stand gefallen\n  {nackt}"), 1
    if ohne_aussage:
        return (f"⚠ Sperrklinke ohne Aussage – Lauf unvollständig für "
                f"{', '.join(ohne_aussage)} (Einzelheiten oben)\n  {nackt}"), 1
    nachsatz = " (Baseline nachgezogen)" if nachgezogen else ""
    return f"✓ Sperrklinke gehalten{nachsatz}\n  {nackt}", 0


def lies_baseline() -> dict:
    """Die festgehaltenen Scores, oder `{}`.

    Fail-open: Eine fehlende oder unlesbare Datei heißt „kein Vorher", nicht „Abbruch" –
    sonst nähme ein kaputtes JSON das Werkzeug mit, das den Befund liefern soll.
    """
    try:
        return json.loads(BASELINE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def schreibe_baseline(stand: dict) -> None:
    BASELINE.write_text(json.dumps(stand, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ausnahmen_nachsatz() -> str:
    """Nennt die übersprungenen Tests im Verdikt – sonst wüchse die Liste unbemerkt.

    Eine Ausnahme, die nur in einer Datei steht, wird zur Formalie (OBS-S112-8). Hier steht
    sie in jedem Ergebnis, das jemand ansieht.
    """
    n = len(UNTER_MUTMUT_UEBERSPRUNGEN)
    if not n:
        return ""
    return (f"\n  ({n} Test(e) unter mutmut übersprungen – Begründungen in "
            f"prozesscode/_mutmut_ausnahmen.py)")


def raeume_baum() -> None:
    """Wirft `mutants/` weg – den Arbeitsbaum, den mutmut selbst anlegt und wiederverwendet.

    Meist unnötig: mutmut vergleicht die mtime jeder Quelldatei mit ihrer Kopie und mutiert
    eine geänderte Datei neu, wobei es ihre alten Ergebnisse verwirft. Stale Mutanten gibt
    es also nicht. Eine Lücke bleibt: Die Test-zu-Funktion-Zuordnung in
    `mutants/mutmut-stats.json` wird beim Laden nur ERGÄNZT (`|=`), nie bereinigt. Ein
    GEÄNDERTER – nicht neuer – Test behält dort seine alte Zuordnung; mutmut fährt dann für
    einen Mutanten die falschen Tests und meldet ihn womöglich als überlebend, obwohl der
    geänderte Test ihn tötet. Vor einer belastbaren Sichtung deshalb hiermit räumen.
    Ebenso nach einer GELÖSCHTEN Datei: mutmut kopiert in den Baum, entfernt dort aber
    nichts – eine kaputte, im Repo schon gelöschte Testdatei bricht jeden Lauf weiter ab.
    """
    shutil.rmtree(ROOT / "mutants", ignore_errors=True)


def _ohne_core_dump() -> None:
    """Kein Core-Dump für mutmut und seine Worker.

    mutmut beendet hängende Mutanten mit SIGXCPU, und das schreibt einen Dump. Unter WSL leitet
    `core_pattern` ihn als Datei nach Windows (`wsl-crashes`), einige hundert MB je Mutant. Ein
    Lauf über den Bash-Guard verbrachte so 95 % seiner Worker-Zeit mit 60 Timeouts.
    0 genügt nicht: Bei einem Pipe-Ziel wirkt erst 1 (core(5)).
    mutmut zählt den Mutanten weiterhin als Timeout (Exit -24).
    """
    _, hart = resource.getrlimit(resource.RLIMIT_CORE)
    resource.setrlimit(resource.RLIMIT_CORE, (1, hart))


def _laufe(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(MUTMUT), *argv], cwd=ROOT, capture_output=True,
                          text=True, timeout=TIMEOUT_S, preexec_fn=_ohne_core_dump)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mutate", metavar="NAMENSRAUM",
                        help="Nur diesen Mutanten-Namensraum, z.B. prozesscode.anchors")
    parser.add_argument("--ratchet", action="store_true",
                        help="Score je Modul gegen die Baseline halten (s. Modul-Docstring)")
    parser.add_argument("--frisch", action="store_true",
                        help="mutants/ vorher wegwerfen (nach geänderten oder gelöschten "
                             "Dateien – s. raeume_baum)")
    parser.add_argument("--verbose", action="store_true", help="Vollständige Ausgabe")
    # Der Rohaufruf `mutmut show` ist per Bash-Hook gesperrt (dort zusammen mit run/results);
    # ohne diesen Weg zeigte das Verdikt auf eine Sackgasse.
    parser.add_argument("--show", metavar="MUTANT",
                        help="Diff eines Mutanten zeigen (Name aus dem Verdikt), kein Lauf")
    # Springt ein Mutant zwischen zwei Läufen um, wackelt einer der Tests, die mutmut für ihn
    # auswählt – nur mutmut weiß, welche das sind.
    parser.add_argument("--tests-for", metavar="MUTANT",
                        help="Tests nennen, die mutmut für diesen Mutanten auswählt, kein Lauf")
    args = parser.parse_args(argv)

    if not MUTMUT.is_file():
        print(_FEHLT.format(pfad=MUTMUT))
        return 2

    if args.show or args.tests_for:
        gezeigt = (_laufe("show", args.show) if args.show
                   else _laufe("tests-for-mutant", args.tests_for))
        print(gezeigt.stdout + gezeigt.stderr, end="")
        return gezeigt.returncode

    if args.frisch:
        raeume_baum()

    filter_ = []
    if args.mutate:
        filter_ = [args.mutate if _ist_mutantenname(args.mutate) else f"{args.mutate}.*"]
    lauf = _laufe("run", *filter_)
    lauf_ausgabe = lauf.stdout + lauf.stderr

    # Bricht der Lauf ab (kaputte Suite, fehlende Stats, Absturz), sagt jede Zahl danach
    # nichts: Die Ergebnisse im Baum stammen aus einem früheren Lauf. Erkannt am Exit-Code –
    # mutmut endet nur in seinen Abbruchpfaden mit ≠ 0, ihre Texte wechseln je Version.
    if lauf.returncode != 0:
        zeilen = lauf_ausgabe.strip().splitlines()
        emit(verbose=args.verbose, output=lauf_ausgabe,
             verdict=_ABBRUCH.format(code=lauf.returncode,
                                     zeile=zeilen[-1] if zeilen else "keine Ausgabe"))
        return 1

    # `--all true`: ohne die getöteten Mutanten ließe sich der Nenner nicht bilden.
    eintraege = lies_ergebnisse(args.mutate)

    pragmas = sum(pragma_zeilen(modul) for modul in {n.rsplit(".", 1)[0] for n, _s in eintraege})
    verdikt, details = baue_verdikt(eintraege, pragmas)
    code = 1 if verdikt.startswith("✗") else 0

    if args.ratchet:
        gemessen, offen = nach_modul(eintraege), offene_je_modul(eintraege)
        zeilen, schlechter, fortschreibung = ratchet(gemessen, lies_baseline(), offen,
                                                     messung())
        if fortschreibung is not None:
            schreibe_baseline(fortschreibung)
        details = (details or []) + [""] + zeilen
        ohne_aussage = sorted(m for m, (_g, beurteilbar) in gemessen.items()
                              if beurteilbar and offen.get(m))
        verdikt, code = klinken_verdikt(verdikt, schlechter=schlechter,
                                        nachgezogen=fortschreibung is not None,
                                        ohne_aussage=ohne_aussage)

    if args.mutate:
        verdikt += f"\n  (Ausschnitt: {args.mutate})"
    verdikt += ausnahmen_nachsatz()

    emit(verbose=args.verbose, output=lauf_ausgabe, verdict=verdikt, details=details)
    return code


if __name__ == "__main__":
    sys.exit(main())
