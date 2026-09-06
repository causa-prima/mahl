"""Tests für anchors.py – Abschnitts-Anker und ihre Verweise, alle drei Richtungen.

Warum (OBS-S112-7): Verweise zwischen Projektdokumenten standen als Prosa – „§2",
„Sektion Security", „Schritt 4". Kein Werkzeug konnte prüfen, ob das Ziel existiert, und weil
sie auf *Nummern* zeigten, mussten die Nummern stabil bleiben: Wächst der Inhalt, entstehen
Einschübe wie `4b`/`4c` statt einer Neunummerierung. Die Gliederung richtet sich dann nach der
Verweisbarkeit statt nach dem Inhalt.

**Format** (User-Entscheid S124): `<a id="CGT-result"></a>` über der Überschrift, Verweis als
echter Markdown-Link `[CGT-result](../guidelines/coding-guideline-typescript.md#CGT-result)`.
Kein Eigenbau, sondern die etablierte Lösung für stabile Markdown-Anker: klickbar in GitHub
und IDE, grep-bar für Agenten, stabil gegen Titeländerung UND Umsortieren. Die GitHub-eigenen
Auto-Anchors leisten das nicht – sie leiten sich aus dem Titel ab, jede Umbenennung bricht sie.

Drei Prüfrichtungen, jede schließt eine eigene Lücke:
  1. **Vorwärts** – der Verweis zeigt auf einen Anker, den es nicht gibt.
  2. **Pfad** – den Anker gibt es, aber nicht in der verlinkten Datei; der Klick geht ins Leere.
  3. **Rückwärts** – ein Anker verschwindet, obwohl noch Verweise auf ihn zeigen.
Ohne (3) wäre (1) ein stummes Opt-out: Wer den Anker löscht, merkte nichts. Ohne (2) wäre die
Klickbarkeit unzuverlässig, und genau sie ist der Grund für dieses Format.
"""
from importlib import import_module

import pytest

anchors = import_module("prozesscode.anchors")


GUIDELINE = """# TypeScript-Guideline

<a id="CGT-result"></a>
## Result-Typen
Text mit Verweis auf [CGT-naming](#CGT-naming).

<a id="CGT-naming"></a>
## Benennung
Anderer Text.
"""

SKILL = """# Lauf implementieren

<a id="IMP-architektur"></a>
## Architektur-Check
Siehe [CGT-result](../../../docs/guidelines/typescript.md#CGT-result).

<a id="IMP-review"></a>
## Review-Loop
Zurück zu [IMP-architektur](#IMP-architektur).
"""

BESTAND = {"docs/guidelines/typescript.md": GUIDELINE, ".claude/skills/imp/SKILL.md": SKILL}


# --- Anker finden ------------------------------------------------------------
def test_findet_anker_tags():
    assert anchors.anker_in(GUIDELINE) == ["CGT-result", "CGT-naming"]


def test_ueberschrift_allein_ist_kein_anker():
    """Gegenprobe: Sonst gälte jede Überschrift als Anker und nie fehlte einer."""
    assert anchors.anker_in("## Ganz normale Überschrift\n") == []


def test_anker_im_fliesstext_zaehlt_nicht():
    """Ein erwähntes `<a id=…>` in einem Codeblock ist eine Erwähnung, keine Definition."""
    assert anchors.anker_in('Beispiel: `<a id="CGT-x"></a>` schreibt man so.\n') == []


def test_anker_im_listenpunkt_zaehlt():
    """Manche Skills gliedern per nummerierter Liste statt per Überschrift. Sie deswegen
    umzubauen hieße, ~100 Zeilen Unterpunkte auszurücken – viel Diff und Risiko in Dateien,
    die den Arbeitsprozess steuern. Der Anker sitzt dort inline hinter dem Listen-Marker."""
    assert anchors.anker_in('1. <a id="CLS-reflektieren"></a>Session reflektieren\n') == \
        ["CLS-reflektieren"]


def test_anker_hinter_bullet_zaehlt():
    assert anchors.anker_in('- <a id="CLS-x"></a>Punkt\n') == ["CLS-x"]


def test_anker_mitten_im_satz_zaehlt_nicht():
    """Gegenprobe: Nur Zeilenanfang oder Listen-Marker – sonst würde jede Erwähnung
    im Fließtext zur zweiten Definition und der Prüfer meldete Dubletten."""
    assert anchors.anker_in('Der Anker <a id="CGT-x"></a> steht mitten im Satz.\n') == []


# --- Verweise finden ---------------------------------------------------------
def test_findet_verweis_mit_pfad():
    treffer = anchors.verweise_in(SKILL)
    assert ("CGT-result", 5, "../../../docs/guidelines/typescript.md") in treffer


def test_findet_verweis_ohne_pfad():
    """Verweis innerhalb derselben Datei – der Pfad ist leer."""
    assert ("IMP-architektur", 9, "") in anchors.verweise_in(SKILL)


def test_backticks_sind_kein_verweis():
    """Gegenprobe zum alten Format: Nur echte Links zählen, sonst wäre nichts klickbar."""
    assert anchors.verweise_in("Der Anker `CGT-result` steht dort.\n") == []


def test_link_im_fenced_codeblock_ist_kein_verweis():
    """Ein Beispiel im Codeblock zeigt, WIE man verweist – es verweist nicht selbst.
    Ohne diese Ausnahme blockte der Prüfer jede Doku, die ihr eigenes Format erklärt."""
    text = "Beispiel:\n\n```\n[CGT-x](a.md#CGT-x)\n```\n"
    assert anchors.verweise_in(text) == []


def test_link_im_eingerueckten_codeblock_ist_kein_verweis():
    text = "Beispiel:\n\n    [CGT-x](a.md#CGT-x)\n"
    assert anchors.verweise_in(text) == []


def test_link_im_fliesstext_bleibt_ein_verweis():
    """Gegenprobe: Sonst würde die Codeblock-Ausnahme alle echten Verweise verschlucken."""
    assert anchors.verweise_in("Siehe [CGT-x](a.md#CGT-x).\n") == [("CGT-x", 1, "a.md")]


# --- (1) Vorwärts: toter Verweis ---------------------------------------------
def test_verweis_ohne_ziel_wird_gemeldet():
    kaputt = dict(BESTAND)
    kaputt["b.md"] = "Siehe [CGT-fehlt](docs/guidelines/typescript.md#CGT-fehlt).\n"
    assert ("b.md", 1, "CGT-fehlt") in anchors.tote_verweise(kaputt)


def test_aufloesbare_verweise_melden_nichts():
    """Gegenprobe – sonst meldete der Prüfer immer etwas."""
    assert anchors.tote_verweise(BESTAND) == []


# --- (2) Pfad zeigt auf die falsche Datei ------------------------------------
def test_falscher_pfad_wird_gemeldet():
    """Der Anker existiert, aber nicht dort, wohin der Link zeigt – der Klick geht ins Leere."""
    falsch = dict(BESTAND)
    falsch[".claude/skills/imp/SKILL.md"] = SKILL.replace(
        "../../../docs/guidelines/typescript.md", "../../../docs/process/nfr.md")
    fehler = anchors.falsche_pfade(falsch)
    assert fehler == [(".claude/skills/imp/SKILL.md", 5, "CGT-result",
                       "docs/process/nfr.md", "docs/guidelines/typescript.md")]


def test_richtiger_pfad_meldet_nichts():
    assert anchors.falsche_pfade(BESTAND) == []


def test_verweis_ohne_pfad_prueft_die_eigene_datei():
    """Ein leerer Pfad meint dieselbe Datei – zeigt der Anker woanders hin, ist er falsch."""
    falsch = {"a.md": '<a id="AAA-x"></a>\n## T\n',
              "b.md": "Siehe [AAA-x](#AAA-x).\n"}
    fehler = anchors.falsche_pfade(falsch)
    assert fehler and fehler[0][2] == "AAA-x"


# --- (3) Rückwärts: verwaister Verweis nach dem Löschen ----------------------
def test_entfernter_anker_mit_verweisen_wird_gemeldet():
    ohne = GUIDELINE.replace('<a id="CGT-result"></a>\n', "")
    verwaist = anchors.verwaiste(GUIDELINE, ohne,
                                 {".claude/skills/imp/SKILL.md": SKILL})
    assert verwaist == [("CGT-result", [(".claude/skills/imp/SKILL.md", 5)])]


def test_entfernter_anker_ohne_verweise_ist_in_ordnung():
    """Gegenprobe: Ein Anker, auf den niemand zeigt, darf verschwinden."""
    ohne = GUIDELINE.replace('<a id="CGT-naming"></a>\n', "")
    assert anchors.verwaiste(GUIDELINE, ohne, {}) == []


def test_unveraenderte_datei_meldet_nichts():
    assert anchors.verwaiste(GUIDELINE, GUIDELINE, BESTAND) == []


# --- Fundstellen eines Ankers ------------------------------------------------
# Wird ein Abschnitt umbenannt oder umnummeriert, bleiben die Links gültig – aber ihr
# ANZEIGETEXT kann veralten („§4b" zeigt weiter richtig, sagt aber die falsche Nummer). Das
# ist mechanisch nicht prüfbar, weil der Text frei wählbar ist. Prüfbar ist es von Hand,
# sobald jemand die Fundstellen samt Kontext vorgelegt bekommt.
def test_referenzen_liefert_fundstellen_mit_zeile():
    fund = anchors.referenzen("CGT-result", BESTAND)
    assert (".claude/skills/imp/SKILL.md", 5) == fund[0][:2]
    assert "CGT-result" in fund[0][2]


def test_referenzen_findet_auch_verweise_aus_code():
    """Ein Verweis in einer Quelldatei zählt genauso – sonst führte das Umbenennen
    zuverlässig zu veralteten Kommentaren im Code."""
    bestand = dict(BESTAND)
    bestand["Server/Domain/X.cs"] = '// Regel: docs/guidelines/typescript.md#CGT-result\n'
    assert ("Server/Domain/X.cs", 1) in [(d, n) for d, n, _ in
                                         anchors.referenzen("CGT-result", bestand)]


def test_referenzen_ohne_treffer_ist_leer():
    assert anchors.referenzen("CGT-naming", {".claude/skills/imp/SKILL.md": SKILL}) == []


# --- Eindeutigkeit -----------------------------------------------------------
def test_doppelter_anker_wird_gemeldet():
    """Ein Anker ist eine Identität – zweimal vergeben, ist er keine mehr."""
    doppelt = dict(BESTAND)
    doppelt["b.md"] = '<a id="CGT-result"></a>\n## Anderswo\n'
    assert anchors.doppelte(doppelt) == [
        ("CGT-result", ["b.md", "docs/guidelines/typescript.md"])]


def test_eindeutige_anker_melden_nichts():
    assert anchors.doppelte(BESTAND) == []


# --- Welche Dateien geprüft werden -------------------------------------------
# Ein Prüfer, der einen Bereich nicht ansieht, meldet für ihn immer „alles gut" – und sein
# Ausfall löst per Definition nichts aus (CM-S116-1). Genau das passierte in S124: Eine
# `startswith(".")`-Regel sollte `.git` ausschließen und blendete `.claude/**` mit aus, also
# den Bereich mit den meisten Verweisen. 61 frisch gesetzte Anker blieben ungeprüft, während
# `check` grün meldete.
def test_claude_verzeichnis_wird_geprueft(tmp_path):
    (tmp_path / ".claude" / "skills" / "x").mkdir(parents=True)
    (tmp_path / ".claude" / "skills" / "x" / "SKILL.md").write_text(
        '<a id="XXX-a"></a>\n## T\n', encoding="utf-8")
    assert ".claude/skills/x/SKILL.md" in anchors.lies_bestand(tmp_path)


def test_git_verzeichnis_wird_uebersprungen(tmp_path):
    """Gegenprobe: Ohne Ausschluss liefe der Scan über die gesamte Objektdatenbank."""
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "COMMIT_EDITMSG.md").write_text("egal\n", encoding="utf-8")
    assert not any(".git" in p for p in anchors.lies_bestand(tmp_path))


def test_lokale_artefaktordner_werden_uebersprungen(tmp_path):
    """`.pytest_cache/` und `Server/wwwroot/` sind gitignored und ungetrackt – rein lokale
    Cache-/Build-Artefakte ohne Anker. Der Hook las sie bei JEDEM Edit mit (S124, beim
    Sichten der Ziffern-Obermenge aufgefallen: 54 Zeilen Rauschen aus generiertem JS)."""
    (tmp_path / ".pytest_cache" / "v").mkdir(parents=True)
    (tmp_path / ".pytest_cache" / "v" / "nodeids.md").write_text("x", encoding="utf-8")
    (tmp_path / "Server" / "wwwroot" / "assets").mkdir(parents=True)
    (tmp_path / "Server" / "wwwroot" / "assets" / "app.md").write_text("x", encoding="utf-8")
    assert anchors.lies_bestand(tmp_path) == {}


def test_historie_wird_uebersprungen(tmp_path):
    """Dort ist ein Verweis auf den Zustand von damals korrekt und soll stehen bleiben."""
    (tmp_path / "docs" / "history").mkdir(parents=True)
    (tmp_path / "docs" / "history" / "session_1.md").write_text(
        "Siehe [XXX-weg](a.md#XXX-weg).\n", encoding="utf-8")
    assert anchors.lies_bestand(tmp_path) == {}


# --- Verweise aus Python-Dateien ---------------------------------------------
# Die Hook-Meldungen in `prozesscode/hooks/checks/*.py` verweisen auf genau die Guideline-
# Abschnitte, deren Nummern hier abgeschafft werden – und `rop.py` zeigte schon vorher auf
# einen Abschnitt, den es in der genannten Datei nie gab. Ungeprüft bliebe der .py-Bereich
# derselbe blinde Fleck, der `.claude/**` war.
#
# Dort gilt NUR die Klartext-Form `datei.md#ANKER`: Markdown-Link-Syntax wäre in einer
# Terminal-Meldung unlesbar, und die Docstrings der Anker-Werkzeuge zeigen echte Links als
# Beispiel – sie mitzuzählen erzeugte Falschmeldungen im eigenen Werkzeug.
def test_klartext_verweis_in_py_zaehlt():
    text = 'def pruefe():\n    return "Siehe docs/guidelines/typescript.md#CGT-result"\n'
    assert anchors.verweise_aus("x.py", text) == [
        ("CGT-result", 2, "docs/guidelines/typescript.md")]


def test_einrueckung_in_py_ist_kein_codeblock():
    """Die Markdown-Regel „vier Leerzeichen = Codeblock" gilt hier nicht: Python-Code ist
    fast immer eingerückt: Sie würde beinahe jede Hook-Meldung überspringen."""
    assert anchors.verweise_aus("x.py", '        "a.md#CGT-x"\n') == [("CGT-x", 1, "a.md")]


def test_verweis_anzahl_zaehlt_auch_python():
    """Die Erfolgsmeldung nennt diese Zahl. Zählte sie nur Markdown, meldete der Prüfer eine
    Vollständigkeit, die er nicht hat – dieselbe Täuschung, an der der `.claude/**`-Fleck so
    lange unentdeckt blieb. Aufgefallen ist er nur, weil jemand die Summe nachgerechnet hat."""
    bestand = dict(BESTAND)
    bestand["h.py"] = 'm = "docs/guidelines/typescript.md#CGT-result"\n'
    assert anchors.verweis_anzahl(bestand) == anchors.verweis_anzahl(BESTAND) + 1


def test_klartext_hinter_backtick_zaehlt():
    """Docstrings setzen Pfade gewohnheitsmäßig in Backticks. Bliebe diese Form ungeprüft,
    entstünde der blinde Fleck ausgerechnet dort, wo die Werkzeuge ihre Regeln erklären."""
    assert anchors.verweise_aus("x.py", "Regel (`a.md#CGT-x`): …\n") == [("CGT-x", 1, "a.md")]


def test_klartext_in_klammern_zaehlt():
    """Der häufigste Fall in Quellcode-Kommentaren: `// Domänentyp (pfad.md#ANKER, Ebene 2)`.
    Ein Muster, das die öffnende Klammer pauschal ausschließt, um Markdown-Links zu meiden,
    übersieht sie alle – in S124 blieben so 9 von 10 umgestellten Code-Verweisen ungezählt,
    während `check` grün meldete."""
    assert anchors.verweise_aus("X.cs", "// Domänentyp (a.md#CGT-x, Ebene 2)\n") == [
        ("CGT-x", 1, "a.md")]


def test_markdown_link_in_py_zaehlt_nicht():
    assert anchors.verweise_aus("x.py", "Beispiel: [CGT-x](a.md#CGT-x)\n") == []


def test_klartext_in_md_zaehlt_nicht():
    """Gegenprobe: In Markdown bleibt der Link die einzige Form – sonst wäre die
    Klickbarkeit optional, und sie ist der Grund für dieses Format."""
    assert anchors.verweise_aus("x.md", "Siehe a.md#CGT-x\n") == []


def test_py_definiert_keine_anker():
    """`<a id=…>` am Zeilenanfang eines Python-Strings ist Testmaterial, kein Abschnitt.
    Ohne diese Regel meldete der Prüfer die Fixtures dieser Datei hier als Dubletten der
    echten Guideline – das Werkzeug bräche an seinen eigenen Tests."""
    bestand = dict(BESTAND)
    bestand["t.py"] = 'G = """\n<a id="CGT-result"></a>\n## T\n"""\n'
    assert anchors.doppelte(bestand) == []


# --- Zwei Stufen: ganz ausgeschlossen vs. musterweise ausgenommen -------------

def test_generierte_datei_wird_nicht_geprueft():
    """`package-lock.json` und die EF-Migrationen schreibt ein Werkzeug, kein Mensch.
    Ein Verweis kann dort nicht entstehen, und die Datei stellt allein 13.012 der 22.723
    Zahl-Vorkommen des Repos (S124-Inventur) – sie bei jedem Edit mitzulesen ist reine Last."""
    assert not anchors.wird_geprueft("Client/package-lock.json")
    assert not anchors.wird_geprueft(
        "Infrastructure/Migrations/20260817125333_InitialCreate.Designer.cs")


def test_laufzeit_artefakt_wird_nicht_geprueft():
    """Von der Werkzeugkette geschrieben, gitignored, kein Inhalt zum Pflegen."""
    assert not anchors.wird_geprueft(".claude/RESUME.md")
    assert not anchors.wird_geprueft(".claude/session-types.json")


def test_gewoehnliche_testdatei_wird_geprueft():
    """Der blinde Fleck, den S124 fand: `test_primitives.py` trug einen toten `§2`-Verweis,
    entdeckt nur durch einen zufälligen grep. Eine Testdatei ist kein Freibrief – nur die
    Tests der Prüfwerkzeuge selbst brauchen eine Ausnahme, und die ist musterweise."""
    assert anchors.wird_geprueft("tests/test_primitives.py")


def test_pruefwerkzeug_test_ist_nur_musterweise_ausgenommen():
    """Zweite Stufe: Die Datei wird geprüft, aber die Muster, die dort Eingabedatum sind,
    zählen nicht als Befund. Ein `[Schritt 5](#ANKER)` in test_ordinale.py IST der Testfall."""
    assert anchors.wird_geprueft("tests/test_ordinale.py")
    assert "ordinal" in anchors.ausnahmen_fuer("tests/test_ordinale.py")
    assert "verweis" in anchors.ausnahmen_fuer("tests/test_anchors.py")


def test_gewoehnliche_datei_hat_keine_ausnahme():
    assert anchors.ausnahmen_fuer("docs/process/nfr.md") == frozenset()


def test_unbekannter_dateityp_wird_geprueft(tmp_path):
    """Kein Dateityp fällt still durchs Raster. Eine Allowlist erzeugt genau den Fehler,
    der in S124 zweimal auftrat: `.claude/**` ausgeschlossen, `.cs`/`.ts` nie aufgenommen –
    beide Male meldete der Prüfer grün für einen Bereich, den er nie geöffnet hatte."""
    (tmp_path / "pipeline.yml").write_text('doc: "a.md#CGT-x"\n', encoding="utf-8")
    assert "pipeline.yml" in anchors.lies_bestand(tmp_path)


def test_binaerdatei_wird_uebersprungen(tmp_path):
    """Ein NUL-Byte im Kopf heißt: keine Textdatei. Als Netz gegen Formate, die keine
    Ordner-Regel kennt – sie zu 'lesen' ergäbe Zeichensalat und kostet nur Zeit."""
    (tmp_path / "logo.dat").write_bytes(b"\x89PNG\x00\x00 a.md#CGT-x")
    assert anchors.lies_bestand(tmp_path) == {}


def test_generate_werden_uebersprungen(tmp_path):
    """`__pycache__` und Report-Ausgaben sind Erzeugnisse, keine Quellen."""
    for ordner in ("__pycache__", "reports"):
        (tmp_path / ordner).mkdir()
        (tmp_path / ordner / "x.md").write_text("Siehe [X](a.md#CGT-x)\n", encoding="utf-8")
    assert anchors.lies_bestand(tmp_path) == {}


def test_fixture_der_eigenen_tests_zaehlt_nicht_als_verweis(monkeypatch):
    """Ein Anker-String in den Tests DIESES Werkzeugs ist Eingabedatum – ohne die Ausnahme
    läse das Werkzeug seine eigenen Fixtures als Verweise und meldete sie als tot.

    Seit S124 gilt sie musterweise statt für die ganze Datei. Vorher fiel jede `test_*.py`
    komplett heraus, und in einer davon lag ein toter Verweis, den erst ein zufälliger
    grep fand – die Datei war nie geprüft worden."""
    monkeypatch.setitem(anchors.MUSTER_AUSNAHMEN, "tests/test_x.py", frozenset({"verweis"}))
    assert anchors.verweise_aus("tests/test_x.py", 'm = "a.md#CGT-x"\n') == []
    assert anchors.verweise_aus("tests/test_y.py", 'm = "a.md#CGT-x"\n')


def test_py_wird_gescannt(tmp_path):
    (tmp_path / "prozesscode" / "hooks").mkdir(parents=True)
    (tmp_path / "prozesscode" / "hooks" / "h.py").write_text("x = 1\n", encoding="utf-8")
    assert "prozesscode/hooks/h.py" in anchors.lies_bestand(tmp_path)


def test_toter_klartext_verweis_wird_gemeldet():
    kaputt = dict(BESTAND)
    kaputt["h.py"] = 'msg = "Siehe docs/guidelines/typescript.md#CGT-fehlt"\n'
    assert ("h.py", 1, "CGT-fehlt") in anchors.tote_verweise(kaputt)


def test_klartext_pfad_wird_repo_relativ_gelesen():
    """Ein Pfad in einer Hook-Meldung erscheint im Terminal, dessen Arbeitsverzeichnis das
    Repo-Root ist – er ist repo-relativ, nicht relativ zur Quelldatei. Läse man ihn wie in
    Markdown, meldete der Prüfer jede Meldung aus `prozesscode/hooks/checks/` als falschen Pfad."""
    bestand = dict(BESTAND)
    bestand["prozesscode/hooks/checks/c.py"] = 'm = "docs/guidelines/typescript.md#CGT-result"\n'
    assert anchors.falsche_pfade(bestand) == []


def test_falscher_klartext_pfad_wird_gemeldet():
    """Gegenprobe – der belegte Fall `rop.py`: Der Anker existiert, aber nicht dort."""
    bestand = dict(BESTAND)
    bestand["prozesscode/hooks/checks/c.py"] = 'm = "docs/process/nfr.md#CGT-result"\n'
    assert anchors.falsche_pfade(bestand) == [
        ("prozesscode/hooks/checks/c.py", 1, "CGT-result",
         "docs/process/nfr.md", "docs/guidelines/typescript.md")]


def test_verwaiste_findet_verweis_aus_py():
    """Rückwärts: Auch ein Anker, auf den nur eine Hook-Meldung zeigt, darf nicht still
    verschwinden – sonst verweist der Hook den Entwickler ins Leere."""
    ohne = GUIDELINE.replace('<a id="CGT-result"></a>\n', "")
    verwaist = anchors.verwaiste(GUIDELINE, ohne,
                                 {"h.py": 'm = "docs/guidelines/typescript.md#CGT-result"\n'})
    assert verwaist == [("CGT-result", [("h.py", 1)])]


# --- Format ------------------------------------------------------------------
@pytest.mark.parametrize("roh", ["CGT-result", "IMP-architektur", "E2E-treue", "CGT-a1"])
def test_gueltige_anker(roh):
    assert anchors.ist_anker(roh)


@pytest.mark.parametrize("roh", ["cgt-result", "CGT", "CGT-", "CGT-Result", "TD-S089-1",
                                 "OBS-S124-1", "ADR-S112-5"])
def test_ungueltige_anker(roh):
    """Tracker-IDs sind bewusst KEINE Anker – sie haben eigene Prüfer, und ein gemeinsames
    Muster würde beide Mechanismen aneinanderbinden."""
    assert not anchors.ist_anker(roh)


def test_der_mutanten_baum_wird_nicht_gescannt(tmp_path):
    """`mutants/` ist eine vollständige Repo-Kopie, die mutmut anlegt.

    Ohne diesen Ausschluss zählt jede Anker-Prüfung nach einem Mutationslauf die Kopie mit:
    real gemessen 386 „defekte" Verweise und 129 Ordinal-Funde, die es im Bestand nicht
    gibt. Der Gate-Befund wäre dann eine Aussage über ein Build-Artefakt.
    """
    (tmp_path / "mutants" / "docs").mkdir(parents=True)
    (tmp_path / "mutants" / "docs" / "kopie.md").write_text(
        "Siehe [CGT-gibt-es-nicht](x.md#CGT-gibt-es-nicht)\n", encoding="utf-8")
    (tmp_path / "echt.md").write_text("# echt\n", encoding="utf-8")

    bestand = anchors.lies_bestand(tmp_path)
    assert "echt.md" in bestand
    assert not any(p.startswith("mutants/") for p in bestand), sorted(bestand)
