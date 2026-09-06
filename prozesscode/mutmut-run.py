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

**Warum kein Gate:** wie bei der Coverage (siehe `coding-guideline-python.md`, „Was nicht
gilt"). Ein Volllauf mutiert 15.000 Zeilen gegen eine 1.000er-Suite; das ist eine Sichtung
für die Retro oder für eine gezielte Frage an ein Modul, kein Hook.

**`--ratchet` – die Sperrklinke.** Ein einzelner Lauf sagt, dass 34 Mutanten überleben,
aber nicht, ob es beim letzten Mal 12 waren. `--ratchet` hält den Score je Modul in
`mutation-baseline.json` fest und meldet einen Rückschritt als `✗`. Zwei Festlegungen:
Gleichstand geht durch (sonst wäre es eine Steigerungspflicht), und eine Verbesserung zieht
die Baseline nach (sonst friert sie beim ersten Glücksfall ein). Verglichen wird als Bruch,
nicht in gerundeten Prozenten.

Bewusst **kein Gate** – kein Hook, kein Commit-Zwang. Gemessen dauert ein Modul mittlerer
Größe 84 s, die großen liegen darüber; ein Zwang in dieser Größenordnung erzeugt den Druck,
unter dem er umgangen wird. Die Klinke greift, wenn jemand sie zieht.

**Was die Statusarten bedeuten** – die Unterscheidung trägt die ganze Aussage:
  survived   Der Mutant lief, alle Tests blieben grün. Eine Lücke im Test, nicht im Code.
  no tests   Kein Test berührt die Stelle. Eine Lücke in der Abdeckung.
  timeout    Der Mutant erzeugte eine Endlosschleife o.ä. Sagt nichts über die Testgüte.
  suspicious Lief ungewöhnlich lange, ohne zu scheitern. Wie timeout: kein Befund.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from ._mutmut_ausnahmen import UNTER_MUTMUT_UEBERSPRUNGEN
from ._wrapper_output import emit

ROOT = Path(__file__).resolve().parent.parent
MUTMUT = ROOT / ".venv" / "bin" / "mutmut"

# Die festgehaltenen Scores der Sperrklinke. Getrackt, weil der Vergleich über Sessions
# hinweg tragen muss – eine Baseline im gitignorierten `mutants/` wäre nach jedem
# `--frisch` weg und die Klinke damit stumm.
BASELINE = Path(__file__).resolve().parent / "mutation-baseline.json"

# Ein Volllauf kann Stunden dauern; der Deckel ist eine Reißleine, keine Erwartung.
TIMEOUT_S = 4 * 60 * 60

MAX_ZEILEN = 15

# Exit-Code eines Mutantenlaufs → Status. Nachbau von `mutmut.__main__.status_by_exit_code`,
# bewusst hier und nicht importiert: Das CLI-Modul zöge beim Import die halbe mutmut-Laufzeit
# mit, und der Grund für diesen Nachbau ist gerade eine Lücke DARIN (s. -9 unten).
STATUS_JE_EXIT_CODE: dict[int | None, str] = {
    1: "killed", 3: "killed", -24: "killed",
    0: "survived",
    5: "no tests", 33: "no tests",
    2: "check was interrupted by user",
    34: "skipped", 35: "suspicious",
    36: "timeout", 24: "timeout", 152: "timeout", 255: "timeout",
    # SIGKILL – der Kernel hat den Mutanten hart beendet, meist wegen einer Endlosschleife
    # oder eines Speicherfraßes, den die Mutation erzeugt hat. mutmut kennt diesen Code
    # NICHT: `results` stirbt daran mit `KeyError: -9`, mitten in der Ausgabe. Wie ein
    # Timeout gewertet – über die Tests sagt er nichts.
    -9: "timeout",
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
    return [(name, status) for name, status in paare if name.startswith(ausschnitt + ".")]


def baue_verdikt(eintraege: list[tuple[str, str]],
                 ignorieren: set[str] | None = None) -> tuple[str, list[str] | None]:
    """Verdikt und Detailzeilen aus den Ergebnissen.

    Nenner ist die Zahl der tatsächlich BEWERTETEN Mutanten – `not checked` lag außerhalb
    des Ausschnitts und ist nicht gemessen worden.

    `ignorieren` nimmt die Mutanten an Meldungstexten aus der Wertung (s. `string_mutanten`).
    Sie werden trotzdem **gezählt und genannt**: Die Stellen sind ungeprüft, nur nicht
    sinnvoll prüfbar – das zu verschweigen wäre eine andere Aussage als die gemessene.
    """
    ignorieren = ignorieren or set()
    an_texten = sum(1 for n, s in eintraege if n in ignorieren and s in BEFUND)
    eintraege = [(n, s) for n, s in eintraege if n not in ignorieren]

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
    if an_texten:
        # Bewusst nur die ÜBERLEBENDEN: Die getöteten Text-Mutanten sind kein Befund, und
        # sie mitzuzählen ließe die Zahl größer wirken, als der ausgeklammerte Befund ist.
        umfang += (f", +{an_texten} überlebende an Meldungstexten (nicht sinnvoll tötbar – "
                   f"s. string_mutanten)")

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
        "  Eine Stelle ansehen: .venv/bin/mutmut show <name>"
    )
    return f"✗ mutmut: {umfang}, {', '.join(teile)}", zeilen


# --- Mutanten an Meldungstexten ----------------------------------------------

# So sieht ein Mutantenbaum aus: je Funktion `x_<name>__mutmut_orig` plus je Mutation eine
# durchnummerierte Kopie.
_MUTANTEN_FUNKTION = re.compile(r"^def (x_(\w+)__mutmut_(orig|\d+))\(", re.M)


def string_mutanten(modul: str) -> set[str]:
    """Namen der Mutanten, die nur einen Stringinhalt verändern.

    mutmut umschließt ihn mit `XX…XX`: aus `"Anker setzen"` wird `"XXAnker setzenXX"`. Der
    Text bleibt damit **Substring** – ein `in`-Test kann so einen Mutanten prinzipiell nicht
    töten, und der einzige, der es könnte (exakter Vergleich der ganzen Meldung), bricht bei
    jeder Umformulierung. Solche Mutanten sind deshalb kein Befund über die Testgüte.

    Gemessen an drei Modulen (S129) stellen sie 48 %, 53 % und 79 % aller Überlebenden.
    Ohne diese Erkennung risse die Sperrklinke bei jeder neuen Erklärzeile in einer
    Guard-Meldung – in einem Projekt, dessen Meldungen den Ausweg nennen sollen, laufend.

    Fail-open: Ohne Baum wird nichts ausgeklammert, statt den Lauf abzubrechen.
    """
    pfad = ROOT / "mutants" / (modul.replace(".", "/") + ".py")
    try:
        text = pfad.read_text(encoding="utf-8")
    except OSError:
        return set()

    treffer = list(_MUTANTEN_FUNKTION.finditer(text))
    koerper = {m.group(1): (m.group(2), text[m.end():treffer[i + 1].start()
                                             if i + 1 < len(treffer) else len(text)])
               for i, m in enumerate(treffer)}
    originale = {fn: rumpf for name, (fn, rumpf) in koerper.items()
                 if name.endswith("__mutmut_orig")}

    # `XX` nur dann eine Mutation, wenn es im Original derselben Funktion fehlt – sonst
    # meldete jede Konstante, die selbst „XX" enthält, einen Fehltreffer.
    return {f"{modul}.{name}" for name, (fn, rumpf) in koerper.items()
            if not name.endswith("__mutmut_orig")
            and "XX" in rumpf and "XX" not in originale.get(fn, "")}


# --- Sperrklinke -------------------------------------------------------------

def score(eintraege: list[tuple[str, str]],
          ignorieren: set[str] | None = None) -> tuple[int, int]:
    """(getötet, beurteilbar) – der Bruch, in dem die Testgüte eines Moduls gemessen wird.

    Beurteilbar sind getötete und überlebende Mutanten sowie die ohne deckenden Test:
    Bei allen dreien hat der Lauf etwas über die Tests erfahren. `timeout` und `suspicious`
    sagen etwas über den Mutanten aus, `not checked` gar nichts – beide stehen außerhalb
    des Bruchs, sonst verschöben sie den Score, ohne dass sich an den Tests etwas ändert.
    """
    ignorieren = ignorieren or set()
    beurteilbar = [s for n, s in eintraege
                   if (s == GETOETET or s in BEFUND) and n not in ignorieren]
    return sum(1 for s in beurteilbar if s == GETOETET), len(beurteilbar)


def nach_modul(eintraege: list[tuple[str, str]],
               ignorieren: set[str] | None = None) -> dict[str, tuple[int, int]]:
    """{Modulpfad: (getötet, beurteilbar)} – die Baseline lebt je Modul, nicht je Lauf.

    Je Modul, weil mutmut dateigranular invalidiert: Eine geänderte Zeile wirft die
    Ergebnisse genau einer Datei weg, und genau deren Score ist danach neu zu vergleichen.
    """
    je_modul: dict[str, list[tuple[str, str]]] = {}
    for name, status in eintraege:
        je_modul.setdefault(name.rsplit(".", 1)[0], []).append((name, status))
    return {modul: score(paare, ignorieren) for modul, paare in je_modul.items()}


def _prozent(getoetet: int, beurteilbar: int) -> str:
    return f"{100 * getoetet / beurteilbar:.1f} %" if beurteilbar else "–"


def ratchet(gemessen: dict[str, tuple[int, int]],
            baseline: dict) -> tuple[list[str], bool, dict | None]:
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
    """
    zeilen: list[str] = []
    verschlechtert = False
    neu = dict(baseline)  # fremde Module bleiben unberührt – ein Ausschnitt löscht nichts
    geaendert = False

    for modul in sorted(gemessen):
        getoetet, beurteilbar = gemessen[modul]
        if not beurteilbar:
            zeilen.append(f"  {modul}: kein bewerteter Mutant – nichts zu vergleichen")
            continue

        vorher = baseline.get(modul)
        if vorher is None:
            zeilen.append(f"  {modul}: {_prozent(getoetet, beurteilbar)} – neu aufgenommen")
            neu[modul] = {"getoetet": getoetet, "beurteilbar": beurteilbar}
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
            neu[modul] = {"getoetet": getoetet, "beurteilbar": beurteilbar}
            geaendert = True
        else:
            zeilen.append(f"  {modul}: {_prozent(getoetet, beurteilbar)} – unverändert")

    # Eine gerissene Klinke schreibt NIE fort: Sonst wäre der schlechtere Stand beim
    # nächsten Lauf die neue Messlatte, und der Rückschritt hätte sich selbst legalisiert.
    if verschlechtert or not geaendert:
        return zeilen, verschlechtert, None
    return zeilen, verschlechtert, neu


def klinken_verdikt(befund: str, *, schlechter: bool, nachgezogen: bool) -> tuple[str, int]:
    """Bei `--ratchet` entscheidet die Klinke über ✓/✗, nicht die Zahl der Befunde.

    Ein Modul mit 31 überlebenden Mutanten ist ein bekannter Zustand, kein neuer Fehler –
    die Klinke fragt, ob er SCHLECHTER geworden ist. Bliebe das Befund-✗ stehen, meldete
    `--ratchet` auf jedem Modul mit Altlast dauerhaft rot und gäbe kein Signal mehr, das
    sich vom Rauschen abhebt. Der Befund selbst bleibt als Zeile darunter sichtbar.
    """
    nackt = befund.lstrip("✓✗ ")
    if schlechter:
        return (f"✗ Sperrklinke gerissen – die Testgüte ist unter den festgehaltenen "
                f"Stand gefallen\n  {nackt}"), 1
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
    """
    shutil.rmtree(ROOT / "mutants", ignore_errors=True)


def _laufe(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(MUTMUT), *argv], cwd=ROOT, capture_output=True,
                          text=True, timeout=TIMEOUT_S)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mutate", metavar="NAMENSRAUM",
                        help="Nur diesen Mutanten-Namensraum, z.B. prozesscode.anchors")
    parser.add_argument("--ratchet", action="store_true",
                        help="Score je Modul gegen die Baseline halten (s. Modul-Docstring)")
    parser.add_argument("--frisch", action="store_true",
                        help="mutants/ vorher wegwerfen (nach geänderten TESTS – s. raeume_baum)")
    parser.add_argument("--verbose", action="store_true", help="Vollständige Ausgabe")
    args = parser.parse_args(argv)

    if not MUTMUT.is_file():
        print(_FEHLT.format(pfad=MUTMUT))
        return 2

    if args.frisch:
        raeume_baum()

    filter_ = [f"{args.mutate}.*"] if args.mutate else []
    lauf = _laufe("run", *filter_)
    lauf_ausgabe = lauf.stdout + lauf.stderr

    # Bricht der Lauf ab (kaputte Suite, fehlende Stats), sagt jede Zahl danach nichts.
    if "failed to collect stats" in lauf_ausgabe or "no active tests found" in lauf_ausgabe:
        emit(verbose=args.verbose, output=lauf_ausgabe,
             verdict="✗ mutmut kam nicht bis zum ersten Mutanten – die Suite läuft im "
                     "Mutantenbaum nicht durch")
        return 1

    # `--all true`: ohne die getöteten Mutanten ließe sich der Nenner nicht bilden.
    eintraege = lies_ergebnisse(args.mutate)

    # Je berührtem Modul: die Mutanten an Meldungstexten aus der Wertung nehmen.
    an_texten: set[str] = set()
    for modul in {n.rsplit(".", 1)[0] for n, _s in eintraege}:
        an_texten |= string_mutanten(modul)

    verdikt, details = baue_verdikt(eintraege, an_texten)
    code = 1 if verdikt.startswith("✗") else 0

    if args.ratchet:
        zeilen, schlechter, fortschreibung = ratchet(
            nach_modul(eintraege, an_texten), lies_baseline())
        if fortschreibung is not None:
            schreibe_baseline(fortschreibung)
        details = (details or []) + [""] + zeilen
        verdikt, code = klinken_verdikt(verdikt, schlechter=schlechter,
                                        nachgezogen=fortschreibung is not None)

    if args.mutate:
        verdikt += f"\n  (Ausschnitt: {args.mutate})"
    verdikt += ausnahmen_nachsatz()

    emit(verbose=args.verbose, output=lauf_ausgabe, verdict=verdikt, details=details)
    return code


if __name__ == "__main__":
    sys.exit(main())
