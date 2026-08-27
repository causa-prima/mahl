"""Tests für ordinale.py – selbstvergebene Gliederungsnummern in neuen Zeilen.

Warum (S124): Nach der Anker-Migration (OBS-S112-7) war der Bestand nummernfrei, aber nichts
hielt ihn so. Eine Nummer im Verweistext ist eine **zweite Adresse** neben dem Anker – der Anker
wird geprüft, die Nummer nicht. Zwei bereits tote Verweise lagen im Bestand („kaizen Schritt 5"
für einen Schritt 7, „Script-Output Abschnitt 9" ohne Entsprechung), beide unbemerkt.

Zwei Klassen, bewusst verschieden behandelt:
  1. **Blockierend** – nummerierte Überschrift, Nummer im Anker-Linktext, ordinaler Absatz-Lead.
     Strukturell erkennbar, praktisch keine Fehlalarme.
  2. **Nur protokolliert** – Mengenangaben („alle vier Agenten"). Am Bestand gemessen wären
     65–75 % davon Fehlalarm; ein Hook, der so oft falsch anschlägt, wird weggeklickt und
     verliert auch für die richtigen Treffer die Wirkung. Die Quote für NEUE Zeilen ist damit
     aber nicht gemessen – deshalb Log statt Urteil, bis Daten vorliegen.

Geprüft werden nur **hinzugekommene** Zeilen: Der Bestand enthält legitime Altfälle, und ein
Edit an einer solchen Datei darf nicht kollateral blockieren.
"""
import os
import sys
from importlib import import_module

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "scripts"))
ordinale = import_module("ordinale")


# --- Muster 1: nummerierte / buchstabierte Überschrift ------------------------

def test_nummerierte_ueberschrift_wird_gefunden():
    assert ordinale.ordinale_in("## 5. Findings präsentieren")


def test_buchstabierte_ueberschrift_wird_gefunden():
    assert ordinale.ordinale_in("## A) Neue Maßnahmen")


def test_ueberschrift_mit_ordinalwort_wird_gefunden():
    assert ordinale.ordinale_in("### Gate 1: Implementierung")
    assert ordinale.ordinale_in("## Schritt 0: Kontext laden")


def test_ueberschrift_mit_beliebigem_wort_plus_zahl_wird_gefunden():
    """Die Bezugswort-Liste ist die bekannte Schwachstelle – „Agent" fehlte und ließ
    `### Agent 1 – Progressive Disclosure` durch (S124, von einem Sichter gefunden).
    Deshalb zusätzlich wortlos: <Wort> <Zahl> vor einem Gedankenstrich oder Doppelpunkt."""
    assert ordinale.ordinale_in("### Agent 1 – Progressive Disclosure")
    assert ordinale.ordinale_in("## Runde 2: Nacharbeit")


def test_ueberschrift_mit_zahl_ohne_trenner_bleibt_erlaubt():
    """`## Claude 5 als Modell` ist keine Gliederung – ohne Trenner kein Treffer."""
    assert ordinale.ordinale_in("## Claude 5 als Modell") == []


def test_klammer_nummernbereich_wird_gefunden():
    """`die **Split-Schritte** (1–4)` – Bereichsverweis auf eine Liste darunter."""
    assert ordinale.ordinale_in("die **Split-Schritte** (1–4) zerteilen die Menge")


def test_jahreszahl_in_klammern_ist_kein_bereich():
    assert ordinale.ordinale_in("Das Projekt startete (2024) mit einer Skizze.") == []


def test_session_nummer_ist_eine_id(tmp_path):
    """`## Session 123 – 2026-08-21` ist eine Periodenmarke, keine Gliederungsposition –
    dieselbe Klasse wie `S124` in einer Tracker-ID, von außen vergeben."""
    assert ordinale.ordinale_in("## Session 123 – 2026-08-21") == []


def test_nummer_aus_dem_dateinamen_ist_identitaet(tmp_path, monkeypatch):
    """`# Szenario 3 – Der schnelle Einkauf` in `szenario_3_einkauf.md`: Die Nummer trägt der
    Dateiname mit, sie IST die Identität des Dokuments und kann nicht wegsortiert werden."""
    monkeypatch.setattr(ordinale.anchors, "REPO_ROOT", tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "szenario_3_einkauf.md").write_text(
        "# Szenario 3 – Der schnelle Einkauf\n", encoding="utf-8")
    assert ordinale.bestand(tmp_path) == []


def test_abweichende_nummer_trotz_dateiname_bleibt_befund(tmp_path, monkeypatch):
    """Nur die Nummer AUS dem Dateinamen ist frei – eine andere bleibt eine Position."""
    monkeypatch.setattr(ordinale.anchors, "REPO_ROOT", tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "szenario_3_einkauf.md").write_text(
        "# Szenario 3 – Einkauf\n\n## Schritt 7: Abschluss\n", encoding="utf-8")
    assert ordinale.bestand(tmp_path)


def test_roemische_ueberschrift_wird_gefunden():
    assert ordinale.ordinale_in("## IV. Abschluss")


def test_namensueberschrift_ist_sauber():
    assert ordinale.ordinale_in("## Findings präsentieren") == []


def test_datum_als_ueberschrift_ist_kein_ordinal():
    """`## 2026-08-26` – die Ziffern sind ein Datum, keine Gliederung."""
    assert ordinale.ordinale_in("## 2026-08-26 Session 124") == []


# --- Muster 2: Nummer im Anker-Linktext --------------------------------------

def test_nummer_im_linktext_wird_gefunden():
    assert ordinale.ordinale_in("weiter mit [Schritt 5](#KZN-findings)")


def test_regel_im_linktext_wird_gefunden():
    assert ordinale.ordinale_in("siehe [Regel 2](#CGC-rolle-typ)")


def test_nackte_zahl_als_linktext_wird_gefunden():
    assert ordinale.ordinale_in("die Achsen [1](#CLU-capability)–[4](#CLU-split)")


def test_namenslinktext_ist_sauber():
    assert ordinale.ordinale_in("weiter mit [Findings präsentieren](#KZN-findings)") == []


def test_dateiname_mit_ziffer_im_linktext_ist_sauber():
    """`e2e-testing.md` trägt eine Ziffer, ist aber keine Gliederungsnummer."""
    assert ordinale.ordinale_in("siehe [docs/process/e2e-testing.md](#E2E-tags)") == []


def test_linktext_ohne_anker_wird_ignoriert():
    """Ein Link auf eine URL ohne Anker ist kein Abschnitts-Verweis."""
    assert ordinale.ordinale_in("[RFC 7232 Abschnitt 2](https://example.org/rfc7232)") == []


# --- Muster 3: ordinaler Absatz-Lead -----------------------------------------

def test_fetter_lead_mit_nummer_wird_gefunden():
    assert ordinale.ordinale_in("**Regel 3 – Verwechslungsschutz.**")


def test_fetter_lead_mit_buchstabe_wird_gefunden():
    assert ordinale.ordinale_in("- **A) Session abschließen** (empfohlen)")


def test_lead_mit_anker_davor_wird_gefunden():
    assert ordinale.ordinale_in('<a id="RVW-spawn"></a>**1. Frischen Auditor spawnen.**')


def test_markdown_ordered_list_ist_erlaubt():
    """Markdown zählt selbst weiter – ein Einschub verschiebt nichts von Hand."""
    assert ordinale.ordinale_in("1. **Frischen Auditor spawnen.** Agent-Tool mit …") == []


# --- Abgrenzungen ------------------------------------------------------------

def test_codeblock_wird_uebersprungen():
    """`# 1. Schritt` in einem Python-Block ist ein Kommentar, keine Überschrift."""
    text = "```python\n# 1. Schritt: laden\n```"
    assert ordinale.ordinale_in(text) == []


def test_marker_hebt_die_zeile_auf():
    assert ordinale.ordinale_in("## Gate 1: Implementierung  <!-- ordinal-ok -->") == []


def test_fundstelle_traegt_zeilennummer_und_text():
    treffer = ordinale.ordinale_in("Zeile eins\n## 5. Findings")
    assert treffer[0][0] == 2
    assert "5. Findings" in treffer[0][1]


# --- nur neue Zeilen ---------------------------------------------------------

def test_unveraenderte_altlast_blockiert_nicht():
    alt = "## 5. Findings\nText."
    neu = "## 5. Findings\nText.\nEin neuer, sauberer Satz."
    assert ordinale.neue_ordinale(alt, neu) == []


def test_neu_hinzugefuegtes_ordinal_wird_gefunden():
    alt = "## Findings\nText."
    neu = "## Findings\nText.\n## 6. Umsetzen"
    assert ordinale.neue_ordinale(alt, neu)


def test_verschobene_zeile_gilt_nicht_als_neu():
    """Ein Einschub oben darf die unveränderte Altlast unten nicht neu erscheinen lassen."""
    alt = "## 5. Findings"
    neu = "Neuer Absatz.\n\n## 5. Findings"
    assert ordinale.neue_ordinale(alt, neu) == []


# --- Nicht-Markdown: nur der Verweis-Fall gilt --------------------------------

def test_python_kommentar_ist_keine_ueberschrift():
    """`# 1. Schritt` ist in .py ein Kommentar – Muster 1 darf dort nicht greifen."""
    assert ordinale.ordinale_in("# 1. Schritt: laden", markdown=False) == []


def test_verweis_gilt_auch_ausserhalb_markdown():
    """Der Klartext-Verweis im Code ist genau der Fall, den S124 im Produktionscode fand."""
    treffer = ordinale.ordinale_in(
        "// Domänentyp (docs/guidelines/coding-guideline-csharp.md#CGC-x, Regel 5)",
        markdown=False)
    assert treffer


def test_markdown_default_prueft_alle_muster():
    assert ordinale.ordinale_in("## 5. Findings")


# --- Paragraph und Zeilennummer: strukturell eindeutig, deshalb blockierend ---

def test_paragraph_verweis_wird_gefunden():
    """`§3` war in S124 viermal im Bestand – zweimal bereits tot, weil die Guideline
    ihre Paragraphen längst durch Namen ersetzt hatte. Die Form ist eindeutig: `§` plus
    Zahl ist immer ein Positionsverweis, nie ein Messwert."""
    assert ordinale.ordinale_in("bräuchte aber nach §3 einen Ktor-Guard", markdown=False)
    assert ordinale.ordinale_in("- Meldung am Feld (UX-Guideline §4: nah am Element)")


def test_fremdbestimmter_paragraph_ist_erlaubt():
    """RFC, ISO, DIN, Gesetz: Die Nummer vergibt eine externe Autorität, das Projekt kann
    sie nicht wegsortieren – der einzige Fall, in dem eine Nummer die bessere Adresse ist."""
    assert ordinale.ordinale_in("// 200-Body wäre falsch (RFC 7232 §4.1).",
                                markdown=False) == []
    assert ordinale.ordinale_in("nach ISO 8601 §3.2 formatiert", markdown=False) == []


def test_zitiertes_beispiel_ist_kein_verweis():
    """Ein Verweis zeigt auf etwas, ein Zitat führt etwas vor. Die Regel-Dokumentation muss
    „§2" und „Zeile 304" nennen dürfen, um zu erklären, was sie verbietet – in
    Anführungszeichen steht ein Beispiel, nie eine Adresse. Ohne diese Ausnahme bräuchten
    die fünf Illustrationsstellen im Bestand je einen `ordinal-ok`-Marker."""
    assert ordinale.ordinale_in('Verweise standen als Prosa – „§2", „Sektion Security".') == []
    assert ordinale.ordinale_in('sagt „Zeile 304 → {}" nicht, welcher Block gemeint ist',
                                markdown=False) == []


def test_code_span_ist_auch_ein_zitat():
    """Backticks zitieren wie Anführungszeichen – in Markdown und in Kommentaren gleichermaßen.
    Ohne diese Ausnahme kann keine Doku mehr über einen `§2`-Verweis schreiben, ohne ihn zu
    setzen; der Hook hat genau daran den Kommentar blockiert, der die Regel erklärt."""
    assert ordinale.ordinale_in("dort lag ein toter `§2`-Verweis in der Datei",
                                markdown=False) == []


def test_verweis_neben_einem_zitat_bleibt_ein_befund():
    """Die Ausnahme gilt der zitierten Stelle, nicht der ganzen Zeile."""
    assert ordinale.ordinale_in('„Beispiel" – gilt nach §3 des Dokuments', markdown=False)


def test_zeilennummer_als_verweis_wird_gefunden():
    """Der fragilste Verweis überhaupt: `Zeile 605` verschiebt sich bei JEDEM Edit der
    Zieldatei. In S124 war die Angabe im Bestand bereits falsch."""
    assert ordinale.ordinale_in("Der Deny-Text (Zeile 605 und analog 568) bietet an:")


def test_eigene_zeilenangabe_im_werkzeug_output_ist_erlaubt():
    """`Zeile 3:` als Präfix einer Fehlermeldung benennt die Stelle, die das Werkzeug
    gerade gelesen hat – erzeugt zur Laufzeit, nicht von Hand gepflegt."""
    assert ordinale.ordinale_in("Zeile 3: Feld fehlt", markdown=False) == []


# --- Mengenangaben: nur protokolliert, nie blockierend ------------------------

def test_mengenangabe_wird_erkannt():
    assert ordinale.mengenangaben_in("Warte bis alle vier Agenten fertig sind.")


def test_mengenangabe_ist_kein_blockierendes_ordinal():
    assert ordinale.ordinale_in("Warte bis alle vier Agenten fertig sind.") == []


def test_bestand_findet_ordinal_in_markdown(tmp_path, monkeypatch):
    monkeypatch.setattr(ordinale.anchors, "REPO_ROOT", tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("## 5. Findings\n", encoding="utf-8")
    funde = ordinale.bestand(tmp_path)
    assert funde and funde[0][0] == "docs/a.md"


def test_bestand_respektiert_die_muster_ausnahme(tmp_path, monkeypatch):
    """Zweite Stufe: Die Tests der Prüfwerkzeuge führen die Muster als Eingabe – dort ist
    `## 5. Findings` der Testfall, kein Befund. Der Rest der Datei bleibt geprüft; deshalb
    eine Muster- und keine Datei-Ausnahme (S124: in einer pauschal ausgeschlossenen
    Testdatei lag ein toter Verweis)."""
    monkeypatch.setattr(ordinale.anchors, "REPO_ROOT", tmp_path)
    monkeypatch.setitem(ordinale.anchors.MUSTER_AUSNAHMEN, "t/test_x.py",
                        frozenset({"ordinal"}))
    (tmp_path / "t").mkdir()
    (tmp_path / "t" / "test_x.py").write_text("# gilt nach §3 der Regel\n", encoding="utf-8")
    (tmp_path / "t" / "test_y.py").write_text("# gilt nach §3 der Regel\n", encoding="utf-8")
    funde = ordinale.bestand(tmp_path)
    assert [rel for rel, *_ in funde] == ["t/test_y.py"]


def test_bestand_ueberspringt_history(tmp_path, monkeypatch):
    """docs/history/ hält den Zustand von damals – dort ist die Nummer korrekt."""
    monkeypatch.setattr(ordinale.anchors, "REPO_ROOT", tmp_path)
    (tmp_path / "docs" / "history").mkdir(parents=True)
    (tmp_path / "docs" / "history" / "s1.md").write_text("## 5. Alt\n", encoding="utf-8")
    assert ordinale.bestand(tmp_path) == []


def test_bestand_wendet_markdown_regel_pro_dateityp_an(tmp_path, monkeypatch):
    """`# 2. Schritt` in .py ist ein Kommentar – der Bestand darf ihn nicht melden."""
    monkeypatch.setattr(ordinale.anchors, "REPO_ROOT", tmp_path)
    (tmp_path / "s.py").write_text("# 2. Schritt: laden\n", encoding="utf-8")
    assert ordinale.bestand(tmp_path) == []


def test_relativsatz_ist_keine_mengenangabe():
    """„…der beide Seiten benennt" – „beide" ist Objekt, kein Ordinalbezug."""
    assert ordinale.mengenangaben_in("ein Hinweis, der beide Seiten benennt") == []
