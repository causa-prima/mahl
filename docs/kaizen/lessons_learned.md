# Lessons Learned

<!--
Format: Einträge pro Session gruppiert. Ein Bullet pro Erkenntnis.
Pflicht: Jede Session endet mit mindestens einem Eintrag – "Keine Learnings" nur mit expliziter Begründung.
Technische Schuld gehört in AGENT_MEMORY.md, nicht hierher.

Eintrag-Format:
  ## Session NNN – YYYY-MM-DD

  - **[SCHWERE] [KATEGORIE] [KONTEXT] Kurztitel**
    Was: Ein Satz – was ist passiert?
    Warum: Ein Satz – Ursache.
    Regel: Die destillierte Erkenntnis (imperative Form).

Schwere:    KRITISCH | HOCH | MITTEL | GERING
Kategorien: PROZESS | AGENT | QUALITÄT | TOOLING
Kontext:    TDD | C#-Code | TS-Code | Review | Agent-Prompt | Skill-Nutzung |
            Session-Struktur | Tooling | Gherkin | Doku | Sonstiges

Alle drei Tags sind Pflicht. Definitionen und Reaktionsregeln: docs/kaizen/PROCESS.md

Nach der Sitzung prüfen: Gehört ein Eintrag in principles.md oder countermeasures.md?
KRITISCH-Findings werden sofort behandelt (Andon-Cord) – hier trotzdem dokumentieren.
-->

> **Format-Referenz:** `docs/kaizen/PROCESS.md`
> **Archiv (Sessions 001–046, altes Format):** `docs/kaizen/archive/session_001_to_046.md`

---

## Session 052 – 2026-04-10

- **[MITTEL] [PROZESS] [Doku] Fenced Code Block für copy-paste-kritische Texte**
  Was: Trigger-Text in closing-session mit Backtick-Escaping (`\`kaizen\``) formuliert – wäre literal kopiert worden.
  Warum: In Markdown-Anweisungen an Agenten müssen Texte, die exakt kopiert werden sollen, in Fenced Code Blocks stehen (nicht als Inline-Code mit Escaping), weil der Agent die rohe Markdown-Syntax sieht.
  Regel: Exakt-zu-kopierenden Text immer in ``` einschließen, nie mit Backtick-Escaping in Fließtext.

- **[MITTEL] [PROZESS] [Review] Review-Scope verhaltensbasiert, nicht größenbasiert**
  Was: review-code Scope-Kriterium war Dateianzahl (<3 = KLEIN) – lädt falsche Agenten bei kleinen aber business-kritischen Änderungen.
  Warum: Dateianzahl korreliert nicht mit Risiko. Drei neugeschriebene Dateien mit Domain-Logik sind GROSS.
  Regel: Scope anhand der Art der Änderung bestimmen (Verhaltensänderung? Domain-Layer betroffen?), nicht anhand der Anzahl geänderter Dateien.

- **[GERING] [TOOLING] [Doku] Retro-Script: Archivdateien ohne Format-Konvention ausschließen**
  Was: `session_001_to_046.legacy` wurde von retro_report.py als `.md` gelesen und fälschlich als "12 Sessions" gezählt.
  Warum: Das Script las alle `*.md`-Dateien im Archiv, unabhängig vom Inhalt.
  Regel: Unstrukturierte Archivdateien mit `.legacy`-Extension benennen; Script prüft nur `*.md`.

## Session 051 – 2026-04-10

- **[MITTEL] [QUALITÄT] [Gherkin] Then-Assertion war trivial wahr – nicht erkannt**
  Was: `And die Liste ist alphabetisch nach Name sortiert` in "Neue Zutat anlegen" prüft mit einem einzigen Listeneintrag nichts Sinnvolles – Assertion ist immer wahr; erst im Review als HIGH entdeckt.
  Warum: Nicht geprüft ob das Then mit dem gewählten Given überhaupt falsifizierbar ist.
  Regel: Für jede Then-Aussage prüfen: Kann das Given einen Gegenfall produzieren? Falls nein, ist die Assertion trivial wahr und testet nichts.

- **[MITTEL] [QUALITÄT] [Gherkin] Given beschrieb nicht vollständig den für Then nötigen Ausgangszustand**
  Was: Then `die Zutaten-Liste ist leer` nach Löschen, obwohl Given nur `"Mehl" existiert` – nicht ausgeschlossen dass weitere Zutaten vorhanden sind; führte zu zwei User-Ablehnungen.
  Warum: Then formuliert ohne zu prüfen ob das Given allein die Vorbedingung vollständig beschreibt.
  Regel: Vor jedem Then prüfen: Beschreibt das Given den Ausgangszustand vollständig genug um diese Aussage zu rechtfertigen?

- **[MITTEL] [PROZESS] [Gherkin] Feature-Scope nicht gegen US-Akzeptanzkriterien abgeglichen**
  Was: Bestehendes Feature-File deckte nur Create+Delete ab; US fordert CRUD+Tags – Abweichung nicht in Schritt 0.B erkannt, erst im Review als HIGH entdeckt.
  Warum: In Schritt 0.B nur bestehende Szenarien gelesen, nicht Feature-Scope aktiv gegen alle Operationen der US-AKs geprüft.
  Regel: In Schritt 0.B des gherkin-workshops: Feature-Scope explizit gegen alle Operationen aus den Akzeptanzkriterien abgleichen; Lücken sofort als Scope-Entscheidung markieren.

- **[GERING] [QUALITÄT] [Gherkin] Logisch widersprüchliche Given-Steps**
  Was: `Given es sind keine Zutaten vorhanden` + `And die Zutat "Mehl" existiert` – logischer Widerspruch, der User hat abgelehnt.
  Warum: Gedacht als "erst leeren, dann hinzufügen" – aber Gherkin-Semantik: alle Given-Schritte gelten gleichzeitig.
  Regel: Given-Schritte in Szenarien auf logische Widersprüche prüfen – sie gelten gleichzeitig, nicht sequentiell.

---

## Session 050 – 2026-04-09

- **[MITTEL] [AGENT] [Review] Fix-Vorschlag formuliert ohne Mechanismus vorab zu prüfen**
  Was: Bei F3 (Runde 6) schlug ich vor "beides hätte ein Archiv hinterlassen müssen" – KRITISCH/HOCH-Findings schreiben aber sofort in countermeasures.md, ohne Retro oder Archiv auszulösen.
  Warum: Die Invariante klang plausibel, wurde aber nicht gegen PROCESS.md verifiziert.
  Regel: Vor einem Fix-Vorschlag der eine Invariante behauptet, die Invariante gegen die tatsächliche Prozessdefinition prüfen.

---

## Session 049 – 2026-04-08

- **[MITTEL] [PROZESS] [Review] Review-Agent-Output vor Umsetzung nicht auf Sachkorrektheit geprüft**
  Was: Mehrere Reviewer-Findings wurden zunächst akzeptiert, die bei näherer Prüfung auf falschen Prämissen basierten (M1: mv ist nicht irreversibel; H3: Eskalationslogik war kein Widerspruch).
  Warum: Findings wurden auf Plausibilität bewertet, nicht auf Verifikation gegen den tatsächlichen Inhalt der Dateien.
  Regel: Vor der Umsetzung jedes Reviewer-Findings den beanstandeten Sachverhalt direkt im Dokument prüfen – nicht nur die Begründung des Reviewers lesen.

- **[MITTEL] [PROZESS] [Doku] Inkonsistenz zwischen zwei Skills nicht beim Schreiben erkannt**
  Was: closing-session schrieb "Score ≤ 0", kaizen erwartete "Jenga-Score ≤ 0" – Match schlug still fehl.
  Warum: Zwei Skills die aufeinander verweisen wurden nie gegeneinander abgeglichen.
  Regel: Wenn ein Skill einen exakten String aus einem anderen Skill matcht, den Quell-Skill lesen und den genauen Text übernehmen.

- **[MITTEL] [PROZESS] [Skill-Nutzung] Nummerierungsfehler beim manuellen Umnummerieren von Schritt-Listen**
  Was: Schritt 5 in kaizen-Skill hatte nach Edit einen Sprung von 2 auf 4.
  Warum: Beim Einfügen eines neuen Schritts nur die neuen Nummern gesetzt, alte Folgeschritte vergessen.
  Regel: Nach dem Einfügen eines Schritts in eine nummerierte Liste die gesamte Sequenz einmal durchlesen.

- **[GERING] [PROZESS] [Doku] principles.md referenzierte nicht-existierenden Hook-Namen**
  Was: Kommentar verwies auf `.claude/hooks/startup.py` – Hook heißt tatsächlich `session-start.sh`.
  Warum: Kommentar wurde beim Erstellen des Hooks nicht synchronisiert.
  Regel: Beim Einrichten eines Hooks den referenzierten Dateinamen in allen Kommentaren/Docs anpassen.

## Session 048 – 2026-04-07

- **[MITTEL] [PROZESS] [Tooling] Edit-Tool ohne vorheriges Read aufgerufen**
  Was: Mehrere Edit-Aufrufe schlugen fehl, weil die Dateien in dieser Konversation nicht vorher gelesen wurden.
  Warum: Parallele Edits vorbereitet ohne Read-Schritt einzuplanen.
  Regel: Vor jedem Edit sicherstellen, dass die Datei in dieser Konversation bereits gelesen wurde.

- **[MITTEL] [PROZESS] [Skill-Nutzung] Skill-Schritt-Reihenfolge nicht auf Abhängigkeiten geprüft**
  Was: closing-session Skill hatte AGENT_MEMORY vor Jenga-Score – musste nach User-Hinweis korrigiert werden.
  Warum: Abhängigkeit (Jenga-Score als Input für AGENT_MEMORY) beim Skill-Design nicht explizit bedacht.
  Regel: Bei Skill-Design mit Task-Reihenfolge Datenflusss-Abhängigkeiten explizit prüfen bevor Reihenfolge festgelegt wird.
