#!/usr/bin/env python3
"""Selbstvergebene Gliederungsnummern finden – Kernlogik für Hook und CLI.

Warum (S124): Die Anker-Migration (OBS-S112-7) ersetzte „Schritt 5" durch Namen, weil eine
Nummer im Verweistext eine **zweite Adresse** neben dem Anker ist: Der Anker wird geprüft, die
Nummer nicht. Sie wird bei Umsortierung still falsch – zwei solche Verweise lagen bereits tot im
Bestand. Nach der Migration hielt nichts den Zustand; dieses Modul tut es.

Legitim bleibt **fremdbestimmte** Nummerierung – von einer externen Autorität vergeben (RFC,
Gesetz, fremde Spec). Nicht legitim ist „steht in einer anderen Datei": Eine ADR-Punktnummer
schreiben dieselben Autoren wie eine Abschnittsnummer (S124, von einem Prüf-Subagenten belegt).

Zwei Klassen, bewusst verschieden scharf:

**Blockierend** (`ordinale_in`) – strukturelle Muster mit nahezu keinen Fehlalarmen:
  - **Überschrift**   nummeriert/buchstabiert  `## 5. Findings`, `### Gate 1:`, `## A) Maßnahmen`
  - **Verweistext**   Nummer im Anker-Linktext `[Schritt 5](#KZN-…)`, `[4](#CLU-…)`
  - **Absatz-Lead**   ordinal, fett            `**Regel 3 – …**`, `- **A) Session abschließen**`

Die Muster tragen Namen statt Nummern – aus eigener Erfahrung: Der Vorgänger dieses Docstrings
zählte `1./2./3.`, während der Code darunter schon bei `2b)` und `2c)` stand. Genau das Rutschen,
gegen das dieses Werkzeug gebaut ist, war hier zuerst eingetreten.

**Nur protokolliert** (`mengenangaben_in`) – „alle vier Agenten". Am Bestand gemessen wären
65–75 % Fehlalarm (S124: 22 von 65 behandlungsbedürftig). Ein Hook, der so oft falsch
anschlägt, wird weggeklickt und verliert auch für die richtigen Treffer die Wirkung. Die Quote
für **neue** Zeilen ist damit aber nicht gemessen – der Bestand besteht überwiegend aus
Code-Kommentaren, die selten neu entstehen. Deshalb Log statt Urteil, bis Daten vorliegen.

Bewusst NICHT erfasst: Markdown-Ordered-Lists (`1.` am Zeilenanfang). Dort zählt Markdown
selbst weiter; ein Einschub verschiebt nichts, was von Hand gepflegt werden müsste. Verweise
VON außen auf solche Listenpunkte fängt das Verweistext-Muster, sobald sie über einen Anker laufen.

Zeilen-Ausnahme: `ordinal-ok` in der Zeile.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import anchors  # noqa: E402

MARKER = "ordinal-ok"

# Wörter, die im Verweistext eine Gliederungsposition bezeichnen. Die Liste ist die bekannte
# Schwachstelle – zweimal hat eine zu enge Auswahl echte Fälle durchgelassen (S124: „Gate",
# „Dimension" fehlten). Die wortlose Überschriften-Variante unten fängt deshalb zusätzlich
# ohne Bezugswort.
_BEZUG = (r"Schritte?|Punkte?|Sektion|Abschnitt|Regel|Phase|Gate|Ebene|Stufe|Kapitel|Teil|"
          r"Dimension|Check|Runde|Frage|Kategorie|Rang|Achse|Dim")

# --- Überschrift: Ziffer/Buchstabe/römisch als Präfix, oder Bezugswort + Zahl. ---
_H_PRAEFIX = re.compile(r"^\s{0,3}#{1,6}\s+(?:\d+[.:)]|[A-H][.)]|[IVX]{1,4}[.)])\s")
_H_WORT = re.compile(rf"^\s{{0,3}}#{{1,6}}\s+(?:{_BEZUG})\s+\d")
# Wortlos, weil die Liste oben zweimal versagt hat („Gate", dann „Agent"): <Wort> <Zahl>,
# gefolgt von einem Trenner. Der Trenner grenzt gegen „## Claude 5 als Modell" ab.
_H_FREI = re.compile(r"^\s{0,3}#{1,6}\s+\w+\s+\d+\s*[–—:-]")
# IDs, keine Positionen: Die Session-Zählung ist von außen vergeben (wie `S124` in einer
# Tracker-ID) und lässt sich nicht wegsortieren. Bewusst eine ID-Liste, keine Gliederungswort-
# Liste – letztere hat zweimal versagt und wird deshalb gerade NICHT erweitert.
_ID_UEBERSCHRIFT = re.compile(r"^\s{0,3}#{1,6}\s+Session\s+\d+\b", re.IGNORECASE)
# Nummernbereich in Klammern: `die **Split-Schritte** (1–4)` verweist auf Positionen einer
# Liste. Vierstellige Zahlen sind Jahre, keine Bereiche.
_BEREICH = re.compile(r"\(\s*\d{1,3}\s*[–—-]\s*\d{1,3}\s*\)")

# --- Verweistext: Bezugswort + Zahl, oder nackte Zahl. Nur bei Zielen mit `#`. ---
_LINK_WORT = re.compile(rf"\[[^\]]*\b(?:{_BEZUG})\.?\s*\d[^\]]*\]\([^)]*#[\w.-]+\)")
_LINK_ZAHL = re.compile(r"\[\s*\d+(?:\.\d+)?\s*\]\([^)]*#[\w.-]+\)")

# Klartext-Form desselben Verweises im Code: `// … datei.md#ANKER, Regel 5`. Dort gibt es  ordinal-ok
# keine Link-Syntax – eine Terminal-Meldung und ein Quellcode-Kommentar können sie nicht tragen.
_KLARTEXT_WORT = re.compile(rf"[\w./-]+\.md#[\w-]+[^\n]{{0,80}}?\b(?:{_BEZUG})\.?\s*\d")

# --- Absatz-Lead: fett, optional mit Anker davor, Ziffer/Buchstabe INNERHALB der Sterne. ---
# `1. **Titel**` (Ordered List) trifft nicht zu – dort steht die Ziffer davor.
_LEAD = re.compile(
    rf'^\s*(?:[-*]\s+)?(?:<a id="[\w-]+"></a>)?\*\*(?:\d+[.:)]|[A-H]\)|(?:{_BEZUG})\s+\d\s*[–-])')

# --- Paragraph / Zeilennummer: Verweisformen, die auch ohne Anker eindeutig sind. ---
# Beide fand S124 nur durch Sichten, weil sie kein Bezugswort tragen und keinen Link brauchen.
# `§` ist immer eine Position, nie ein Messwert – außer die Nummer kommt von außen (RFC/ISO/
# Gesetz), dann ist sie die bessere Adresse. `Zeile N` ist die fragilste Form überhaupt: Sie
# verschiebt sich bei jedem Edit der Zieldatei; im Bestand war eine solche Angabe schon falsch.
_FREMDE_NORM = re.compile(r"\b(?:RFC|ISO|DIN|EN|IEEE|Art\.?|Artikel|BGB|StGB|DSGVO)\s*[\d.:-]*\s*$")
_PARAGRAPH = re.compile(r"§\s*\d")
_ZEILENVERWEIS = re.compile(r"\bZeile\s+\d+")

_FENCE = re.compile(r"^\s*(?:```|~~~)")

# Mengenangaben: Zahlwort als Attribut eines Substantivs. Der Artikel muss im Nominativ/Akkusativ
# stehen – „der beide Seiten benennt" ist ein Relativsatz, kein Ordinalbezug (S124-Fehlalarm).
_MENGE = re.compile(
    r"\b(?:alle[nr]?|die|den)\s+"
    r"(zwei|drei|vier|fünf|sechs|sieben|acht|neun|zehn)\s+"
    r"([A-ZÄÖÜ][A-Za-zÄÖÜäöüß-]{2,}|[a-zäöüß-]{3,})",
    re.IGNORECASE)


def _pruefbare_zeilen(text: str):
    """(Nummer, Zeile) je Zeile außerhalb von Codeblöcken und ohne Marker."""
    im_block = False
    for nr, zeile in enumerate(text.splitlines(), 1):
        if _FENCE.match(zeile):
            im_block = not im_block
            continue
        if im_block or MARKER in zeile:
            continue
        yield nr, zeile


def _zahlen_im_dateinamen(rel: str) -> set[str]:
    """Zahlen, die der Dateiname selbst trägt.

    `# Szenario 3 – Der schnelle Einkauf` in `szenario_3_einkauf.md`: Die Nummer IST die
    Identität des Dokuments, sie steht im Dateinamen und kann nicht wegsortiert werden –
    anders als eine Position innerhalb eines Dokuments. Eine ABWEICHENDE Zahl in derselben
    Datei bleibt ein Befund.
    """
    return set(re.findall(r"\d+", rel.rsplit("/", 1)[-1]))


def ordinale_in(text: str, markdown: bool = True,
                freie_zahlen: set[str] | None = None) -> list[tuple[int, str, str]]:
    """Blockierende Fundstellen als (Zeilennummer, Zeile, Musterbezeichnung).

    `markdown=False` prüft nur den Verweis-Fall: In `.py`/`.cs`/`.ts` leitet `#` einen
    Kommentar ein und `**` ist gewöhnlicher Text – Überschrift und Absatz-Lead träfen dort massenhaft
    falsch. Der Verweis dagegen ist gerade dort real (S124 fand 18 Doku-Verweise im
    Produktionscode, davon 10 mit Abschnittsnummer).
    """
    treffer = []
    frei = freie_zahlen or set()
    for nr, zeile in _pruefbare_zeilen(text):
        if _ID_UEBERSCHRIFT.match(zeile):
            continue
        if markdown and (_H_PRAEFIX.match(zeile) or _H_WORT.match(zeile)
                         or _H_FREI.match(zeile)):
            if frei and set(re.findall(r"\d+", zeile)) <= frei:
                continue  # die Nummer trägt der Dateiname – Identität, keine Position
            treffer.append((nr, zeile.strip(), "nummerierte Überschrift"))
        elif _LINK_WORT.search(zeile) or _LINK_ZAHL.search(zeile) or (
                not markdown and _KLARTEXT_WORT.search(zeile)):
            treffer.append((nr, zeile.strip(), "Nummer im Verweistext"))
        elif _paragraph_verweis(zeile):
            treffer.append((nr, zeile.strip(), "Paragraphen-Verweis"))
        elif _zeilen_verweis(zeile):
            treffer.append((nr, zeile.strip(), "Verweis auf eine Zeilennummer"))
        elif markdown and _BEREICH.search(zeile):
            treffer.append((nr, zeile.strip(), "Nummernbereich"))
        elif markdown and _LEAD.match(zeile):
            treffer.append((nr, zeile.strip(), "ordinaler Absatz-Lead"))
    return treffer


def _zitiert(zeile: str, pos: int) -> bool:
    """Ob die Stelle innerhalb von Anführungszeichen liegt.

    Ein Verweis zeigt auf etwas, ein Zitat führt etwas vor: Die Regel-Dokumentation muss ein
    Paragraphenzeichen samt Nummer nennen dürfen, um zu erklären, was sie verbietet. Ohne
    diese Unterscheidung bräuchten allein die Illustrationsstellen dieses Werkzeugs fünf
    `ordinal-ok`-Marker – und ein Marker, den man routinemäßig setzt, ist keiner mehr.

    Grenze, bewusst offen: Läuft ein Zitat über einen Zeilenumbruch, sieht diese Prüfung nur
    die halbe Klammer und meldet. Das ist die seltenere Lage und mit einer Umformulierung
    behoben; eine mehrzeilige Zustandsverfolgung wäre teurer als der Fall wert ist.
    """
    # Gezählt statt gepaart: Der Bestand mischt typografische und gerade Anführungszeichen
    # innerhalb desselben Zitats, ein Paar-Matching müsste jede Kombination kennen.
    # Ungerade Zahl links von der Stelle = mittendrin. Der Apostroph bleibt bewusst draußen –
    # er ist in Prosa und Code kein Zitatzeichen.
    return sum(zeile.count(z, 0, pos) for z in "„“”\"»«`") % 2 == 1


def _paragraph_verweis(zeile: str) -> bool:
    """`§` + Zahl, außer die Nummer stammt von einer externen Norm oder steht im Zitat."""
    return any(not _FREMDE_NORM.search(zeile[:m.start()]) and not _zitiert(zeile, m.start())
               for m in _PARAGRAPH.finditer(zeile))


def _zeilen_verweis(zeile: str) -> bool:
    """`Zeile N` als Verweis – nicht als selbst erzeugtes Meldungs-Präfix (`Zeile 3: …`)."""
    return any(not zeile[m.end():].lstrip().startswith(":") and not _zitiert(zeile, m.start())
               for m in _ZEILENVERWEIS.finditer(zeile))


def mengenangaben_in(text: str) -> list[tuple[int, str, str]]:
    """Fundstellen der Log-Klasse als (Zeilennummer, Zeile, Fundstück)."""
    return [(nr, zeile.strip(), m.group(0))
            for nr, zeile in _pruefbare_zeilen(text)
            for m in _MENGE.finditer(zeile)]


def _neu_hinzugekommen(pre: str, post: str) -> str:
    """Nur Zeilen, die es vorher nirgends gab – Verschieben zählt nicht als neu."""
    alt = set(pre.splitlines())
    return "\n".join(z for z in post.splitlines() if z not in alt)


def neue_ordinale(pre: str, post: str) -> list[tuple[int, str, str]]:
    """Blockierende Fundstellen ausschließlich in hinzugekommenen Zeilen.

    Der Bestand enthält legitime Altfälle (Ordered Lists, historische Messwerte); ein Edit an
    einer solchen Datei darf nicht kollateral blockieren. Die Zeilennummern beziehen sich auf
    den Auszug, nicht auf die Datei – für die Meldung zählt der Zeileninhalt.
    """
    return ordinale_in(_neu_hinzugekommen(pre, post))


def neue_mengenangaben(pre: str, post: str) -> list[tuple[int, str, str]]:
    """Log-Klasse ausschließlich in hinzugekommenen Zeilen."""
    return mengenangaben_in(_neu_hinzugekommen(pre, post))


def bestand(wurzel: Path | None = None) -> list[tuple[str, int, str, str]]:
    """Alle blockierenden Fundstellen im Repo als (Datei, Zeile, Text, Muster).

    Das Gegenstück zum Hook: Der sieht nur Edit/Write, diese Sicht auch alles, was per
    `git merge`, `mv` oder von Hand hereinkommt – dieselbe Lücke, die bei den Ankern das
    `anker-defekt`-Modul der Session-Agenda schließt.
    """
    wurzel = wurzel or anchors.REPO_ROOT
    funde = []
    # Dieselbe Iteration wie die Anker-Prüfung – `os.walk` mit Pruning statt `rglob("*")`,
    # das erst durch `node_modules` hindurchliefe (dort: 3161 ms → 28 ms). Bewusst kein
    # Nachbau: Zwei Ausschlusslisten driften auseinander, und die Divergenz fällt erst auf,
    # wenn eine Seite blind geworden ist (CM-S116-1).
    for datei in sorted(anchors.relevante_dateien(wurzel)):
        rel = datei.relative_to(wurzel).as_posix()
        if "ordinal" in anchors.ausnahmen_fuer(rel):
            continue  # führt die Muster als Eingabe – siehe anchors.MUSTER_AUSNAHMEN
        try:
            text = datei.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for nr, zeile, art in ordinale_in(text, markdown=rel.endswith(".md"),
                                          freie_zahlen=_zahlen_im_dateinamen(rel)):
            funde.append((rel, nr, zeile, art))
    return funde


def main() -> None:
    funde = bestand()
    if not funde:
        print("✓ Keine selbstvergebenen Gliederungsnummern im Bestand.")
        return
    for rel, nr, zeile, art in funde:
        print(f"{rel}:{nr}  [{art}]  {zeile[:120]}")
    print(f"\n{len(funde)} Fundstelle(n). Namen statt Nummern; bewusster Einzelfall → "
          f"`{MARKER}` in die Zeile.")
    sys.exit(1)


if __name__ == "__main__":
    main()
