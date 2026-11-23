"""check-test-spec-ref: Jeder neue Komponenten-/Integrationstest nennt die Spec, die ihn treibt.

CM-S070-1, Review-Fix-Pfad: In einem Review-Fix entstanden Tests für Verhalten, das kein
Szenario-Beispiel nannte. Der Freigabe-Anker sieht das nicht – ein Review-Fix bekommt
einen eigenen. Der Hook setzt deshalb an der Quelle an: Ein neuer Testfall trägt `// Szenario:`
(bei einem Szenariogrundriss zusätzlich `// Beispiel:`) oder, ohne US-Tag, einen ADR-Verweis.
Er prüft, DASS eine existierende Spec genannt ist – ob sie den Fall inhaltlich deckt, bleibt
ein Urteil des Test-Reviews.
"""
import textwrap
from importlib import import_module

import pytest

from prozesscode.hooks.checks import guard_log

hook = import_module("prozesscode.hooks.check-test-spec-ref")

FEATURE = textwrap.dedent("""\
    @US-602
    Feature: Rezepte erfassen

      # Erklärender Kommentar im Kopf, wie im Bestand.

      # @run-6 · Formular·Abbrechen · Frontend-only
      @US-602-happy-path
      Scenario: Abbrechen ohne Eingaben führt ohne Nachfrage zur Rezept-Liste
        When ich auf "Abbrechen" klicke
        Then sehe ich die Rezept-Liste

      # @run-6 · Formular·Abbrechen · Frontend-only
      @US-602-happy-path
      Scenario Outline: Abbrechen mit Eingaben fragt nach – Verwerfen führt zur Rezept-Liste
        When ich <Eingabe>
        Then sehe ich die Nachfrage "Eingaben verwerfen?"

        Examples:
          | Eingabe                           |
          | "Pfannkuchen" als Titel eingebe   |
          | "Salz" als Zutaten eingebe        |

      @US-602-error
      Scenario Outline: Ungültiger Titel
        When ich <Titel> als Titel eingebe
        Then sehe ich am Titel die Meldung <Meldung>

        Examples:
          | Titel   | Meldung                     |
          | ""      | "Bitte einen Titel angeben" |
          | "   "   | "Bitte einen Titel angeben" |
    """)
ADRS = {"ADR-S106-3", "ADR-S135-1"}
TS = "Client/src/pages/RecipesPage.test.tsx"
CS = "Server.Tests/Endpoints/RecipeEndpointsTests.cs"

BESTAND_TS = textwrap.dedent("""\
    describe('Rezepte', () => {
      it('US602_HappyPath_Bestand_OhneKommentar', async () => {
        // Given
      })
    })
    """)


GEGLIEDERT = "    // Given\n    // When\n    // Then\n"


def _neu_ts(kommentar: str, name: str = "US602_HappyPath_Neu", rumpf: str = GEGLIEDERT) -> str:
    """Bestand plus ein neuer Testfall mit dem gegebenen Kommentarblock darüber."""
    block = textwrap.indent(textwrap.dedent(kommentar), "  ")
    ohne_schluss = BESTAND_TS.removesuffix("})\n")  # schließendes describe abnehmen …
    return ohne_schluss + f"\n{block}  it('{name}', async () => {{\n{rumpf}  }})\n}})\n"  # … und wieder dran


def _verstoesse(post: str, pre: str = BESTAND_TS, pfad: str = TS) -> list[str]:
    return hook.verstoesse(pfad, pre, post, [FEATURE], ADRS)


# --- Form 1: einfaches Szenario ----------------------------------------------------
def test_neuer_test_mit_existierendem_szenario_ist_ok():
    # Given
    post = _neu_ts("// Szenario: Abbrechen ohne Eingaben führt ohne Nachfrage zur Rezept-Liste\n")
    # When / Then
    assert _verstoesse(post) == []


def test_neuer_test_ohne_jeden_verweis_wird_abgewiesen():
    # Given
    post = _neu_ts("// nur ein Erklärkommentar\n")
    # When
    meldungen = _verstoesse(post)
    # Then
    assert meldungen == [hook.OHNE_VERWEIS.format(test="US602_HappyPath_Neu")]


def test_verweis_im_rumpf_statt_darueber_nennt_die_geforderte_position():
    # Given: der Szenario-Verweis steht im Rumpf statt als Kommentarzeile über dem Test
    post = _neu_ts("// nur ein Erklärkommentar\n",
                   rumpf="    // Szenario: Abbrechen ohne Eingaben führt ohne Nachfrage zur Rezept-Liste\n"
                         + GEGLIEDERT)
    # When
    meldungen = _verstoesse(post)
    # Then: abgewiesen, und die Meldung sagt, wo der Verweis stehen muss
    assert len(meldungen) == 1
    assert "eigene Kommentarzeile direkt über dem Test" in meldungen[0]


def test_szenario_titel_den_es_nicht_gibt_wird_abgewiesen():
    # Given
    post = _neu_ts("// Szenario: Abbrechen mit Leerraum\n")
    # When / Then
    assert _verstoesse(post) == [hook.SZENARIO_FEHLT.format(test="US602_HappyPath_Neu",
                                                             titel="Abbrechen mit Leerraum")]


# --- Form 2: Szenariogrundriss ------------------------------------------------------
GRUNDRISS = "// Szenario: Abbrechen mit Eingaben fragt nach – Verwerfen führt zur Rezept-Liste\n"


def test_grundriss_ohne_beispielzeile_wird_abgewiesen():
    # Given
    post = _neu_ts(GRUNDRISS)
    # When / Then
    assert _verstoesse(post) == [hook.BEISPIEL_FEHLT.format(
        test="US602_HappyPath_Neu",
        titel="Abbrechen mit Eingaben fragt nach – Verwerfen führt zur Rezept-Liste")]


def test_grundriss_mit_existierender_beispielzeile_ist_ok():
    post = _neu_ts(GRUNDRISS + '// Beispiel: "Salz" als Zutaten eingebe\n')
    assert _verstoesse(post) == []


def test_beispielzeile_die_unter_dem_grundriss_fehlt_wird_abgewiesen():
    # Given – Text nur im zweiten Schritt steht in keiner Zeile der Tabelle
    post = _neu_ts(GRUNDRISS + '// Beispiel: "Teig rühren." als zweiten Schritt eingebe\n')
    # When / Then
    assert _verstoesse(post) == [hook.BEISPIEL_UNBEKANNT.format(
        test="US602_HappyPath_Neu", beispiel='"Teig rühren." als zweiten Schritt eingebe',
        titel="Abbrechen mit Eingaben fragt nach – Verwerfen führt zur Rezept-Liste")]


def test_kopfzeile_der_beispieltabelle_ist_keine_beispielzeile():
    post = _neu_ts(GRUNDRISS + "// Beispiel: Eingabe\n")
    assert len(_verstoesse(post)) == 1


def test_beispielzeile_eines_anderen_grundrisses_zaehlt_nicht():
    post = _neu_ts(GRUNDRISS + '// Beispiel: "" | "Bitte einen Titel angeben"\n')
    assert len(_verstoesse(post)) == 1


def test_mehrspaltige_beispielzeile_wird_mit_trenner_erkannt_auch_mit_aeusseren_strichen():
    for zeile in ('"   " | "Bitte einen Titel angeben"', '| "   "   |  "Bitte einen Titel angeben" |'):
        post = _neu_ts('// Szenario: Ungültiger Titel\n' f'// Beispiel: {zeile}\n')
        assert _verstoesse(post) == [], zeile


def test_erste_beispielzeile_nach_der_kopfzeile_zaehlt():
    post = _neu_ts(GRUNDRISS + '// Beispiel: "Pfannkuchen" als Titel eingebe\n')
    assert _verstoesse(post) == []


def test_mehrspaltige_zeile_ohne_trenner_wird_abgewiesen():
    """Zellen sind mit `|` getrennt – dieselben Wörter ohne Trenner sind keine Zeile der Tabelle."""
    post = _neu_ts('// Szenario: Ungültiger Titel\n// Beispiel: "" "Bitte einen Titel angeben"\n')
    assert len(_verstoesse(post)) == 1


def test_jeder_von_mehreren_szenario_verweisen_wird_geprueft_in_lesereihenfolge():
    # Given – ungültig, gültig, ungültig: kein Verweis darf die Prüfung der folgenden beenden
    post = _neu_ts("// Szenario: Gibt es nicht A\n"
                   "// Szenario: Abbrechen ohne Eingaben führt ohne Nachfrage zur Rezept-Liste\n"
                   "// Szenario: Gibt es nicht B\n")
    # When / Then
    assert _verstoesse(post) == [
        hook.SZENARIO_FEHLT.format(test="US602_HappyPath_Neu", titel="Gibt es nicht A"),
        hook.SZENARIO_FEHLT.format(test="US602_HappyPath_Neu", titel="Gibt es nicht B")]


def test_trenner_ohne_leerzeichen_wird_erkannt():
    post = _neu_ts('// Szenario: Ungültiger Titel\n// Beispiel: ""|"Bitte einen Titel angeben"\n')
    assert _verstoesse(post) == []


def test_alle_beispiele_deckt_einen_parametrisierten_test():
    post = _neu_ts(GRUNDRISS + "// Beispiel: alle\n")
    assert _verstoesse(post) == []


# --- Form 3: Querschnitt ohne US-Tag -------------------------------------------------
def test_test_ohne_us_tag_mit_existierender_adr_ist_ok():
    post = _neu_ts("// ADR-S106-3: Reihenfolge-Pin, den kein Mutant fängt\n", name="FocusOrder_Pin")
    assert _verstoesse(post) == []


def test_adr_verweis_auf_eine_unbekannte_adr_wird_abgewiesen():
    post = _neu_ts("// ADR-S999-9: gibt es nicht\n", name="FocusOrder_Pin")
    assert _verstoesse(post) == [hook.ADR_UNBEKANNT.format(test="FocusOrder_Pin", adr="ADR-S999-9")]


def test_us_getaggter_test_mit_nur_adr_verweis_wird_abgewiesen():
    """Diagnose c (ADR-Kommentar) trägt keinen US-Tag – sonst verdeckt der Tag die Lücke."""
    post = _neu_ts("// ADR-S135-1: Normalisierung\n", name="US602_EdgeCase_NurNel")
    assert _verstoesse(post) == [hook.US_TAG_OHNE_SZENARIO.format(test="US602_EdgeCase_NurNel")]


# --- Bestand und Abgrenzung ------------------------------------------------------------
def test_bestehender_test_ohne_verweis_bleibt_ungeprueft():
    """Nur neue Testfälle – die 91 Bestandstests ohne Verweis blockieren keinen Edit."""
    post = BESTAND_TS.replace("// Given", "// Given – nur umformuliert")
    assert _verstoesse(post) == []


def test_beschreibende_suite_ist_kein_testfall():
    post = BESTAND_TS + "describe('Neue Gruppe', () => {})\n"
    assert _verstoesse(post) == []


def test_verweis_ueber_einer_suite_gilt_nicht_fuer_den_test_darin():
    """Der Kommentarblock endet an der ersten Code-Zeile – ein `describe` ist Code."""
    post = BESTAND_TS[:-3] + (
        "\n  // Szenario: Abbrechen ohne Eingaben führt ohne Nachfrage zur Rezept-Liste\n"
        "  describe('Gruppe', () => {\n    it('US602_HappyPath_Neu', async () => {\n    })\n  })\n})\n")
    assert len(_verstoesse(post)) == 1


# --- C# (xunit) ------------------------------------------------------------------------
BESTAND_CS = textwrap.dedent("""\
    public class RecipeEndpointsTests
    {
        [Fact]
        public async Task US602_HappyPath_Bestand()
        {
        }
    }
    """)


def test_csharp_verweis_ueber_den_attributen_wird_gefunden():
    # Given – Kommentar über [Theory] und [InlineData], wie im Bestand üblich
    neu = ("\n    // Szenario: Abbrechen ohne Eingaben führt ohne Nachfrage zur Rezept-Liste\n"
           "    [Theory]\n    [InlineData(1)]\n    public async Task US602_HappyPath_Neu(int x)\n"
           "    {\n    }\n}\n")
    post = BESTAND_CS[:-2] + neu
    # When / Then
    assert _verstoesse(post, pre=BESTAND_CS, pfad=CS) == []


def test_csharp_verweis_ueber_weiterem_attribut_und_leerzeile_wird_gefunden():
    # Given – [Trait] vor [Fact], Leerzeile zwischen Kommentar und Attributen
    neu = ("\n    // Szenario: Abbrechen ohne Eingaben führt ohne Nachfrage zur Rezept-Liste\n\n"
           '    [Trait("Art", "Integration")]\n    [Fact]\n    public void US602_HappyPath_Neu()\n'
           "    {\n    }\n}\n")
    # When / Then
    assert _verstoesse(BESTAND_CS[:-2] + neu, pre=BESTAND_CS, pfad=CS) == []


def test_csharp_neuer_test_ohne_verweis_wird_abgewiesen():
    post = BESTAND_CS[:-2] + "\n    [Fact]\n    public void US602_Error_Neu()\n    {\n    }\n}\n"
    assert _verstoesse(post, pre=BESTAND_CS, pfad=CS) == [
        hook.OHNE_VERWEIS.format(test="US602_Error_Neu")]


# --- Zuständigkeit ------------------------------------------------------------------------
@pytest.mark.parametrize("pfad, zustaendig", [
    ("Client/src/pages/RecipesPage.test.tsx", True),
    ("/home/x/repo/Client/src/services/recipes.test.ts", True),
    ("Server.Tests/Endpoints/RecipeEndpointsTests.cs", True),
    ("Client/e2e/recipes.spec.ts", False),          # E2E: check-e2e-scenario-ref
    ("Client/src/zz.probe.test.tsx", False),        # Wegwerf-Probe: qa-check bricht ab, solange sie existiert
    ("Client/src/services/x.probe.test.ts", False),
    ("Client/src/probe.test.tsx", True),            # nur die Endung `.probe.test.*` zählt, nicht der Name
    ("Client/src/pages/RecipesPage.tsx", False),
    ("Server/Domain/Recipe.cs", False),
    ("tests/test_retro_report.py", False),
])
def test_zustaendig_nur_fuer_komponenten_und_integrationstests(pfad, zustaendig):
    assert hook.betrifft(pfad) is zustaendig


# --- Aufrufpfad: über den Dispatcher wie Claude Code ------------------------------------------
@pytest.mark.aufrufpfad("check-test-spec-ref")
def test_dispatcher_weist_neuen_test_ohne_verweis_ab(tmp_path, monkeypatch):
    # Given – echte Verzeichnisform, Feature und ADR-Datei im tmp-Repo
    features = tmp_path / "features"
    features.mkdir()
    (features / "recipes.feature").write_text(FEATURE, encoding="utf-8")
    adr = tmp_path / "adr.md"
    adr.write_text("### ADR-S106-3: Querschnitts-Tests\n", encoding="utf-8")
    monkeypatch.setattr(hook, "_FEATURES_DIR", features)
    monkeypatch.setattr(hook, "_ADR_FILE", adr)
    datei = tmp_path / "Client" / "src" / "pages" / "X.test.tsx"
    datei.parent.mkdir(parents=True)
    datei.write_text(BESTAND_TS, encoding="utf-8")
    daten = {"tool_name": "Write", "tool_input": {"file_path": str(datei),
                                                  "content": _neu_ts("// kein Verweis\n")}}
    # When – Einstieg wie im Dispatcher (Registrierung prüft test_dispatch_edit_write)
    grund = hook.check(daten)
    # Then
    assert grund == (hook.KOPF + "  - " + hook.OHNE_VERWEIS.format(test="US602_HappyPath_Neu")
                     + "\n" + hook.AUSWEG)


# --- Gliederung: // Given, // When, // Then in jedem neuen Testfall ------------------------
# CM-S070-1: Fehlende Given-Kommentare fielen erst im Übergabelauf von qa-check auf – nach der
# Test-Freigabe, sodass die freigegebene Datei noch einmal geändert werden musste. Hier wird
# dieselbe Regel (prozesscode/_test_struktur.py) beim Schreiben des Tests geprüft.
SZENARIO = "// Szenario: Abbrechen ohne Eingaben führt ohne Nachfrage zur Rezept-Liste\n"


def test_neuer_test_ohne_gliederung_nennt_alle_fehlenden_marker():
    # Given
    post = _neu_ts(SZENARIO, rumpf="    expect(1).toBe(1)\n")
    # When
    meldungen = hook.struktur_verstoesse(TS, BESTAND_TS, post)
    # Then
    assert meldungen == [hook.GLIEDERUNG_FEHLT.format(
        test="US602_HappyPath_Neu", fehlt="// Given, // When, // Then")]


def test_neuer_test_ohne_given_nennt_nur_given():
    # Given
    post = _neu_ts(SZENARIO, rumpf="    // When\n    // Then\n")
    # When
    meldungen = hook.struktur_verstoesse(TS, BESTAND_TS, post)
    # Then
    assert meldungen == [hook.GLIEDERUNG_FEHLT.format(test="US602_HappyPath_Neu", fehlt="// Given")]


def test_gegliederter_neuer_test_ist_ok_auch_mit_erklaerung_hinter_dem_marker():
    post = _neu_ts(SZENARIO, rumpf="    // Given: die Zutat Salz\n    // When: ich speichere\n"
                                   "    // Then: sehe ich die Liste\n")
    assert hook.struktur_verstoesse(TS, BESTAND_TS, post) == []


def test_kombinierter_marker_zaehlt_nicht_als_then():
    """Dieselbe Regel wie qa-check: `// When / Then` enthält kein `// Then`."""
    post = _neu_ts(SZENARIO, rumpf="    // Given\n    // When / Then\n")
    assert hook.struktur_verstoesse(TS, BESTAND_TS, post) == [
        hook.GLIEDERUNG_FEHLT.format(test="US602_HappyPath_Neu", fehlt="// Then")]


def test_marker_eines_nachbartests_gilt_nicht_fuer_den_neuen():
    """Geprüft wird der Rumpf des neuen Tests, nicht die Datei: Der Bestandstest trägt
    `// Given`, der neue nicht."""
    post = _neu_ts(SZENARIO, rumpf="    // When\n    // Then\n")
    assert len(hook.struktur_verstoesse(TS, BESTAND_TS, post)) == 1


def test_marker_im_kommentar_ueber_dem_test_zaehlt_nicht():
    """Der Kommentarblock über dem Test trägt die Spec, nicht die Gliederung – ein `// Given`
    direkt über `it(` deckt den Rumpf nicht."""
    post = _neu_ts(SZENARIO + "// Given steht hier, nicht im Rumpf\n",
                   rumpf="    // When\n    // Then\n")
    assert hook.struktur_verstoesse(TS, BESTAND_TS, post) == [
        hook.GLIEDERUNG_FEHLT.format(test="US602_HappyPath_Neu", fehlt="// Given")]


def test_bestandstest_ohne_gliederung_bleibt_ungeprueft():
    """Nur neue Testfälle – der Bestandstest trägt nur `// Given` und blockiert keinen Edit."""
    post = BESTAND_TS.replace("// Given", "// Given – nur umformuliert")
    assert hook.struktur_verstoesse(TS, BESTAND_TS, post) == []


def test_csharp_neuer_test_ohne_gliederung_wird_abgewiesen_mit_gliederung_nicht():
    # Given
    kopf = "\n    " + SZENARIO + "    [Fact]\n    public void US602_HappyPath_Neu()\n    {\n"
    ohne = BESTAND_CS[:-2] + kopf + "    }\n}\n"
    mit = BESTAND_CS[:-2] + kopf + "        // Given\n        // When\n        // Then\n    }\n}\n"
    # When / Then
    assert hook.struktur_verstoesse(CS, BESTAND_CS, ohne) == [hook.GLIEDERUNG_FEHLT.format(
        test="US602_HappyPath_Neu", fehlt="// Given, // When, // Then")]
    assert hook.struktur_verstoesse(CS, BESTAND_CS, mit) == []


def test_csharp_gegliederter_test_mit_mehrzeiliger_signatur_ist_ok():
    """Eine Parameterliste über zwei Zeilen ließ den Rumpf aus dem Testfall fallen –
    die Gliederungs-Marker galten als fehlend, obwohl sie dastanden."""
    # Given
    neu = ("\n    " + SZENARIO + "    [Theory]\n    public async Task US602_HappyPath_Neu(\n"
           "        string a, string b)\n    {\n        // Given\n        // When\n        // Then\n    }\n}\n")
    # When / Then
    assert hook.struktur_verstoesse(CS, BESTAND_CS, BESTAND_CS[:-2] + neu) == []


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """tmp-Repo in echter Verzeichnisform: features/, ADR-Datei, Client/src/."""
    features = tmp_path / "features"
    features.mkdir()
    (features / "recipes.feature").write_text(FEATURE, encoding="utf-8")
    adr = tmp_path / "adr.md"
    adr.write_text("### ADR-S106-3: Querschnitts-Tests\n", encoding="utf-8")
    monkeypatch.setattr(hook, "_FEATURES_DIR", features)
    monkeypatch.setattr(hook, "_ADR_FILE", adr)
    (tmp_path / "Client" / "src").mkdir(parents=True)
    return tmp_path


def _write(pfad, inhalt) -> dict:
    """Write auf eine Datei, die schon mit dem Bestand existiert – sonst wäre auch der neu."""
    if pfad.name.endswith((".test.tsx", ".test.ts")):
        pfad.write_text(BESTAND_TS, encoding="utf-8")
    return {"tool_name": "Write", "tool_input": {"file_path": str(pfad), "content": inhalt}}


def test_einstieg_meldet_mehrere_verstoesse_je_zeile(repo):
    datei = repo / "Client" / "src" / "Y.test.tsx"
    inhalt = (_neu_ts("// kein Verweis\n").removesuffix("})\n")
              + "  it('US602_Error_Zweiter', async () => {\n" + GEGLIEDERT + "  })\n})\n")
    grund = hook.check(_write(datei, inhalt))
    assert grund == (hook.KOPF
                     + "  - " + hook.OHNE_VERWEIS.format(test="US602_HappyPath_Neu") + "\n"
                     + "  - " + hook.OHNE_VERWEIS.format(test="US602_Error_Zweiter") + "\n"
                     + hook.AUSWEG)


def test_einstieg_laesst_eine_wegwerf_probe_ohne_verweis_und_gliederung_durch(repo):
    # Eine Probe prüft Werkzeugverhalten (etwa jsdom), keinen Fall des Laufs – Spec-Verweis und Gliederung
    # wären Zeremonie. Gegenstück zur Lücke: qa-check bricht ab, solange die Probe existiert.
    datei = repo / "Client" / "src" / "zz.probe.test.tsx"
    assert hook.check(_write(datei, _neu_ts("// kein Verweis\n", rumpf=""))) is None


def test_einstieg_meldet_spec_und_gliederung_getrennt_und_protokolliert_die_gliederung(repo):
    """Beide Befunde in einer Meldung (sonst sähe man den zweiten erst nach dem Beheben des
    ersten); die Gliederung zählt im Guard-Protokoll unter eigenem Namen, damit ihr Ausfall
    nicht hinter den Auslösungen der Spec-Prüfung verschwindet."""
    # Given
    datei = repo / "Client" / "src" / "G.test.tsx"
    inhalt = _neu_ts("// kein Verweis\n", rumpf="    // Given\n")
    # When
    grund = hook.check(_write(datei, inhalt))
    # Then
    assert grund == (hook.KOPF + "  - " + hook.OHNE_VERWEIS.format(test="US602_HappyPath_Neu")
                     + "\n" + hook.AUSWEG + "\n"
                     + hook.KOPF_GLIEDERUNG + "  - " + hook.GLIEDERUNG_FEHLT.format(
                         test="US602_HappyPath_Neu", fehlt="// When, // Then")
                     + "\n" + hook.AUSWEG_GLIEDERUNG)
    assert guard_log.zaehlstand() == {hook.GUARD_GLIEDERUNG: 1}


def test_einstieg_nur_gliederung_ohne_spec_kopf_je_test_eine_zeile(repo):
    # Given – zwei neue Tests mit Spec, beide ungegliedert
    datei = repo / "Client" / "src" / "H.test.tsx"
    inhalt = (_neu_ts(SZENARIO, rumpf="").removesuffix("})\n")
              + "  " + SZENARIO + "  it('US602_HappyPath_Zweiter', async () => {\n    // Given\n  })\n})\n")
    # When
    grund = hook.check(_write(datei, inhalt))
    # Then
    assert grund == (hook.KOPF_GLIEDERUNG
                     + "  - " + hook.GLIEDERUNG_FEHLT.format(
                         test="US602_HappyPath_Neu", fehlt="// Given, // When, // Then") + "\n"
                     + "  - " + hook.GLIEDERUNG_FEHLT.format(
                         test="US602_HappyPath_Zweiter", fehlt="// When, // Then") + "\n"
                     + hook.AUSWEG_GLIEDERUNG)


def test_einstieg_prueft_den_adr_verweis_gegen_die_adr_datei(repo):
    datei = repo / "Client" / "src" / "Z.test.tsx"
    assert hook.check(_write(datei, _neu_ts("// ADR-S106-3: Pin\n", name="Pin"))) is None


def test_einstieg_ignoriert_dateien_die_keine_tests_sind(repo):
    """Eine Komponente, in deren Text zufällig `it('…'` steht, ist kein Testfall."""
    datei = repo / "Client" / "src" / "Hilfe.tsx"
    assert hook.check(_write(datei, "it('US602_HappyPath_Text', () => {})\n")) is None


def test_dispatcher_laesst_test_mit_gueltigem_verweis_durch(tmp_path, monkeypatch):
    """Gegenprobe zum Aufrufpfad-Test: derselbe Aufbau mit Verweis → kein Einwand, sonst
    bliebe offen, ob der Hook nur an der fehlenden Feature-Datei scheitert."""
    features = tmp_path / "features"
    features.mkdir()
    (features / "recipes.feature").write_text(FEATURE, encoding="utf-8")
    monkeypatch.setattr(hook, "_FEATURES_DIR", features)
    monkeypatch.setattr(hook, "_ADR_FILE", tmp_path / "adr.md")
    (tmp_path / "adr.md").write_text("", encoding="utf-8")
    datei = tmp_path / "Client" / "src" / "X.test.tsx"
    datei.parent.mkdir(parents=True)
    datei.write_text(BESTAND_TS, encoding="utf-8")
    inhalt = _neu_ts("// Szenario: Abbrechen ohne Eingaben führt ohne Nachfrage zur Rezept-Liste\n")
    assert hook.check({"tool_name": "Write",
                       "tool_input": {"file_path": str(datei), "content": inhalt}}) is None
