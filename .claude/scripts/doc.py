#!/usr/bin/env python3
"""Gezielter Abruf eines Doku-Abschnitts über seinen Anker – lesen statt Volldatei.

Warum (OBS-S114-2): `docs/guidelines` und `docs/process` machen zusammen **20,4 %** des
gesamten Read-Volumens aus (61 Sessions, `read-breakdown.py --by-area`) – Ø 11.856 Zeichen je
Read bei nur **6 % gezielten** Zugriffen. Praktisch jeder Aufruf las das ganze Dokument, weil
es keinen Weg gab, einen einzelnen Abschnitt zu holen; jeder Subagent startet kalt und liest
seine Pflichtlektüre vollständig. Der Gegenbeleg steht im selben Datensatz: `docs/history`
liegt bei **72 % gezielt**, denn dort existiert mit `decisions.py` ein Abrufweg. Der Median
eines Abschnitts ist 952 Zeichen – Faktor 12 gegenüber der Volldatei.

**Warum ein eigenes Script neben `anchors.py`.** Die Grenze läuft an der Zielgruppe, nicht an
der Anker-Logik: `anchors.py` (`list|check|refs`) bedient den Doku-Autor und den Hook –
Registry und Integrität. `doc.py` bedient den arbeitenden Subagenten – Retrieval. Ein
Backend-Implementierer, der `--help` liest, braucht `check` nie. Der Anker-Index wird nicht
kopiert, sondern aus `anchors` importiert (Muster wie `obs.py` über `obs_parse.py`).

**Die Scope-Regel** (User-Entscheid S125) – was gehört zu einem Anker? Zwei Fälle:

  - **Überschriften-Anker** → bis zur nächsten Überschrift, die *gleichrangig oder
    höherrangig* ist. Die Unterabschnitte gehören also dazu. Bewusst nicht „bis zur nächsten
    Überschrift beliebiger Ebene" und nicht „bis zum nächsten Anker": Beide sparen im Median
    nur ~200 Zeichen und erkaufen das durch **stilles Abschneiden** – wer `CGC-domain-typen`
    abruft, bekäme den Vorspann ohne die Regeln und hätte keinen Anhaltspunkt, dass etwas
    fehlt. Das ist hier die teuerste Fehlerklasse, weil das Ergebnis vollständig aussieht.

  - **Absatz-Anker** → nur der zusammenhängende Block, in dem der Anker steht; tiefer
    eingerückte Zeilen sind Fortsetzung, gleich eingerückte nach einer Leerzeile nicht. Am
    Bestand validiert (35 Absatz-Anker): 21 identisch zur Alternative, 6 mal ist diese Regel
    richtig und die Alternative falsch (sie zöge den nächsten Arbeitsschritt mit hinein), 8
    mal zeigt sie ein **Gliederungsproblem der Doku** an. Diese acht werden umgebaut – fehlt
    eine Überschrift, wird sie ergänzt –, statt die Regel aufzuweichen. Denn eine Heuristik,
    die schlechte Gliederung glattbügelt, verbirgt sie auch vor dem menschlichen Leser.

Damit ist der Anker keine Marke mehr, sondern eine **abrufbare Einheit**. Was zu ihm gehört,
muss aus der Gliederung folgen – `doc.py audit` sichtet den Bestand darauf.
"""
import argparse
import os
import re
import sys
from importlib import import_module

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
anchors = import_module("anchors")

_HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
_FENCE = re.compile(r"^\s*```")
# Dasselbe Muster wie in `anchors.py`, nicht neu geschrieben: Was ein Anker ist, wird an EINER
# Stelle definiert. Neu formuliert bräche eine spätere Änderung dort dieses Werkzeug lautlos –
# beide Test-Suiten haben eigene Fixtures und würden es nicht bemerken. `re.M` stört nicht,
# weil hier nur einzelne, bereits getrennte Zeilen geprüft werden.
_ANKER_ZEILE = anchors._DEFINITION
# Einrückung plus Marker-Art: Die Art trennt zwei nebeneinanderliegende Listen (`-` gefolgt von
# `1.` sind nach CommonMark zwei Listen, kein Geschwisterpaar).
_LISTEN_MARKER = re.compile(rf"^(\s*)({anchors._LISTE})\s+")

# Ab dieser Größe ist ein Abschnitt als Abrufeinheit fragwürdig – er kostet so viel wie eine
# halbe Volldatei und will vermutlich untergliedert werden. Kein Fehler, ein Hinweis.
GROSS_AB = 8000


# --- Zeilen-Klassifikation ---------------------------------------------------
def _ausserhalb_fence(zeilen: list[str]) -> list[bool]:
    """Für jede Zeile: liegt sie außerhalb eines Code-Fence?

    Ohne diese Unterscheidung beendet ein `# Kommentar` in einem Bash-Block jeden Abschnitt –
    die Ebenen-Regel liefe an der ersten Raute im Beispielcode ins Leere, und zwar lautlos.
    """
    draussen, im_fence = [], False
    for zeile in zeilen:
        if _FENCE.match(zeile):
            im_fence = not im_fence
            draussen.append(False)
            continue
        draussen.append(not im_fence)
    return draussen


def _ebene(zeile: str) -> int | None:
    """Überschriftenebene (1–6) oder None. Die Fence-Prüfung liegt beim Aufrufer.

    Ein vorangestellter Anker wird abgezogen: `<a id="X"></a>## Titel` auf einer Zeile ist eine
    dokumentierte Schreibweise. Wurde sie beim Vorwärts-Scan nicht erkannt, lief der
    vorhergehende Abschnitt über sie hinweg bis zum Dateiende, und `toc` verschwieg den
    Abschnitt ganz – beides lautlos.
    """
    treffer = _heading(zeile)
    return len(treffer.group(1)) if treffer else None


def _heading(zeile: str) -> re.Match | None:
    """Der Überschriften-Treffer dieser Zeile, um einen vorangestellten Anker bereinigt."""
    return _HEADING.match(_ANKER_ZEILE.sub("", zeile).lstrip())


def _anker_positionen(zeilen: list[str]) -> list[tuple[str, int]]:
    """(Anker, Zeilenindex) in Dokumentreihenfolge.

    `anchors.anker_in` liefert nur die Namen; für den Abruf ist die Position nötig. Dasselbe
    Muster – Anker am Zeilenanfang oder direkt hinter einem Listen-Marker –, damit beide
    Werkzeuge denselben Bestand sehen.
    """
    return [(m.group(1), i) for i, z in enumerate(zeilen) if (m := _ANKER_ZEILE.match(z))]


def _kopfzeile_des_ankers(zeilen: list[str], idx: int) -> tuple[int, int | None]:
    """(Zeilenindex der zugehörigen Überschrift, deren Ebene) – oder (idx, None) beim
    Absatz-Anker.

    Beide Schreibweisen zählen: Anker auf eigener Zeile über der Überschrift (die Regel), und
    Anker inline vor dem Überschriftentext.
    """
    rest = _ANKER_ZEILE.sub("", zeilen[idx]).strip()
    if (ebene := _ebene(rest)) is not None:
        return idx, ebene
    if idx + 1 < len(zeilen) and (ebene := _ebene(zeilen[idx + 1].strip())) is not None:
        return idx + 1, ebene
    return idx, None


# --- Scope-Regel -------------------------------------------------------------
def _vor_dem_anker(zeilen: list[str], j: int) -> int:
    """Die Grenze, verschoben vor die Ankerzeile des Folgeabschnitts.

    Der Anker steht eine Zeile ÜBER seiner Überschrift. Ohne diese Korrektur endete jeder
    Abschnitt erst hinter dem Anker des nächsten – der Abruf lieferte eine fremde Identität
    mit aus, und die Nachbar-Anzeige hielte den Folgeabschnitt für Teil des eigenen.
    """
    return j - 1 if j > 0 and _ANKER_ZEILE.match(zeilen[j - 1]) else j


def _ende_ueberschrift(zeilen: list[str], draussen: list[bool], ab: int, ebene: int) -> int:
    """Erste Zeile NACH dem Abschnitt: die nächste gleichrangige oder höherrangige
    Überschrift."""
    for j in range(ab + 1, len(zeilen)):
        if draussen[j] and (e := _ebene(zeilen[j])) is not None and e <= ebene:
            return _vor_dem_anker(zeilen, j)
    return len(zeilen)


def _einrueckung(zeile: str) -> int:
    """Wie weit die Zeile eingerückt ist – die rohe Leerzeichenzahl.

    Bewusst der Marker, nicht der Inhalt dahinter: In Markdown entscheidet die Einrückung des
    **Markers** über die Verschachtelung. Ein `-` auf gleicher Höhe wie ein `1.` beginnt eine
    neue Liste auf derselben Ebene und ist kein Unterpunkt; hinter dem Marker gemessen wäre
    `basis` um dessen Breite zu groß und schlösse die echten Unterpunkte aus.
    """
    return len(zeile) - len(zeile.lstrip())


def _ende_absatz(zeilen: list[str], draussen: list[bool], ab: int,
                 anker_zeilen: set[int]) -> int:
    """Erste Zeile NACH dem zusammenhängenden Block.

    Drei Abbruchgründe: eine Überschrift, ein weiterer Anker (der eine eigene Einheit beginnt –
    ohne diese Prüfung schluckte ein Block den nächsten Anker samt Inhalt, sobald keine
    Leerzeile dazwischen stand), und eine Leerzeile, hinter der es nicht tiefer eingerückt
    weitergeht. Tiefer eingerückt heißt Fortsetzung – auch wenn dort ein Code-Fence beginnt.
    """
    basis = _einrueckung(zeilen[ab])
    idx = ab + 1
    while idx < len(zeilen):
        zeile = zeilen[idx]
        if draussen[idx] and _ebene(zeile) is not None:
            return _vor_dem_anker(zeilen, idx)
        if idx in anker_zeilen:
            return idx
        if zeile.strip() == "" and draussen[idx]:
            weiter = idx
            while weiter < len(zeilen) and zeilen[weiter].strip() == "":
                weiter += 1
            if weiter >= len(zeilen) or _einrueckung(zeilen[weiter]) <= basis:
                return idx
        idx += 1
    return len(zeilen)


def grenzen(anker: str, text: str) -> tuple[int, int]:
    """(erste, erste-nach) Zeilenindex des Abschnitts, den dieser Anker adressiert."""
    zeilen = text.splitlines()
    stellen = _anker_positionen(zeilen)
    # Erste Definition gewinnt. Eine Dublette meldet `anchors.py check` als Integritätsfehler;
    # bis sie behoben ist, liefert der Abruf wenigstens berechenbar dieselbe Stelle.
    positionen: dict[str, int] = {}
    for name, i in stellen:
        positionen.setdefault(name, i)
    if anker not in positionen:
        raise KeyError(anker)
    idx = positionen[anker]
    draussen = _ausserhalb_fence(zeilen)
    kopf, ebene = _kopfzeile_des_ankers(zeilen, idx)
    if ebene is not None:
        return idx, _ende_ueberschrift(zeilen, draussen, kopf, ebene)
    # Steht der Anker allein auf seiner Zeile, beginnt der Block in der nächsten.
    start_inhalt = idx if _ANKER_ZEILE.sub("", zeilen[idx]).strip() else idx + 1
    andere = {i for _, i in stellen if i != idx}
    return idx, _ende_absatz(zeilen, draussen, min(start_inhalt, len(zeilen) - 1), andere)


def abschnitt(anker: str, text: str) -> str:
    """Der Text, den dieser Anker adressiert – inklusive Anker- und Überschriftenzeile."""
    von, bis = grenzen(anker, text)
    return "\n".join(text.splitlines()[von:bis]).rstrip() + "\n"


# --- Kontext-Kopf ------------------------------------------------------------
def _breadcrumb(zeilen: list[str], draussen: list[bool], idx: int) -> list[str]:
    """Die Überschriften-Kette über dieser Zeile, von außen nach innen – ohne die H1.

    Die H1 ist in aller Regel der Dateititel und wiederholt damit nur den Pfad, der links
    daneben schon steht („coding-guideline-csharp.md › Guideline für das Generieren von
    C#-Code"). Der Kopf soll einordnen, nicht den gesparten Platz wieder auffüllen.
    """
    kette: dict[int, str] = {}
    for j in range(idx + 1):
        if not draussen[j]:
            continue
        if (treffer := _heading(zeilen[j])) is not None:
            ebene = len(treffer.group(1))
            kette = {e: t for e, t in kette.items() if e < ebene}
            kette[ebene] = treffer.group(2).strip()
    return [kette[e] for e in sorted(kette) if e > 1]


def kopf(anker: str, datei: str, text: str, bestand: dict[str, str]) -> str:
    """Zwei bis drei Zeilen Einordnung: wo der Abschnitt sitzt und was ihn umgibt.

    Der Zweck ist nicht Zierde, sondern die Gegenprobe zum gezielten Lesen: sichtbar machen,
    was NICHT geliefert wurde. Ohne sie kann ein Abschnitt vollständig wirken, obwohl der
    tragende Nachbarabschnitt fehlt. Bewusst knapp – ein Kopf, der den Abschnitt aufbläht,
    frisst den Gewinn wieder auf, um dessentwillen das Werkzeug existiert.
    """
    zeilen = text.splitlines()
    draussen = _ausserhalb_fence(zeilen)
    von, bis = grenzen(anker, text)
    # Der Breadcrumb beschreibt, WO der Abschnitt sitzt – also die Lage seiner eigenen
    # Überschrift. Vom Abschnittsende aus gerechnet nennte er den letzten Unterabschnitt.
    kopfzeile, _ = _kopfzeile_des_ankers(zeilen, von)
    pfad = " › ".join([datei] + _breadcrumb(zeilen, draussen, kopfzeile))
    positionen = _anker_positionen(zeilen)
    vorher = [a for a, i in positionen if i < von]
    nachher = [a for a, i in positionen if i >= bis]
    ausgabe = [f"{pfad}  [{anker}]"]
    nachbarn = []
    if vorher:
        nachbarn.append(f"← {vorher[-1]}")
    if nachher:
        nachbarn.append(f"{nachher[0]} →")
    if nachbarn:
        ausgabe.append("Nachbarn: " + "  ".join(nachbarn))
    return "\n".join(ausgabe)


# --- Kürzung, die sich selbst meldet -----------------------------------------
def kuerze(text: str, hoechstens: int) -> tuple[str, str]:
    """(gekürzter Text, Hinweis). Der Hinweis ist leer, wenn nichts wegfiel.

    Eine stille Kürzung wäre genau der Fehler, gegen den die Scope-Regel entschieden hat –
    nur diesmal vom Aufrufer selbst ausgelöst.
    """
    zeilen = text.splitlines()
    if len(zeilen) <= hoechstens:
        return text, ""
    rest = len(zeilen) - hoechstens
    return ("\n".join(zeilen[:hoechstens]) + "\n",
            f"… {rest} weitere Zeilen – vollständig: doc.py get <ANKER>")


def zuschnitt(text: str, hoechstens: int | None = None,
              ohne_unterabschnitte: bool = False) -> tuple[str, list[str]]:
    """(zugeschnittener Text, alle Hinweise). Der EINE Ort, an dem Zuschnitte kombiniert werden.

    Jeder Schnitt meldet sich einzeln. Würde ein Hinweis den anderen ersetzen, stünde
    ausgerechnet in der Funktion, die stille Kürzung verhindern soll, eine eingebaute – der
    Aufrufer läse „N Zeilen gekürzt" und wüsste nicht, dass zusätzlich alle Unterabschnitte
    fehlen.
    """
    if hoechstens is not None and hoechstens < 0:
        raise ValueError(f"--zeilen braucht eine Zahl ab 0, nicht {hoechstens}")
    hinweise = []
    if ohne_unterabschnitte:
        text, hinweis = nur_vorspann(text)
        if hinweis:
            hinweise.append(hinweis)
    if hoechstens is not None:
        text, hinweis = kuerze(text, hoechstens)
        if hinweis:
            hinweise.append(hinweis)
    return text, hinweise


def nur_vorspann(text: str) -> tuple[str, str]:
    """(Text bis zum ersten Unterabschnitt, Hinweis)."""
    zeilen = text.splitlines()
    draussen = _ausserhalb_fence(zeilen)
    eigene = next((_ebene(z) for i, z in enumerate(zeilen) if draussen[i]
                   and _ebene(z) is not None), 0)
    for j in range(1, len(zeilen)):
        if draussen[j] and (e := _ebene(zeilen[j])) is not None and e > eigene:
            rest = len(zeilen) - j
            return ("\n".join(zeilen[:j]).rstrip() + "\n",
                    f"… {rest} weitere Zeilen in Unterabschnitten – "
                    f"vollständig: doc.py get <ANKER>")
    return text, ""


# --- Inventur ----------------------------------------------------------------
def toc(text: str) -> list[dict]:
    """Alle Abschnitte einer Datei – mit Anker, sofern einer existiert.

    Abschnitte OHNE Anker werden mitgelistet. Sonst hielte der Abrufende die Anker-Liste für
    das Inhaltsverzeichnis und übersähe, dass Teile der Datei gar nicht adressierbar sind –
    ein Filter, der sich als Bestand ausgibt.
    """
    zeilen = text.splitlines()
    draussen = _ausserhalb_fence(zeilen)
    positionen = _anker_positionen(zeilen)
    anker_bei = {i: a for a, i in positionen}
    eintraege = []
    for i, zeile in enumerate(zeilen):
        if not draussen[i]:
            continue
        ebene = _ebene(zeile)
        if ebene is not None:
            anker = anker_bei.get(i - 1) or anker_bei.get(i)
            titel = _heading(zeile).group(2).strip()
        elif i in anker_bei and _kopfzeile_des_ankers(zeilen, i)[1] is None:
            anker = anker_bei[i]
            rest = _ANKER_ZEILE.sub("", zeile).strip() or (
                zeilen[i + 1].strip() if i + 1 < len(zeilen) else "")
            titel = re.sub(r"[*`_]", "", rest)[:60]
            ebene = 0
        else:
            continue
        von, bis = (grenzen(anker, text) if anker
                    else (i, _ende_ueberschrift(zeilen, draussen, i, ebene)))
        eintraege.append({
            "anker": anker,
            "titel": titel,
            "ebene": ebene,
            "zeile": i + 1,
            "zeichen": sum(len(z) + 1 for z in zeilen[von:bis]),
        })
    return eintraege


# --- Audit -------------------------------------------------------------------
def geprueft(bestand: dict[str, str]) -> int:
    """Wie viele Anker das Audit gesichtet hat – die Zahl der Erfolgsmeldung.

    Muss aus derselben Quelle stammen wie die Sichtung selbst. Zählte sie enger, meldete das
    Audit eine Vollständigkeit, die es nicht hat (CM-S116-1).
    """
    return sum(len(anchors.anker_in(t)) for d, t in bestand.items() if d.endswith(".md"))


def audit(bestand: dict[str, str]) -> list[dict]:
    """Anker, deren Abrufeinheit fragwürdig ist – der ganze Bestand, nicht eine Auswahl.

    Zwei Arten, beide sind Gliederungshinweise und keine Fehler:
      `fortsetzung` – hinter dem Block eines Absatz-Ankers steht weiterer Text, bevor die
                      nächste Überschrift oder der nächste Anker kommt. Entweder gehört er
                      dazu (dann fehlt eine Überschrift oder die trennende Leerzeile ist
                      falsch) oder nicht (dann ist alles in Ordnung) – das entscheidet ein
                      Mensch, nicht die Heuristik.
      `lose`        – zwischen Anker und Inhalt steht eine Leerzeile. Der Anker gilt dann als
                      Absatz-Anker über einer leeren Zeile und liefert nichts Sinnvolles.
      `fence`       – die Datei hat eine ungerade Zahl von ```-Zeilen. Ab dem offenen Fence
                      gilt jede Überschrift als Code; alle Abschnittsgrenzen darunter sind
                      still falsch. Datei-, nicht Anker-Befund.
      `geschwister` – dahinter steht ein Listenpunkt derselben Ebene UND derselben Art. Das
                      ist die normale Form einer Aufzählung, in der nur ein Punkt einen Anker
                      trägt, und kein Befund. Trotzdem gezählt und ausgewiesen: Ein stiller
                      Abzug wäre ein Filter, der sich als Vollprüfung ausgibt.
      `gross`       – der Abschnitt ist so groß, dass der gezielte Abruf kaum noch spart.
    """
    befunde = []
    for datei in sorted(bestand):
        if not datei.endswith(".md"):
            continue
        text = bestand[datei]
        zeilen = text.splitlines()
        if sum(1 for z in zeilen if _FENCE.match(z)) % 2:
            befunde.append({
                "datei": datei, "anker": None, "art": "fence", "zeile": 0,
                "hinweis": "ungerade Zahl von ```-Zeilen – jede Überschrift dahinter gilt als "
                           "Code, alle Abschnittsgrenzen darunter sind still falsch"})
        for anker, idx in _anker_positionen(zeilen):
            befunde += _befunde_zum_anker(datei, text, zeilen, anker, idx)
    return befunde


def _befunde_zum_anker(datei: str, text: str, zeilen: list[str], anker: str,
                       idx: int) -> list[dict]:
    """Die Befunde eines einzelnen Ankers – eigene Funktion, damit sie ohne den Bestands-Lauf
    prüfbar bleibt."""
    von, bis = grenzen(anker, text)
    zeichen = sum(len(z) + 1 for z in zeilen[von:bis])
    befunde = []
    if zeichen > GROSS_AB:
        befunde.append({"datei": datei, "anker": anker, "art": "gross", "zeile": idx + 1,
                        "zeichen": zeichen,
                        "hinweis": f"{zeichen} Zeichen – untergliedern?"})
    if _kopfzeile_des_ankers(zeilen, idx)[1] is not None:
        return befunde
    if not _ANKER_ZEILE.sub("", zeilen[idx]).strip() and not zeilen[min(
            idx + 1, len(zeilen) - 1)].strip():
        befunde.append({
            "datei": datei, "anker": anker, "art": "lose", "zeile": idx + 1,
            "hinweis": "Leerzeile zwischen Anker und Inhalt – der Abruf findet keine Einheit"})
        return befunde
    nachfolger = _erster_zurueckgelassener(zeilen, bis)
    if nachfolger is None:
        return befunde
    befunde.append({
        "datei": datei, "anker": anker, "zeile": idx + 1,
        "art": _art_des_nachfolgers(zeilen[idx], zeilen[nachfolger]),
        "hinweis": f"Text ab Zeile {nachfolger + 1} fällt aus dem Abruf: "
                   f"{zeilen[nachfolger].strip()[:60]}"})
    return befunde


def _erster_zurueckgelassener(zeilen: list[str], ab: int) -> int | None:
    """Index der ersten Zeile hinter dem Abschnitt, die weder leer ist noch eine neue Einheit
    beginnt – oder None, wenn direkt eine Überschrift oder ein Anker folgt."""
    draussen = _ausserhalb_fence(zeilen)
    anker_zeilen = {i for _, i in _anker_positionen(zeilen)}
    for j in range(ab, len(zeilen)):
        if not zeilen[j].strip():
            continue
        if j in anker_zeilen or (draussen[j] and _ebene(zeilen[j]) is not None):
            return None
        return j
    return None


def _art_des_nachfolgers(eigene: str, folgende: str) -> str:
    """`geschwister`, wenn beide Zeilen Punkte DERSELBEN Liste sind – sonst `fortsetzung`.

    Gleiche Einrückung allein genügt nicht: `- ` und `1. ` auf gleicher Höhe sind nach
    CommonMark zwei getrennte Listen. Als Geschwister eingestuft verschwände ein echtes
    Gliederungsproblem unsichtbar im „kein Befund"-Topf.
    """
    eigener, folgender = _LISTEN_MARKER.match(eigene), _LISTEN_MARKER.match(folgende)
    if not (eigener and folgender):
        return "fortsetzung"
    gleiche_tiefe = len(eigener.group(1)) == len(folgender.group(1))
    gleiche_art = eigener.group(2)[0].isdigit() == folgender.group(2)[0].isdigit()
    return "geschwister" if gleiche_tiefe and gleiche_art else "fortsetzung"


# --- CLI ---------------------------------------------------------------------
def _finde_datei(muster: str, bestand: dict[str, str]) -> str | None:
    treffer = [d for d in sorted(bestand) if d.endswith(".md") and muster in d]
    if len(treffer) == 1:
        return treffer[0]
    if not treffer:
        return None
    exakt = [d for d in treffer if d.endswith("/" + muster) or d == muster]
    return exakt[0] if len(exakt) == 1 else None


def cmd_get(args) -> int:
    bestand = anchors.lies_bestand()
    wo = anchors.index(bestand)
    if args.anker not in wo:
        print(f"Anker '{args.anker}' ist nirgends definiert. Bestand: anchors.py list",
              file=sys.stderr)
        return 1
    datei = wo[args.anker][0]
    text = bestand[datei]
    inhalt, hinweise = zuschnitt(abschnitt(args.anker, text), args.zeilen,
                                 args.nur_vorspann)
    print(kopf(args.anker, datei, text, bestand))
    for hinweis in hinweise:
        print(hinweis.replace("<ANKER>", args.anker))
    print("─" * 60)
    print(inhalt, end="")
    return 0


def cmd_toc(args) -> int:
    bestand = anchors.lies_bestand()
    datei = _finde_datei(args.datei, bestand)
    if datei is None:
        print(f"Keine eindeutige Markdown-Datei für '{args.datei}'.", file=sys.stderr)
        return 1
    eintraege = toc(bestand[datei])
    gesamt = len(bestand[datei])
    mit_anker = sum(1 for e in eintraege if e["anker"])
    print(f"{datei} – {gesamt} Zeichen, {len(eintraege)} Abschnitte, "
          f"{mit_anker} mit Anker")
    for e in eintraege:
        einzug = "  " * max(e["ebene"] - 1, 0)
        anker = e["anker"] or "(kein Anker)"
        print(f"  {einzug}{anker:<32} {e['titel'][:46]:<48} {e['zeichen']:>6} Z.")
    print(f"\nAbschnitt holen: doc.py get <ANKER>")
    return 0


def cmd_audit(args) -> int:
    bestand = anchors.lies_bestand()
    befunde = audit(bestand)
    nach_art = {art: [b for b in befunde if b["art"] == art]
                for art in ("fence", "lose", "fortsetzung", "geschwister", "gross")}
    for art, titel in (("fence", "Dateien mit unausgeglichenen Code-Fences"),
                       ("lose", "Anker ohne erkennbare Einheit"),
                       ("fortsetzung", "Absatz-Anker, deren Abruf Text zurücklässt")):
        if nach_art[art]:
            print(f"⚠️  {len(nach_art[art])} {titel}:")
            for b in nach_art[art]:
                stelle = f"{b['datei']}:{b['zeile']}" if b["zeile"] else b["datei"]
                print(f"  {stelle}  {b['anker'] or ''}")
                print(f"      {b['hinweis']}")
    if nach_art["gross"]:
        print(f"\nℹ️  {len(nach_art['gross'])} Abschnitte über {GROSS_AB} Zeichen:")
        for b in sorted(nach_art["gross"], key=lambda x: -x["zeichen"]):
            print(f"  {b['datei']}:{b['zeile']}  {b['anker']:<32} {b['zeichen']:>6} Z.")
    print(f"\n{geprueft(bestand)} Anker gesichtet, "
          f"{len(nach_art['fortsetzung'])} mit zurückgelassenem Text, "
          f"{len(nach_art['lose'])} ohne Einheit, {len(nach_art['fence'])} Fence-Fehler, "
          f"{len(nach_art['gross'])} übergroß, "
          f"{len(nach_art['geschwister'])} mit Geschwister-Listenpunkt (kein Befund).")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(
        description="Doku-Abschnitt gezielt abrufen statt die ganze Datei zu lesen.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    p_get = sub.add_parser("get", help="Einen Abschnitt über seinen Anker holen")
    p_get.add_argument("anker")
    # `type=int` allein ließ `--zeilen -3` durch; Pythons Negativ-Slicing schnitt dann die
    # LETZTEN drei Zeilen ab statt auf drei zu begrenzen.
    p_get.add_argument("--zeilen", type=lambda s: max(int(s), 0),
                       help="höchstens N Zeilen (meldet die Kürzung)")
    p_get.add_argument("--nur-vorspann", action="store_true",
                       help="ohne die Unterabschnitte")
    p_get.set_defaults(fn=cmd_get)

    p_toc = sub.add_parser("toc", help="Abschnitte einer Datei mit Anker und Größe")
    p_toc.add_argument("datei", help="Pfad oder eindeutiger Teil davon")
    p_toc.set_defaults(fn=cmd_toc)

    sub.add_parser("audit", help="Anker sichten, deren Abrufeinheit fragwürdig ist"
                   ).set_defaults(fn=cmd_audit)

    args = p.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
