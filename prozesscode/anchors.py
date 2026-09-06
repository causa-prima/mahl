#!/usr/bin/env python3
"""Abschnitts-Anker und ihre Verweise – Index, Prüfung in beide Richtungen, CLI.

Warum (OBS-S112-7): Verweise zwischen Projektdokumenten stehen als Prosa – „§2",
„Sektion Security", „Schritt 4". Kein Werkzeug kann prüfen, ob das Ziel existiert; Verweise
sterben unbemerkt in beide Richtungen. Und weil sie auf *Nummern* zeigen, müssen die Nummern
stabil bleiben: Wächst der Inhalt, entstehen Einschübe wie `4b`/`4c` statt einer
Neunummerierung – die Gliederung richtet sich nach der Verweisbarkeit statt nach dem Inhalt.

**Das Schema** (User-Entscheid S124). Der Anker ist ein HTML-Anchor über der Überschrift, der
Verweis ein echter Markdown-Link:

    <a id="CGT-result"></a>                                    ← Definition
    ## Result-Typen
    … siehe [CGT-result](../guidelines/typescript.md#CGT-result) …   ← Verweis  anchor-ok

Kein Eigenbau, sondern die etablierte Lösung für stabile Markdown-Anker: **klickbar** in
GitHub und IDE, grep-bar für Agenten, stabil gegen Titeländerung UND Umsortieren. Die
GitHub-eigenen Auto-Anchors leisten das nicht – sie leiten sich aus dem Titel ab, jede
Umbenennung bricht sie; ein Anker im sichtbaren Überschriftentext wiederum wäre nicht
klickbar. Der Name ist ein **Slug, keine Nummer** – Nummern sind das Problem, ein Slug
übersteht Umsortieren. Damit entfällt der Zwang, Abschnitte überhaupt zu nummerieren.

**Tracker-IDs sind bewusst keine Anker.** `TD-S089-1`, `OBS-S124-1`, `ADR-S112-5` haben eigene
Prüfer (`decisions.py check`, `check-dangling-refs.py`); ein gemeinsames Muster würde beide
Mechanismen aneinanderbinden, ohne dass einer davon besser würde.

Geprüft wird in beide Richtungen, weil eine allein ein stummes Opt-out wäre: Wer den Anker
löscht, merkte nichts; wer den Verweis liest, fände nichts. Dieselbe Überlegung wie bei
`check-dangling-refs.py` für volatile Tracker-IDs.
"""
import argparse
import os
import re
import sys
from collections import defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent

# Anker: 2–4 Großbuchstaben oder Ziffern als Dokument-Präfix, Bindestrich, Kleinbuchstaben-Slug.
# Der Slug schließt Großbuchstaben aus, damit Tracker-IDs (`TD-S089-1`) nicht mitgefangen werden.
_ANKER = r"[A-Z0-9]{2,4}-[a-z][a-z0-9-]*"
_ANKER_GANZ = re.compile(rf"^{_ANKER}$")
# Was Markdown als Listeneinstieg zählt. Eigener Name, weil `doc.py` dasselbe Fachwissen für
# die Einrückungsmessung braucht – dreimal ausgeschrieben driftet es auseinander, sobald ein
# Format dazukommt.
_LISTE = r"(?:[-*+]|\d+\.)"
# Definition: HTML-Anchor am Zeilenanfang – oder direkt hinter einem Listen-Marker. Manche
# Skills gliedern per nummerierter Liste statt per Überschrift; sie deswegen umzubauen hieße,
# hundert Zeilen Unterpunkte auszurücken, in Dateien, die den Arbeitsprozess steuern.
# Ausgeschlossen bleibt der Fließtext: Ein mitten im Satz erwähntes `<a id=…>` ist eine
# Erwähnung und darf keine zweite Definition erzeugen.
_DEFINITION = re.compile(
    rf'^(?:\s*{_LISTE}\s+)?<a id="({_ANKER})"></a>', re.M)
# Verweis: echter Markdown-Link mit Fragment. Der Pfad ist optional (leer = dieselbe Datei).
_VERWEIS = re.compile(rf"\[[^\]]*\]\(([^)#]*)#({_ANKER})\)")
# Verweis außerhalb von Markdown: Klartext `datei.md#ANKER`, wie er in einer Hook-Meldung
# oder einem Code-Kommentar lesbar ist. Die öffnende Klammer MUSS erlaubt sein – die häufigste
# Form im Code ist `// Domänentyp (pfad.md#ANKER, Ebene 2)`. Markdown-Links werden stattdessen  ordinal-ok
# vorher aus der Zeile entfernt (s. klartext_verweise_in): Ein pauschaler Klammer-Ausschluss
# verwarf in S124 neun von zehn Code-Verweisen, während der Prüfer grün meldete.
_KLARTEXT = re.compile(rf"""(?:^|[\s"'`(])((?:[\w./-]+/)?[\w.-]+\.md)#({_ANKER})""")
_MD_LINK = re.compile(r"\[[^\]]*\]\([^)]*\)")

# Dokument → Anker-Präfix. Verbindlich, damit nicht jeder Bearbeiter eigene Kürzel vergibt und
# der Bestand unlesbar wird. Der Prüfer erzwingt sie NICHT – er prüft Eindeutigkeit und
# Auflösbarkeit; ein Präfix-Zwang würde nur das Anlegen neuer Dokumente behindern, ohne einen
# Bruch zu verhindern. Diese Tabelle ist die Nachschlagequelle: `anchors.py praefixe`.
PRAEFIXE = {
    "docs/guidelines/coding-guideline-general.md": "CGG",
    "docs/guidelines/coding-guideline-csharp.md": "CGC",
    "docs/guidelines/coding-guideline-typescript.md": "CGT",
    "docs/guidelines/coding-guideline-ux.md": "CGU",
    "docs/guidelines/csharp-rop.md": "ROP",
    "docs/guidelines/csharp-stryker.md": "STK",
    "docs/guidelines/csharp-sumtypes.md": "SUM",
    "docs/process/dev-workflow.md": "DEV",
    "docs/process/e2e-testing.md": "E2E",
    "docs/process/nfr.md": "NFR",
    "docs/process/review-checklist.md": "RCL",
    "docs/process/slow-commands.md": "SLC",
    "docs/process/tdd-process.md": "TDD",
    "docs/reference/architecture.md": "ARC",
    "docs/reference/glossary.md": "GLO",
    "docs/reference/skeleton-spec.md": "SKE",
    "docs/kaizen/process.md": "KPR",
    "docs/kaizen/principles.md": "KPI",
    "CLAUDE.md": "CLA",
    ".claude/skills/implementing-scenario/SKILL.md": "IMP",
    ".claude/skills/closing-session/SKILL.md": "CLS",
    ".claude/skills/gherkin-workshop/SKILL.md": "GHW",
    ".claude/skills/kaizen/SKILL.md": "KZN",
    ".claude/skills/review-code/SKILL.md": "RVC",
    ".claude/skills/review-docs/SKILL.md": "RVD",
    ".claude/skills/review-workflow/SKILL.md": "RVW",
    ".claude/skills/write-code/SKILL.md": "WRC",
    ".claude/skills/draining-observations/SKILL.md": "DRN",
    ".claude/skills/design-an-interface/SKILL.md": "DSI",
    ".claude/skills/gherkin-workshop/references/scenario-clustering.md": "CLU",
}

# Verzeichnisse, in denen ein Verweis historisch korrekt ist und stehen bleiben soll.
# `docs/history` trägt allein über 100 Verweise auf Zustände von damals – sie zu prüfen hieße,
# über hundert Falschmeldungen zu erzeugen und den Prüfer damit unbenutzbar zu machen.
SKIP_PREFIXES = ("docs/history/", "docs/kaizen/archive/", ".claude/tmp/")

# Geprüft wird JEDE Textdatei außerhalb dieser Verzeichnisse – bewusst eine Deny- und keine
# Allowlist. Eine Allowlist erzeugt den Fehler, der in S124 zweimal auftrat: erst blieb
# `.claude/**` ungeprüft, dann `.cs`/`.ts` – beide Male meldete der Prüfer grün für einen
# Bereich, den er nie geöffnet hatte (CM-S116-1). Ein neuer Dateityp fällt so nicht mehr
# stillschweigend heraus; er müsste hier ausdrücklich eingetragen werden.
SKIP_ORDNER = frozenset({".git", "node_modules", "bin", "obj", "dist", "coverage",
                         "StrykerOutput", ".vs", "__pycache__", "reports",
                         # gitignored und ungetrackt – rein lokale Cache-/Build-Artefakte.
                         # Ohne sie las der Hook bei jedem Edit generiertes JS mit (S124).
                         ".pytest_cache", "wwwroot",
                         # Vollständige Repo-Kopie, die mutmut für den Mutationslauf anlegt.
                         # Ohne sie meldet die Prüfung nach jedem Lauf den Bestand doppelt –
                         # gemessen 386 „defekte" Verweise, die es nur in der Kopie gibt.
                         "mutants"})

# Von einem Werkzeug geschrieben, nicht von Hand gepflegt: Ein Verweis kann dort weder
# entstehen noch veralten. `package-lock.json` allein stellte 13.012 der 22.723 Zahl-Vorkommen
# des Repos (S124-Inventur) – bei jedem Edit mitgelesen, ohne dass je etwas darin zu prüfen war.
GENERIERT = ("Client/package-lock.json", "Infrastructure/Migrations/")

# Von der Werkzeugkette pro Session geschrieben, gitignored, ohne pflegbaren Inhalt.
LAUFZEIT = (".claude/RESUME.md", ".claude/session-types.json",
            ".claude/scheduled_tasks.lock")

# --- Zweite Stufe: Datei wird geprüft, einzelne Musterklassen zählen dort nicht ---
# Der Unterschied zur ersten Stufe ist der Grund: Oben ist nichts zu prüfen, hier ist das
# Meiste zu prüfen – nur die Muster, die eine Datei per Konstruktion als EINGABE führt, sind
# kein Befund. Ein pauschaler Datei-Ausschluss wäre bequemer und wurde deshalb S124 korrigiert:
# Alle `test_*.py` flogen komplett heraus, und genau dort lag ein toter Paragraphen-Verweis
# (`test_primitives.py`), den erst ein zufälliger grep fand.
#   "verweis"  – ein Anker-String ist hier Testdatum, kein Verweis
#   "ordinal"  – eine Gliederungsnummer ist hier Testdatum, kein Positionsverweis
MUSTER_AUSNAHMEN: dict[str, frozenset[str]] = {
    "tests/test_anchors.py": frozenset({"verweis", "ordinal"}),
    "tests/test_check_anchors.py": frozenset({"verweis", "ordinal"}),
    "tests/test_ordinale.py": frozenset({"verweis", "ordinal"}),
    "tests/test_check_ordinale.py": frozenset({"verweis", "ordinal"}),
}


def ausnahmen_fuer(rel: str) -> frozenset[str]:
    """Musterklassen, die in dieser Datei Eingabedatum sind statt Befund."""
    return MUSTER_AUSNAHMEN.get(rel, frozenset())


def ist_anker(text: str) -> bool:
    return bool(_ANKER_GANZ.match(text))


def anker_in(text: str) -> list[str]:
    """Die in diesem Text DEFINIERTEN Anker, in Dokumentreihenfolge.

    Nur ein `<a id=…>` allein auf einer Zeile zählt. Ein im Fließtext oder Codeblock
    gezeigtes Beispiel bleibt damit eine Erwähnung und erzeugt keine zweite Definition –
    sonst meldete der Prüfer Dubletten für Abschnitte, die es gar nicht gibt.
    """
    return _DEFINITION.findall(text)


def verweise_in(text: str) -> list[tuple[str, int, str]]:
    """(Ziel-Anker, Zeilennummer, Pfad) für jeden Verweis. Leerer Pfad = dieselbe Datei.

    Nur echte Markdown-Links zählen. Eine Erwähnung in Backticks ist kein Verweis: Sie ist
    nicht klickbar, und Klickbarkeit ist der Grund für dieses Format.
    """
    treffer = []
    im_codeblock = False
    for nr, zeile in enumerate(text.splitlines(), start=1):
        if zeile.lstrip().startswith("```"):
            im_codeblock = not im_codeblock
            continue
        # Codeblöcke tragen Beispiele, die ZEIGEN, wie man verweist – sie verweisen nicht
        # selbst. Ohne diese Ausnahme blockte der Prüfer jede Doku, die ihr eigenes Format
        # erklärt, und die Ausnahme `anchor-ok` würde zur Formalie in genau diesen Dateien.
        # Vier Leerzeichen sind die Markdown-Regel für den eingerückten Codeblock.
        if im_codeblock or zeile.startswith("    "):
            continue
        if _DEFINITION.match(zeile):
            continue
        treffer += [(ziel, nr, pfad) for pfad, ziel in _VERWEIS.findall(zeile)]
    return treffer


def klartext_verweise_in(text: str) -> list[tuple[str, int, str]]:
    """(Ziel-Anker, Zeilennummer, Pfad) für jeden Verweis in Klartext-Form `datei.md#ANKER`.

    Die Form für Python: Eine Hook-Meldung erscheint im Terminal, wo Markdown-Link-Syntax
    nur Zeichensalat wäre. Umgekehrt zählt ein Markdown-Link hier NICHT – die Docstrings der
    Anker-Werkzeuge zeigen echte Links als Beispiel, und die verweisen nicht selbst.

    Auch die Codeblock-Regel aus Markdown gilt hier nicht: Python-Code ist fast immer
    eingerückt, sie würde beinahe jede Meldung überspringen.
    """
    return [(ziel, nr, pfad)
            for nr, zeile in enumerate(text.splitlines(), start=1)
            for pfad, ziel in _KLARTEXT.findall(_MD_LINK.sub("", zeile))]


def verweise_aus(datei: str, text: str) -> list[tuple[str, int, str]]:
    """Die Verweise dieser Datei, in der für ihren Typ gültigen Form.

    Der EINE Ort, an dem die Muster-Ausnahme greift: Jede Prüfrichtung (tot, doppelt, falscher
    Pfad, verwaist) und beide Aufrufer holen ihre Verweise hier. Eine Ausnahme weiter oben je
    Prüfung wäre dieselbe Divergenz, die CM-S116-1 beschreibt.
    """
    if "verweis" in ausnahmen_fuer(datei):
        return []
    return verweise_in(text) if datei.endswith(".md") else klartext_verweise_in(text)


def verweis_anzahl(bestand: dict[str, str]) -> int:
    """Wie viele Verweise die Prüfung abgedeckt hat – die Zahl der Erfolgsmeldung.

    Muss dieselbe Quelle nutzen wie die Prüfung selbst. Zählte sie enger, meldete der Prüfer
    eine Vollständigkeit, die er nicht hat, und der Fehlbetrag fiele nur beim Nachrechnen auf.
    """
    return sum(len(verweise_aus(datei, text)) for datei, text in bestand.items())


def index(bestand: dict[str, str]) -> dict[str, list[str]]:
    """Anker → Dateien, die ihn definieren.

    Nur Markdown definiert Anker. Ein `<a id=…>` am Zeilenanfang eines Python-Strings ist
    Testmaterial, kein Abschnitt – mitgezählt meldete der Prüfer die Fixtures seiner eigenen
    Tests als Dubletten der echten Guideline.
    """
    gefunden: dict[str, list[str]] = defaultdict(list)
    for datei, text in sorted(bestand.items()):
        if not datei.endswith(".md"):
            continue
        for anker in anker_in(text):
            gefunden[anker].append(datei)
    return dict(gefunden)


def referenzen(anker: str, bestand: dict[str, str]) -> list[tuple[str, int, str]]:
    """(Datei, Zeile, Zeilentext) für jeden Verweis auf diesen Anker.

    Für den Fall, den kein Prüfer abdecken kann: Wird ein Abschnitt umbenannt oder
    umnummeriert, bleiben die Links gültig, aber ihr **Anzeigetext** kann veralten – „§4b"
    zeigt weiter aufs richtige Ziel und nennt trotzdem die falsche Nummer. Weil der Text frei
    wählbar ist, ist das nicht maschinell entscheidbar; es braucht die Fundstellen mit
    Kontext, damit ein Mensch gezielt ersetzen kann.
    """
    treffer = []
    for datei, text in sorted(bestand.items()):
        zeilen = text.splitlines()
        for ziel, nr, _pfad in verweise_aus(datei, text):
            if ziel == anker:
                treffer.append((datei, nr, zeilen[nr - 1].strip()))
    return treffer


def doppelte(bestand: dict[str, str]) -> list[tuple[str, list[str]]]:
    """Anker, die mehr als einmal definiert sind – eine Identität, zweimal vergeben."""
    return [(a, d) for a, d in sorted(index(bestand).items()) if len(d) > 1]


def tote_verweise(bestand: dict[str, str]) -> list[tuple[str, int, str]]:
    """(Datei, Zeile, Ziel) für jeden Verweis, dessen Anker nirgends definiert ist."""
    bekannt = set(index(bestand))
    return [
        (datei, nr, ziel)
        for datei, text in sorted(bestand.items())
        for ziel, nr, _pfad in verweise_aus(datei, text)
        if ziel not in bekannt
    ]


def _ziel_datei(quelle: str, pfad: str) -> str:
    """Repo-relativer Pfad, auf den ein Verweis aus `quelle` zeigt. Leer = dieselbe Datei."""
    if not pfad:
        return quelle
    if not quelle.endswith(".md"):
        # Der Pfad steht in einer Terminal-Meldung, deren Arbeitsverzeichnis das Repo-Root
        # ist – er ist repo-relativ. Wie in Markdown gelesen, wäre jede Meldung aus
        # `prozesscode/hooks/checks/` ein falscher Pfad.
        return os.path.normpath(pfad).replace(os.sep, "/")
    return os.path.normpath(os.path.join(os.path.dirname(quelle), pfad)).replace(os.sep, "/")


def falsche_pfade(bestand: dict[str, str]) -> list[tuple[str, int, str, str, str]]:
    """(Datei, Zeile, Ziel, verlinkter Pfad, tatsächlicher Pfad) für jeden Link, dessen
    Anker existiert – aber nicht in der verlinkten Datei.

    Ohne diese Prüfung wäre die Klickbarkeit unzuverlässig: Der Prüfer meldete „alles gut",
    während der Klick ins Leere ginge. Genau sie ist der Grund für das Link-Format, also muss
    sie abgesichert sein.
    """
    wo = index(bestand)
    fehler = []
    for datei, text in sorted(bestand.items()):
        for ziel, nr, pfad in verweise_aus(datei, text):
            if ziel not in wo:
                continue  # meldet bereits `tote_verweise`
            gemeint = _ziel_datei(datei, pfad)
            if gemeint not in wo[ziel]:
                fehler.append((datei, nr, ziel, gemeint, wo[ziel][0]))
    return fehler


def verwaiste(pre: str, post: str, andere: dict[str, str]
              ) -> list[tuple[str, list[tuple[str, int]]]]:
    """Anker, die dieser Edit entfernt, auf die aber anderswo noch verwiesen wird.

    Die Gegenrichtung zu `tote_verweise`. Ohne sie bliebe das Löschen eines Ankers
    folgenlos, bis irgendwann jemand dem Verweis folgt und ins Leere läuft.
    """
    entfernt = [a for a in anker_in(pre) if a not in set(anker_in(post))]
    ergebnis = []
    for anker in entfernt:
        zeigt_drauf = [(datei, nr) for datei, text in sorted(andere.items())
                       for ziel, nr, _pfad in verweise_aus(datei, text) if ziel == anker]
        if zeigt_drauf:
            ergebnis.append((anker, zeigt_drauf))
    return ergebnis


# --- Bestand einlesen --------------------------------------------------------
def wird_geprueft(rel: str) -> bool:
    """Ob diese repo-relative Datei überhaupt geprüft wird – die erste der beiden Stufen.

    EINE Regel für beide Aufrufer – die CLI und der Hook. Zwei getrennte Ausschlusslisten
    driften auseinander, und die Divergenz fällt erst auf, wenn eine der beiden Seiten
    blind geworden ist (CM-S116-1).

    Hier fällt nur heraus, worin **nichts** zu prüfen ist: eingefrorene Historie, generierte
    und Laufzeit-Dateien. Alles, worin das Meiste zu prüfen ist und nur einzelne Muster
    Eingabedatum sind, bleibt drin und wird über `ausnahmen_fuer` behandelt.
    """
    if rel.startswith(SKIP_PREFIXES) or rel.startswith(GENERIERT) or rel in LAUFZEIT:
        return False
    # Bewusst NICHT „alles Versteckte überspringen": `.claude/**` trägt die Skills und damit
    # die meisten Verweise überhaupt. Eine solche Pauschalregel hat den Prüfer in S124 für
    # diesen Bereich blind gemacht, während er grün meldete.
    return not any(teil in SKIP_ORDNER for teil in rel.split("/"))


def relevante_dateien(root: Path | None = None) -> list[Path]:
    """Alle Dateien, in denen Anker und Verweise geprüft werden.

    `os.walk` mit Pruning statt `rglob("*")`: Ein nachgelagerter Filter müsste erst durch
    `node_modules` hindurch, was den Aufruf von Millisekunden auf Sekunden hebt – spürbar,
    weil der Hook bei JEDEM Edit den ganzen Bestand liest.
    """
    basis = root or REPO_ROOT
    dateien = []
    for wurzel, ordner, namen in os.walk(basis):
        ordner[:] = [o for o in ordner if o not in SKIP_ORDNER]
        for name in namen:
            pfad = Path(wurzel) / name
            if wird_geprueft(pfad.relative_to(basis).as_posix()):
                dateien.append(pfad)
    return dateien


def _text_oder_none(pfad: Path) -> str | None:
    """Inhalt der Datei – oder None, wenn sie keine Textdatei ist.

    Ein NUL-Byte im Kopf ist das Kennzeichen: Es kommt in Text praktisch nicht vor, in
    Binärformaten fast immer. Das Netz sitzt hier statt in einer Suffix-Liste, damit auch ein
    unbekanntes Binärformat auffällt, für das niemand eine Regel geschrieben hat.
    """
    roh = pfad.read_bytes()
    if b"\x00" in roh[:4096]:
        return None
    return roh.decode("utf-8", errors="replace")


def lies_bestand(root: Path | None = None) -> dict[str, str]:
    basis = root or REPO_ROOT
    bestand = {}
    for pfad in relevante_dateien(basis):
        text = _text_oder_none(pfad)
        if text is not None:
            bestand[pfad.relative_to(basis).as_posix()] = text
    return bestand


# --- CLI ---------------------------------------------------------------------
def cmd_check(args) -> int:
    bestand = lies_bestand()
    tot = tote_verweise(bestand)
    dopp = doppelte(bestand)
    pfade = falsche_pfade(bestand)

    if pfade:
        print(f"❌ {len(pfade)} Links auf die falsche Datei (Anker existiert, Klick geht ins "
              f"Leere):")
        for datei, nr, ziel, gemeint, echt in pfade[:40]:
            print(f"  {datei}:{nr}: {ziel} → verlinkt {gemeint}, liegt in {echt}")
    if dopp:
        print(f"❌ {len(dopp)} mehrfach vergebene Anker:")
        for anker, dateien in dopp:
            print(f"  {anker}: {', '.join(dateien)}")
    if tot:
        print(f"❌ {len(tot)} Verweise ohne Ziel:")
        for datei, nr, ziel in tot[:40]:
            print(f"  {datei}:{nr}: `{ziel}`")
        if len(tot) > 40:
            print(f"  … und {len(tot) - 40} weitere")
    if not tot and not dopp and not pfade:
        anzahl = len(index(bestand))
        verweise = verweis_anzahl(bestand)
        print(f"✓ {anzahl} Anker, {verweise} Verweise – alle auflösbar, Pfade stimmen, "
              f"keine Dubletten.")
        return 0
    return 1


def cmd_praefixe(args) -> int:
    for datei, praefix in sorted(PRAEFIXE.items(), key=lambda p: p[1]):
        print(f"  {praefix:<5} {datei}")
    print(f"\n{len(PRAEFIXE)} Dokumente. Anker = <PRÄFIX>-<slug>, z.B. CGT-result.")
    print("Nicht gelistetes Dokument: neues Präfix wählen und hier eintragen.")
    return 0


def cmd_list(args) -> int:
    bestand = lies_bestand()
    # Gezählt wird immer über den GANZEN Bestand, auch wenn die Anzeige gefiltert ist:
    # Ein Filter schränkt ein, welche Anker gezeigt werden – nicht, wer auf sie zeigt.
    ziele: dict[str, int] = defaultdict(int)
    for datei, text in bestand.items():
        for ziel, _nr, _pfad in verweise_aus(datei, text):
            ziele[ziel] += 1
    if args.datei:
        bestand = {d: t for d, t in bestand.items() if args.datei in d}
        if not bestand:
            print(f"Keine Datei passt auf '{args.datei}'.", file=sys.stderr)
            return 1
    gefunden = index(bestand)
    if not gefunden:
        print("Keine Anker gefunden.")
        return 0
    for anker, dateien in sorted(gefunden.items()):
        print(f"{anker:<22} {dateien[0]:<48} {ziele.get(anker, 0)}× referenziert")
    print(f"\n{len(gefunden)} Anker.")
    return 0


def cmd_refs(args) -> int:
    bestand = lies_bestand()
    if args.anker not in index(bestand):
        print(f"Anker '{args.anker}' ist nirgends definiert. "
              f"Bestand: anchors.py list", file=sys.stderr)
        return 1
    fund = referenzen(args.anker, bestand)
    if not fund:
        print(f"{args.anker}: keine Verweise – der Abschnitt kann frei umbenannt werden.")
        return 0
    print(f"{args.anker}: {len(fund)} Verweis(e). Der Link bleibt beim Umbenennen gültig – "
          f"prüfe, ob der Anzeigetext noch passt:\n")
    for datei, nr, zeile in fund:
        print(f"  {datei}:{nr}")
        print(f"      {zeile[:160]}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description="Abschnitts-Anker prüfen und auflisten.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check", help="Tote Verweise, falsche Pfade und Anker-Dubletten"
                   ).set_defaults(fn=cmd_check)
    sub.add_parser("praefixe", help="Welches Dokument nutzt welches Anker-Präfix"
                   ).set_defaults(fn=cmd_praefixe)

    p_list = sub.add_parser("list", help="Alle Anker mit Fundort und Verweis-Anzahl")
    p_list.add_argument("--datei", help="nur Dateien, deren Pfad diesen Text enthält")
    p_list.set_defaults(fn=cmd_list)

    p_refs = sub.add_parser(
        "refs", help="Alle Fundstellen eines Ankers – vor dem Umbenennen eines Abschnitts")
    p_refs.add_argument("anker")
    p_refs.set_defaults(fn=cmd_refs)

    args = p.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
