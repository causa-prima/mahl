"""Tests für doc.py – gezielter Abruf eines Abschnitts über seinen Anker.

Warum (OBS-S114-2): `docs/guidelines` und `docs/process` sind zusammen 20,4 % des gesamten
Read-Volumens (61 Sessions, `read-breakdown.py --by-area`), bei Ø 11.856 Zeichen je Read und
nur 6 % gezielten Zugriffen – praktisch jeder Aufruf liest das ganze Dokument, weil es keinen
Weg gab, einen einzelnen Abschnitt zu holen. Der Gegenbeleg steht im selben Datensatz:
`docs/history` liegt bei 72 % gezielt, denn dort existiert mit `decisions.py` ein Abrufweg.

**Scope-Regel** (User-Entscheid S125), zwei Fälle:
  - **Überschriften-Anker** → bis zur nächsten Überschrift, die *gleichrangig oder
    höherrangig* ist. Unterabschnitte gehören also dazu. Die Alternativen (bis zur nächsten
    Überschrift beliebiger Ebene / bis zum nächsten Anker) sparen im Median nur ~200 Zeichen
    und erkaufen das durch **stilles Abschneiden**: Wer `CGC-domain-typen` abruft, bekäme den
    Vorspann ohne die Regeln und hätte keinen Anhaltspunkt, dass etwas fehlt.
  - **Absatz-Anker** → nur der zusammenhängende Block, in dem der Anker steht. Am Bestand
    validiert (35 Absatz-Anker): Bei 21 identisch zur Alternative; bei 6 ist diese Regel
    sachlich richtig und die Alternative falsch (sie zöge den nächsten Arbeitsschritt mit
    hinein); bei 8 zeigt sie ein Gliederungsproblem der Doku an, das behoben wird, statt es
    durch eine Heuristik zu kaschieren – fehlt eine Überschrift, wird sie ergänzt.

Die Kürzung (`--zeilen`) muss sich selbst melden. Ein Ergebnis, das vollständig aussieht und
es nicht ist, ist hier die teuerste Fehlerklasse – dieselbe, die gegen O2/O3 entschieden hat.
"""
from importlib import import_module

import pytest

doc = import_module("prozesscode.doc")
anchors = import_module("prozesscode.anchors")


# --- Fixtures ----------------------------------------------------------------
GUIDELINE = """# C#-Guideline

<a id="CGC-inhalt"></a>
## Inhalt
Kurzer Vorspann.

<a id="CGC-domain-typen"></a>
## Domänentypen
Vorspann des Abschnitts.

<a id="CGC-regeln"></a>
### Regeln
Erste Regel.

### Ohne Anker
Auch dieser Unterabschnitt gehört zu Domänentypen.

<a id="CGC-tests"></a>
## Tests
Letzter Abschnitt.
"""

ABSATZ = """# Skill

<a id="SKL-schritte"></a>
## Schritte

1. <a id="SKL-eins"></a>**Erster Schritt.** Beschreibung.
   - Unterpunkt A
   - Unterpunkt B

2. <a id="SKL-zwei"></a>**Zweiter Schritt.** Beschreibung.

3. **Dritter Schritt ohne eigenen Anker.** Beschreibung.

<a id="SKL-frei"></a>
**Freistehender Absatz.** Zeile eins.
Zeile zwei desselben Blocks.

Nachsatz, der NICHT mehr dazugehört.
"""

CODEBLOCK = """# Doku

<a id="DOC-befehl"></a>
## Befehl
Aufruf:

```bash
# Kommentar mit Raute, der keine Überschrift ist

python3 script.py
```

Nachtext im selben Abschnitt.

<a id="DOC-danach"></a>
## Danach
Anderer Abschnitt.
"""


def bestand(**dateien):
    return dict(dateien)


# --- Eingerückte Code-Blöcke sind kein Markdown ------------------------------
# S128: `principles.md` zeigt im Prinzip „Abschnitte tragen Anker" ein EINGERÜCKTES Beispiel,
# wie ein Anker aussieht – darin die Zeile `      ## Result-Typen`. doc.py las sie als echte
# Überschrift (`_heading` strippte jede Einrückung), meldete in `toc` einen 5.353-Zeichen-
# Abschnitt, den es nicht gibt, und brach `get KPI-doku-referenzen` dort ab: 1.157 statt 6.325
# Zeichen, 82 % des Abschnitts fehlten – ohne Fehler, ohne Kürzungshinweis, an syntaktisch
# unauffälliger Stelle. Nach CommonMark beginnt ab vier Leerzeichen ein Code-Block.
_EINGERUECKT = """<a id="XX-eins"></a>
## Eins

Text von Eins.

    <a id="YY-beispiel"></a>
    ## So sieht eine Überschrift aus
    … erklärender Beispieltext …

Weiterer Text von Eins.

<a id="XX-zwei"></a>
## Zwei

Text von Zwei.
"""


def test_eingerueckte_ueberschrift_beendet_den_abschnitt_nicht():
    """Der Kernfall: Der Abschnitt läuft über das Beispiel hinweg bis zur echten `##`."""
    text = doc.abschnitt("XX-eins", _EINGERUECKT)
    assert "Text von Eins." in text
    assert "Weiterer Text von Eins." in text, "am eingerückten Beispiel abgebrochen"
    assert "Text von Zwei." not in text, "über die nächste echte ## hinausgelaufen"


def test_eingerueckte_ueberschrift_erscheint_nicht_in_der_gliederung():
    titel = [e["titel"] for e in doc.toc(_EINGERUECKT)]
    assert "So sieht eine Überschrift aus" not in titel
    assert "Eins" in titel and "Zwei" in titel


def test_bis_zu_drei_leerzeichen_bleiben_eine_ueberschrift():
    """Gegenprobe zur Vier-Zeichen-Regel: Darunter ist es echtes Markdown und muss zählen.

    Ohne diese Richtung wäre der Fix ein stumpfes „eingerückt = kein Titel" und schnitte
    leicht eingerückte, gültige Überschriften still aus der Gliederung.
    """
    text = '<a id="A-eins"></a>\n## Eins\n\nText.\n\n   ### Drei Leerzeichen\n\nMehr.\n'
    assert "Drei Leerzeichen" in [e["titel"] for e in doc.toc(text)]


# --- Scope: Überschriften-Anker ----------------------------------------------
def test_ueberschriften_anker_endet_bei_gleichrangiger_ueberschrift():
    """`## Inhalt` endet bei der nächsten `##` – nicht am Dateiende."""
    text = doc.abschnitt("CGC-inhalt", GUIDELINE)
    assert "Kurzer Vorspann." in text
    assert "Domänentypen" not in text


def test_ueberschriften_anker_nimmt_unterabschnitte_mit():
    """Der Kernfall gegen stilles Abschneiden: `##` liefert seine `###` mit."""
    text = doc.abschnitt("CGC-domain-typen", GUIDELINE)
    assert "Vorspann des Abschnitts." in text
    assert "Erste Regel." in text, "Unterabschnitt mit Anker fehlt"
    assert "Auch dieser Unterabschnitt" in text, "Unterabschnitt ohne Anker fehlt"
    assert "Letzter Abschnitt." not in text, "über die nächste ## hinausgelaufen"


def test_unterabschnitt_endet_bei_naechster_gleichrangiger():
    """`###` endet bei der nächsten `###` – auch wenn die keinen Anker trägt."""
    text = doc.abschnitt("CGC-regeln", GUIDELINE)
    assert "Erste Regel." in text
    assert "Auch dieser Unterabschnitt" not in text


def test_unterabschnitt_endet_auch_bei_hoeherrangiger_ueberschrift():
    """Eine `##` beendet einen `###`-Abschnitt ebenfalls – sonst liefe er in den
    Nachbarabschnitt hinein."""
    entfernt = "### Ohne Anker\nAuch dieser Unterabschnitt gehört zu Domänentypen.\n"
    guideline = GUIDELINE.replace(entfernt, "")
    assert guideline != GUIDELINE, ("Fixture-Text nicht getroffen – der Test wäre stumm zum "
                                    "Duplikat des Nachbartests degradiert")
    text = doc.abschnitt("CGC-regeln", guideline)
    assert "Erste Regel." in text
    assert "Letzter Abschnitt." not in text


def test_abschnitt_endet_vor_der_ankerzeile_des_naechsten():
    """Der Anker steht ÜBER seiner Überschrift – ohne Korrektur läge er noch im Abschnitt
    davor, der damit eine fremde Identität mit ausliefert."""
    text = doc.abschnitt("CGC-domain-typen", GUIDELINE)
    assert "CGC-tests" not in text


def test_letzter_abschnitt_reicht_bis_dateiende():
    text = doc.abschnitt("CGC-tests", GUIDELINE)
    assert "Letzter Abschnitt." in text


def test_raute_im_codeblock_beendet_keinen_abschnitt():
    """Gegenprobe zur Ebenen-Regel: `# Kommentar` in einem Bash-Block ist keine Überschrift."""
    text = doc.abschnitt("DOC-befehl", CODEBLOCK)
    assert "python3 script.py" in text
    assert "Nachtext im selben Abschnitt." in text, "am Kommentar im Codeblock abgebrochen"
    assert "Anderer Abschnitt." not in text


# --- Scope: Absatz-Anker -----------------------------------------------------
def test_absatz_anker_liefert_nur_seinen_block():
    """Der Fall, in dem die Block-Regel richtig und die Anker-Regel falsch liegt:
    Der nächste Arbeitsschritt darf nicht mitkommen."""
    text = doc.abschnitt("SKL-eins", ABSATZ)
    assert "Erster Schritt." in text
    assert "Zweiter Schritt." not in text


def test_absatz_anker_nimmt_tiefer_eingerueckte_fortsetzung_mit():
    """Unterpunkte eines Listenpunkts gehören zum Block – sie sind eingerückt."""
    text = doc.abschnitt("SKL-eins", ABSATZ)
    assert "Unterpunkt A" in text
    assert "Unterpunkt B" in text


def test_absatz_anker_endet_an_der_leerzeile_vor_gleich_eingeruecktem_text():
    """Ein nicht eingerückter Nachsatz ist ein eigener Block – hier endet der Abruf.

    Genau dieser Fall ist der Doku-Hinweis: Gehört der Nachsatz inhaltlich dazu, wird er an
    den Block angeschlossen, statt die Regel aufzuweichen."""
    text = doc.abschnitt("SKL-frei", ABSATZ)
    assert "Zeile zwei desselben Blocks." in text
    assert "Nachsatz, der NICHT" not in text


def test_absatz_anker_laeuft_nicht_in_die_naechste_ueberschrift():
    text = doc.abschnitt("SKL-zwei", ABSATZ)
    assert "Zweiter Schritt." in text
    assert "Freistehender Absatz." not in text


# --- Nahtstellen zwischen den Regeln -----------------------------------------
INLINE = """# Titel

<a id="INL-eins"></a>## Erste
Text zu eins.

<a id="INL-zwei"></a>## Zweite
Text zu zwei.

<a id="INL-drei"></a>### Unterabschnitt
Noch mehr.
"""

DICHT = """# X

<a id="DIC-eins"></a>**Erster Punkt.** Text zu eins.
<a id="DIC-zwei"></a>**Zweiter Punkt.** Text zu zwei.
"""

FENCE_IM_BLOCK = """# X

1. <a id="FEN-schritt"></a>**Schritt.** Beschreibung.

   ```bash
   echo hallo

   echo welt
   ```

2. Nächster Schritt.
"""


def test_absatz_anker_endet_vor_dem_naechsten_anker_ohne_leerzeile():
    """Ohne Trennzeile schluckte der erste Block den zweiten Anker samt Inhalt – dieselbe
    Klasse wie stilles Abschneiden, nur andersherum: fremder Inhalt ohne Hinweis."""
    text = doc.abschnitt("DIC-eins", DICHT)
    assert "Text zu eins." in text
    assert "DIC-zwei" not in text
    assert "Zweiter Punkt." not in text


def test_inline_anker_vor_ueberschrift_begrenzt_den_vorherigen_abschnitt():
    """`<a id="X"></a>## Titel` ist laut Modul-Doku eine gültige Schreibweise. Wird sie beim
    Vorwärts-Scan nicht als Überschrift erkannt, läuft der Vorgänger bis Dateiende."""
    text = doc.abschnitt("INL-eins", INLINE)
    assert "Text zu eins." in text
    assert "Text zu zwei." not in text


def test_inline_anker_abschnitt_nimmt_seinen_unterabschnitt_mit():
    text = doc.abschnitt("INL-zwei", INLINE)
    assert "Text zu zwei." in text
    assert "Noch mehr." in text


def test_toc_listet_auch_inline_anker_abschnitte():
    """Sonst fällt ein gültig definierter Abschnitt ersatzlos aus dem Inhaltsverzeichnis."""
    anker = [z["anker"] for z in doc.toc(INLINE)]
    assert "INL-eins" in anker
    assert "INL-zwei" in anker
    assert "INL-drei" in anker


def test_absatz_anker_nimmt_eingerueckten_codeblock_nach_leerzeile_mit():
    """Ein eingerücktes Beispiel ist Fortsetzung des Blocks – auch wenn eine Leerzeile davor
    steht und der Block selbst Leerzeilen enthält."""
    text = doc.abschnitt("FEN-schritt", FENCE_IM_BLOCK)
    assert "echo hallo" in text
    assert "echo welt" in text, "an der Leerzeile im Fence abgebrochen"
    assert "Nächster Schritt." not in text


# --- Kontext-Kopf ------------------------------------------------------------
def test_kopf_nennt_breadcrumb_bis_zum_abschnitt():
    kopf = doc.kopf("CGC-regeln", "docs/guidelines/x.md", GUIDELINE,
                    bestand(**{"docs/guidelines/x.md": GUIDELINE}))
    assert "docs/guidelines/x.md" in kopf
    assert "Domänentypen" in kopf, "Elternabschnitt fehlt im Breadcrumb"
    assert "Regeln" in kopf


def test_kopf_nennt_nachbarn_fuer_das_browsen():
    """Der Grund für den Kopf: sichtbar machen, was NICHT geliefert wurde."""
    kopf = doc.kopf("CGC-domain-typen", "docs/guidelines/x.md", GUIDELINE,
                    bestand(**{"docs/guidelines/x.md": GUIDELINE}))
    assert "CGC-inhalt" in kopf
    assert "CGC-tests" in kopf


def test_kopf_laesst_die_h1_weg():
    """Die H1 ist der Dateititel und stünde redundant neben dem Pfad."""
    kopf = doc.kopf("CGC-regeln", "docs/guidelines/x.md", GUIDELINE,
                    bestand(**{"docs/guidelines/x.md": GUIDELINE}))
    assert "C#-Guideline" not in kopf


def test_kopf_bleibt_knapp():
    """Ein Kopf, der den Abschnitt aufbläht, frisst den Gewinn wieder auf."""
    kopf = doc.kopf("CGC-regeln", "docs/guidelines/x.md", GUIDELINE,
                    bestand(**{"docs/guidelines/x.md": GUIDELINE}))
    assert len(kopf.splitlines()) <= 3


# --- Kürzung meldet sich selbst ----------------------------------------------
def test_kuerzung_wird_ausgewiesen():
    """Ohne diese Meldung wäre `--zeilen` genau der stille Schnitt, gegen den die
    Scope-Regel entschieden wurde."""
    voll = doc.abschnitt("CGC-domain-typen", GUIDELINE)
    gekuerzt, hinweis = doc.kuerze(voll, 3)
    assert len(gekuerzt.splitlines()) == 3
    assert hinweis, "Kürzung ohne Hinweis"
    assert "doc.py get" in hinweis, "Hinweis nennt den Weg zum Volltext nicht"


def test_keine_kuerzung_kein_hinweis():
    voll = doc.abschnitt("CGC-inhalt", GUIDELINE)
    gekuerzt, hinweis = doc.kuerze(voll, 999)
    assert gekuerzt == voll
    assert hinweis == ""


def test_nur_vorspann_schneidet_vor_dem_ersten_unterabschnitt():
    voll = doc.abschnitt("CGC-domain-typen", GUIDELINE)
    vorspann, hinweis = doc.nur_vorspann(voll)
    assert "Vorspann des Abschnitts." in vorspann
    assert "Erste Regel." not in vorspann
    assert hinweis, "auch der Vorspann-Schnitt muss sich melden"


def test_nur_vorspann_ohne_unterabschnitt_meldet_nichts():
    """Die Gegenprobe: eine gemeldete Kürzung, die nicht stattfand, ist derselbe
    Vertrauensbruch wie eine stille Kürzung."""
    voll = doc.abschnitt("CGC-inhalt", GUIDELINE)
    vorspann, hinweis = doc.nur_vorspann(voll)
    assert vorspann == voll
    assert hinweis == ""


def test_beide_zuschnitte_melden_sich_einzeln():
    """Wenn --nur-vorspann UND --zeilen kürzen, darf kein Hinweis den anderen verdrängen –
    sonst ist genau in der Funktion eine stille Kürzung eingebaut, die sie verhindern soll."""
    voll = doc.abschnitt("CGC-domain-typen", GUIDELINE)
    _text, hinweise = doc.zuschnitt(voll, hoechstens=1, ohne_unterabschnitte=True)
    assert len(hinweise) == 2, f"ein Hinweis ging verloren: {hinweise}"


def test_zuschnitt_ohne_vorgabe_laesst_alles_stehen():
    voll = doc.abschnitt("CGC-domain-typen", GUIDELINE)
    text, hinweise = doc.zuschnitt(voll)
    assert text == voll
    assert hinweise == []


def test_zuschnitt_auf_null_zeilen_meldet_sich_ebenfalls():
    """`--zeilen 0` ist ein gültiger Wunsch; als falsy behandelt lieferte er stillschweigend
    den vollständigen Abschnitt – das Gegenteil des Verlangten."""
    voll = doc.abschnitt("CGC-domain-typen", GUIDELINE)
    text, hinweise = doc.zuschnitt(voll, hoechstens=0)
    assert text.strip() == ""
    assert len(hinweise) == 1


def test_negative_zeilenzahl_wird_abgewiesen():
    """Ohne Prüfung schnitte Pythons Negativ-Slicing die LETZTEN n Zeilen ab."""
    with pytest.raises(ValueError):
        doc.zuschnitt("a\nb\nc\n", hoechstens=-2)


# --- toc ---------------------------------------------------------------------
def test_toc_listet_abschnitte_mit_anker_und_groesse():
    zeilen = doc.toc(GUIDELINE)
    anker = [z["anker"] for z in zeilen]
    assert "CGC-domain-typen" in anker
    eintrag = next(z for z in zeilen if z["anker"] == "CGC-domain-typen")
    assert eintrag["titel"] == "Domänentypen"
    assert eintrag["ebene"] == 2
    assert eintrag["zeichen"] > 0


def test_toc_listet_absatz_anker_mit_bereinigtem_titel():
    """Eigener Codepfad: Titel aus dem Listentext, Markdown-Auszeichnung entfernt."""
    eintrag = next(z for z in doc.toc(ABSATZ) if z["anker"] == "SKL-eins")
    assert eintrag["ebene"] == 0
    assert eintrag["titel"].startswith("Erster Schritt.")
    assert "**" not in eintrag["titel"]


def test_toc_zeigt_auch_abschnitte_ohne_anker():
    """Sonst wüsste der Abrufende nicht, dass es sie gibt – und hielte das TOC für
    vollständig."""
    zeilen = doc.toc(GUIDELINE)
    titel = [z["titel"] for z in zeilen]
    assert "Ohne Anker" in titel
    ohne = next(z for z in zeilen if z["titel"] == "Ohne Anker")
    assert ohne["anker"] is None


# --- audit -------------------------------------------------------------------
def test_audit_meldet_absatz_anker_mit_abgeschnittener_fortsetzung():
    """Der Bestandsbefund: 14 von 35 Absatz-Ankern haben Text direkt hinter ihrem Block."""
    befunde = doc.audit(bestand(**{"a.md": ABSATZ}))
    anker = [b["anker"] for b in befunde]
    assert "SKL-frei" in anker, "Nachsatz hinter dem Block nicht gemeldet"


def test_audit_meldet_keinen_absatz_anker_ohne_fortsetzung():
    sauber = "# X\n\n<a id=\"SKL-frei\"></a>\n**Block.** Text.\n\n## Ende\nEgal.\n"
    befunde = doc.audit(bestand(**{"a.md": sauber}))
    assert [b for b in befunde if b["anker"] == "SKL-frei"] == []


def test_audit_klassifiziert_geschwister_getrennt_von_fortsetzung():
    """Eine Aufzählung, in der nur ein Punkt einen Anker trägt, ist normal – der nächste
    Punkt ist kein zurückgelassener Text. Der Eintrag bleibt in der Liste, nur mit
    anderer Art."""
    befunde = doc.audit(bestand(**{"a.md": ABSATZ}))
    zwei = next(b for b in befunde if b["anker"] == "SKL-zwei")
    assert zwei["art"] == "geschwister"


def test_audit_zaehlt_geschwister_trotzdem_mit():
    """Ein stiller Abzug wäre ein Filter, der sich als Vollprüfung ausgibt."""
    befunde = doc.audit(bestand(**{"a.md": ABSATZ}))
    assert any(b["art"] == "geschwister" for b in befunde)


def test_audit_wertet_anderen_listentyp_nicht_als_geschwister():
    """`- ` gefolgt von `1. ` sind nach CommonMark zwei getrennte Listen. Als Geschwister
    eingestuft verschwände ein echtes Gliederungsproblem im „kein Befund"-Topf."""
    gemischt = ('# X\n\n- <a id="MIX-eins"></a>**Punkt.** Text.\n\n'
                '1. Neue Liste, gleiche Einrückung.\n')
    befunde = doc.audit(bestand(**{"a.md": gemischt}))
    eins = next(b for b in befunde if b["anker"] == "MIX-eins")
    assert eins["art"] == "fortsetzung"


def test_audit_meldet_uebergrosse_abschnitte():
    zeile = "Zeile.\n"
    gross = ("# X\n\n<a id=\"XXX-gross\"></a>\n## Groß\n"
             + zeile * (doc.GROSS_AB // len(zeile) + 10))
    befunde = doc.audit(bestand(**{"a.md": gross}))
    assert any(b["anker"] == "XXX-gross" and b["art"] == "gross" for b in befunde)


def test_audit_meldet_anker_ohne_erkennbare_einheit():
    """Eine Leerzeile zwischen Anker und Überschrift macht ihn stillschweigend zum
    Absatz-Anker über einer Leerzeile – der Abruf liefert dann nichts Sinnvolles."""
    getrennt = '# X\n\n<a id="SEP-lose"></a>\n\n## Titel\nText.\n'
    befunde = doc.audit(bestand(**{"a.md": getrennt}))
    assert any(b["anker"] == "SEP-lose" and b["art"] == "lose" for b in befunde)


def test_audit_meldet_unausgeglichene_code_fences():
    """Ein vergessener schließender Fence lässt jede folgende Überschrift unsichtbar werden –
    alle Abschnittsgrenzen dahinter sind still falsch."""
    offen = '# X\n\n<a id="OFF-eins"></a>\n## Eins\n\n```bash\necho hallo\n\n## Zwei\nText.\n'
    befunde = doc.audit(bestand(**{"a.md": offen}))
    assert any(b["art"] == "fence" and b["datei"] == "a.md" for b in befunde)


def test_audit_sichtet_alle_anker_statt_zu_filtern():
    """Prinzip „Bestände werden gesichtet, nicht gefiltert": Die Zahl der geprüften Anker
    muss der Zahl der vorhandenen entsprechen – hier hartkodiert, damit der Test nicht
    dieselbe Formel wie der Prüfling nachbaut."""
    assert doc.geprueft(bestand(**{"a.md": ABSATZ, "b.md": GUIDELINE})) == 8


def test_audit_ignoriert_nicht_markdown_dateien():
    """`anchors.lies_bestand()` liest auch `.py` – und diese Testdatei selbst enthält
    Anker-Strings als Fixture-Datum. Ohne den Filter zählte das Werkzeug seine eigenen
    Tests als Doku-Abschnitte (dieselbe Falle sichert `test_anchors.py` bereits ab)."""
    gemischt = bestand(**{"a.md": GUIDELINE, "test_doc.py": ABSATZ})
    assert doc.geprueft(gemischt) == doc.geprueft(bestand(**{"a.md": GUIDELINE}))
    assert all(b["datei"].endswith(".md") for b in doc.audit(gemischt))


def test_doppelt_definierter_anker_liefert_die_erste_stelle():
    """`anchors.py check` meldet die Dublette; bis sie behoben ist, muss der Abruf
    wenigstens deterministisch die erste Definition liefern statt der letzten."""
    doppelt = ('# X\n\n<a id="DUP-a"></a>\n## Erste\nInhalt eins.\n\n'
               '<a id="DUP-a"></a>\n## Zweite\nInhalt zwei.\n')
    assert "Inhalt eins." in doc.abschnitt("DUP-a", doppelt)


# --- Auflösung ---------------------------------------------------------------
def test_unbekannter_anker_liefert_fehler_statt_leerem_ergebnis():
    with pytest.raises(KeyError):
        doc.abschnitt("GIBT-es-nicht", GUIDELINE)
