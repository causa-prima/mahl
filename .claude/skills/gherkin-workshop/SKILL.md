---
name: gherkin-workshop
description: >
  Systematische Gherkin-Scenario-Entdeckung für eine User Story vor der Implementierung.
  Nutzt drei parallele RE-Techniken (Example Mapping, State-Transition-Analyse,
  Input-Partition-Analyse) und einen unabhängigen Review-Agenten in einem Qualitäts-Loop.
  Produziert vollständige, implementierungsreife Feature-Files.
  Idealerweise vor jeder Story-Implementierung einsetzen – auch wenn bereits
  eine Feature-Datei existiert, prüfe ob sie vollständig ist. Typische Trigger:
  „Gherkin schreiben", „Szenarien fehlen", „Feature-File unvollständig",
  „vor der Implementierung", „Was soll die US abdecken?", „welche Szenarien brauchen wir?",
  User nennt eine US-ID im Kontext von „loslegen", „anfangen" oder „als nächstes" –
  auch ohne explizite Erwähnung von Gherkin.
user-invocable: true
---

# Gherkin-Workshop

Aufruf: `/gherkin-workshop <US-ID>`
Beispiel: `/gherkin-workshop US-904`

---

## Pflicht-Lektüre

Lies vor dem Start:
- `docs/stories/user-stories.md` (Index) → `docs/stories/szenario_N_*.md` – Akzeptanzkriterien der Ziel-US (US-Präfix = Szenario-Nummer, oder `Grep "US-NNN" docs/stories/`)
- `docs/reference/glossary.md` – Ubiquitäre Sprache (nur Begriffe daraus in Szenarien)
- `docs/process/e2e-testing.md` – Gherkin-Konventionen, Tag-Schema, Traceability-Regeln
- `docs/history/adr.md` – Explizite Entwurfsentscheidungen (Constraints für Szenarien)
- `docs/guidelines/coding-guideline-ux.md` – Interaction-Design-Prinzipien (Leer-Zustand, Feedback, Fehlermeldungen)
- `features/` – Bestehende Feature-Files (Pattern-Konsistenz)

---

## Task-Liste anlegen

Lege folgende Tasks mit dem TaskCreate-Tool an:
- „0. Kontext laden"
- „1. Regelentdeckung (Dialog)"
- „2. Parallele Scenario-Entdeckung"
- „3. Synthese"
- „4. Review-Loop"
- „5. Feature-File & Freigabe"
- „6. Szenario-Clustering"

---

## Schritt 0: Kontext laden
→ TaskUpdate „0. Kontext laden": in_progress

Gherkin-Szenarien sind die Spec – sie dürfen nachträglich nicht angepasst werden, um die
Implementierung zu bestätigen. Was hier unvollständig oder ungenau ist, zieht sich durch
alle folgenden Phasen.

Lies die Pflicht-Dateien. Lade bei konkretem Bedarf nach:
- `docs/reference/architecture.md` (bei architektonischen Fragen in Schritt 0.A oder Schritt 1)
- `docs/reference/skeleton-spec.md` / `docs/reference/mvp-spec.md` – nur bei konkretem Bedarf; `adr.md`
  hat Vorrang, weil diese Dateien Entscheidungen und unverifizierte Spec-Details vermischen

**Voraussetzung:** Falls die US-ID in `docs/stories/` nicht gefunden wird oder
`docs/reference/glossary.md` keine relevanten Entitäten enthält: stopp und frage den User –
alle folgenden Schritte bauen auf diesen Grundlagen auf.

Notiere schriftlich:

**A) Story-Kern:**
- Was ist das Geschäftsziel?
- Welche Entitäten sind betroffen? (Name aus docs/reference/glossary.md)
- Welche Zustände kann jede Entität haben? (z.B. Ingredient: Aktiv / Soft-Deleted)
- Welche Operationen definiert die US? (Create / Read-Einzeln / Read-Liste / Update / Delete / Restore / Filter / Sort / andere)
- Welche expliziten Validierungsregeln nennt die US oder adr.md?

**B) Bestandsanalyse:**
Existiert bereits eine Feature-Datei für diese US?
- **JA:** vollständig lesen und notiere:
  - Vorhandene Szenarien und Tags
  - Offensichtliche Lücken
- **NEIN:** Notiere „neu anlegen". Schritt 2 startet mit leerem Pool.

**C) Constraints aus adr.md:**
Welche Entscheidungen betreffen diese US?
(z.B. „Soft-Delete-Pattern", „IDs sind UUIDs", „Sortierung alphabetisch nach Name")

**D) Eingabefelder (für Schritt 2, Agents B + C):**
Welche Felder nimmt jede Operation als Eingabe?
Pro Feld: Name, Typ (String / Zahl / Enum / Referenz), bekannte Constraints (NOT NULL, max. Länge, unique, etc.)

**E) UX-Kontext (für Schritt 2, alle Agents):**
Prüfe für jede Operation aus A) welche UX-Prinzipien zutreffen – notiere je "Relevant" oder "Nicht relevant" mit einem Satz Begründung:
- **Prinzip 7 – Leerer Zustand:** Gibt es Listen oder Ansichten, die leer sein können? Bei "Relevant": Leerer Zustand erfordert Erklärungstext ("Noch keine X angelegt.") + nächste Aktion.
- **Prinzip 3 – Sichtbares Feedback:** Gibt es mutierende Operationen, die auf eine Server-Antwort warten? Bei "Relevant": Lade- und Bestätigungszustand beschreiben.
- **Prinzip 4 – Fehlermeldungen:** Gibt es Fehlerfälle mit UI-Fehlermeldungen? Bei "Relevant": Format "[Was ist falsch]." oder "[Was ist falsch] ([Constraint])." – Platzierung nahe am betroffenen Element.
- **Prinzip 1 – Pflichtfeld-Affordance (Least Surprise):** Hat eine Operation ein Formular mit Pflichtfeldern? Bei "Relevant": Pflichtfelder müssen erkennbar markiert sein – eigenes Szenario (→ Formular-/Dialog-Baseline in der UI-Verhaltens-Checkliste, Schritt 1; Details: UX-Guideline Prinzip 8).

Notiere A–E schriftlich – Schritt 2 übergibt sie verbatim an die Agents.

→ TaskUpdate „0. Kontext laden": completed

---

## Schritt 1: Regelentdeckung (Dialog mit User)
→ TaskUpdate „1. Regelentdeckung (Dialog)": in_progress

Ziel: Domänenwissen erfassen, das nicht aus Dokumenten ableitbar ist – und latente
Anforderungen aufdecken, die noch nicht in der User Story formuliert wurden.

### Wie der Dialog funktioniert

Mehrere Runden sind ausdrücklich erwünscht. Starte mit **Tracer-Bullet-Fragen**: Das sind
die 2–3 Fragen, deren Antworten möglichst viele andere Fragen von selbst beantworten.
Erst wenn diese geklärt sind, folgen spezifischere Fragen in weiteren Runden.

**Warum Tracer Bullets zuerst?** Eine Antwort wie „Name ist case-insensitiv beim
Duplikat-Check" beantwortet gleichzeitig Fragen zu Groß-/Kleinschreibung, Trimming-Logik
und Fehlermeldungstext. Wer zuerst die Fragen mit der höchsten Aufklärungswirkung stellt,
braucht insgesamt weniger Runden.

Faustregel pro Runde: **maximal 3–5 Fragen**, Tracer Bullets idealerweise zuerst.
Keine Fragen stellen zu Dingen, die aus den Docs ableitbar sind – das signalisiert dem User,
dass die Vorbereitung in Schritt 0 übersprungen wurde.

Typische Frage-Kategorien:

| Kategorie | Beispiele |
|-----------|-----------|
| Tracer Bullets | „Welche Felder sind bei welchen Operationen Pflicht?" / „Gibt es Zustände oder Kombinationen, die du für besonders fehleranfällig hältst?" |
| Eindeutigkeit | „Case-sensitiv? Werden Leerzeichen beim Vergleich ignoriert?" |
| Grenzfälle | „Was passiert wenn [Szenario X] und [Zustand Y] gleichzeitig gelten?" |
| Fehlermeldungen | „Spezifische oder generische Meldung für [Fehlerfall]?" |
| Latente Regeln | „Gibt es Regeln, die sich nicht aus den Akzeptanzkriterien ergeben, aber wichtig sind?" |
| Technische Fehler | „Gibt es für diese Operation Fehlerverhalten jenseits der allgemeinen Behandlung (→ adr.md: Querschnittliche Fehlerbehandlung)?" |
| Draft-Saving & Abbrechen | „Wie komplex sind die Eingaben dieses Formulars? Trivial → kein Draft-Saving, Abbrechen ohne Rückfrage (Standard). Nicht-trivial → (1) Soll es einen 'Als Entwurf speichern'-Button geben? Falls ja: Abbrechen bietet Entwurf-Option an. Falls nein: (a) Abbrechen ohne Rückfrage oder (b) Bestätigungsdialog? (→ UX-Guideline Prinzip 5)" |

### grill-me für tiefere Exploration

Aktiviere den `grill-me`-Skill wenn der Dialog keinen neuen Informationsgewinn mehr bringt –
d.h. Antworten bestätigen nur bereits Bekanntes, ohne neue Constraints oder Fälle aufzudecken.
Das passiert typischerweise nach 4–5 Runden, aber das Kriterium ist der sinkende
Erkenntnisgewinn, nicht die Rundenzahl. `grill-me` ist auch sinnvoll wenn: grundlegende
Unklarheiten bestehen, die US nur den Standardfall beschreibt (keine Fehlerfälle, keine
Zustandsübergänge), oder das Domänenmodell unvollständig ist.

Warte nach jeder Runde auf die Antwort des Users – Widersprüche entstehen oft erst durch die
Kombination zweier Antworten. Prüfe nach jeder neuen Antwort alle bisherigen rückwirkend auf
Konsistenz.

Der Dialog ist abgeschlossen, wenn:
- Jede Operation aus Schritt 0.A hat entweder (a) mindestens eine geklärte Validierungsregel
  oder (b) der User hat explizit bestätigt, dass keine gilt – notiere dies als Befund.
  Ohne explizite Bestätigung ist die Abwesenheit einer Antwort kein Abschluss.
- Alle Zustände aus Schritt 0.A haben definiertes Verhalten bei allen Operationen aus 0.A –
  außer einer Operation wurde durch adr.md oder explizite User-Aussage als „nicht
  applicable" markiert
- Keine offenen Widersprüche bestehen – prüfe: Widerspricht Antwort X der Antwort Y
  zu derselben Entität / Operation / Zustand?
- Technische Fehler: entweder story-spezifisches Verhalten dokumentiert, oder explizit
  bestätigt dass die allgemeine Behandlung (adr.md: Querschnittliche Fehlerbehandlung)
  gilt – „keine Antwort" ist kein Abschluss
- Draft-Saving & Abbrechen: für jedes Formular dieser Story explizit entschieden — trivial (→ kein Draft-Saving, Abbrechen ohne Rückfrage) oder nicht-trivial (→ Draft-Saving ja/nein, Abbrechen-Verhalten per UX-Guideline Prinzip 5 geklärt); bei Draft-Saving oder Bestätigungsdialog: Szenarien eingeplant
- UI-Verhaltens-Checkliste (siehe unten) vollständig abgearbeitet

### UI-Verhaltens-Checkliste (Pflichtprüfung vor Abschluss von Schritt 1)

Diese Aspekte werden sonst als Implementierungsdetails entschieden — ohne Gherkin-Deckung.
Prüfe jeden Punkt für jede Operation aus Schritt 0.A, die ein Formular oder einen Dialog hat.
Für jeden relevanten Aspekt ohne vorhandenes Szenario: jetzt ein Szenario formulieren,
nicht später als Implementierungsdetail überlassen.

| Aspekt | Prüffrage | Wenn relevant und kein Szenario vorhanden |
|--------|-----------|-------------------------------------------|
| **Nach erfolgreicher Aktion** | Schließt sich der Dialog/das Formular nach dem Absenden? Werden Felder zurückgesetzt? Erscheint eine Bestätigung? | Szenario formulieren, das den sichtbaren Zustand nach Erfolg beschreibt |
| **Abbrechen** | Gibt es einen Abbrechen-Pfad (Button, Escape, Klick außerhalb)? Wohin führt er? Gehen Eingaben verloren? | Szenario formulieren, das die Abbrechen-Navigation und den Endzustand beschreibt |
| **Feld-Initialisierung** | Welche Werte **und Fehler-/Validierungszustände** zeigen Felder beim Öffnen — beim *ersten* Öffnen (Leer, Defaults, vorausgefüllt?) **und beim erneuten Öffnen nach einem abgebrochenen oder fehlgeschlagenen Versuch** (bleibt eine alte Fehlermeldung/Markierung stehen?) | Szenario je relevantem Öffnungs-Kontext, das den sichtbaren Zustand beschreibt — inkl. „kein Rest-Fehler nach Abbrechen + erneutem Öffnen" |
| **Async-Zustände & Sperren während Pending** | Welche Bedienelemente lassen sich während einer laufenden mutierenden Aktion auslösen? **Alle** konfliktträchtigen/schließenden Kontrollen (auslösender Button, **Abbrechen, Escape, Backdrop**) müssen gesperrt sein — nicht nur der Auslöser (UX-Guideline Prinzip 3 „Sperren während Pending"). | Szenario je Kontrolle, das die Sperre während der laufenden Aktion beobachtet |
| **Pflichtfeld-Affordance** | Hat das Formular Pflichtfelder? Sind sie als solche markiert (statisch, vor jeder Eingabe sichtbar)? | Eigenes Happy-Path-Szenario „Pflichtfelder sind als solche markiert" (getestet **beim Öffnen**, nicht im Error-Szenario) |
| **Autofokus beim Öffnen** | Liegt der Fokus beim Öffnen auf dem visuell ersten Feld? | Eigenes Happy-Path-Szenario (E2E: visuell oberstes Input hat Fokus) + Guideline-Invariant „kein CSS-Reorder von Formularfeldern" |
| **Fokus nach Validierungsfehler** | Springt der Fokus nach Submit-Fehler aufs erste fehlerhafte Feld? | **Asserts an bestehende Error-Szenarien** (kein neues Szenario): ein Fall „erstes Feld fehlerhaft" + ein Fall „nur späteres Feld fehlerhaft" |
| **Tastatur & Dialog-Fokus** (Enter-Submit, Escape, Fokus-Falle/-Rückkehr) | Liefert das Framework/HTML-native das Verhalten (echtes `<form>`, MUI `Dialog`)? | **Kein Szenario** — per UX-Guideline Prinzip 8 + Review erzwingen |

**Träger-Regel (Formular-/Dialog-Baseline — welcher Mechanismus bekommt ein Szenario?):**
Frage pro Mechanismus zuerst: *Liefert das Framework / HTML-native das Verhalten?*
- **Ja → kein Szenario**, per UX-Guideline Prinzip 8 + Review erzwingen (sonst testet das Szenario nur das Framework).
- **Nein (eigene Logik) → Szenario/Assert.** Dabei: statische Affordance (Markierung) → **eigenes** Szenario beim Öffnen (one-behavior, eigener Fehlergrund). Nur im Fehlerzustand beobachtbare Mechanik (Fokus aufs erste fehlerhafte Feld) → **Asserts an bestehende Error-Szenarien**, weil „erstes fehlerhaftes Feld" mehrere Input-Partitionen braucht, die die Error-Szenarien schon liefern. Begründung + Details: UX-Guideline Prinzip 8.

Notiere das Ergebnis der Checkliste schriftlich — für jeden Aspekt entweder:
- „Relevant – Szenario formuliert: [Titel]"
- „Relevant – bereits durch Szenario [Titel] abgedeckt"
- „Nicht relevant – [ein Satz Begründung]"

**Achtung:** Offenbart der Dialog eine Architekturentscheidung, die nicht in adr.md
steht (z.B. eine neue Verhaltenssemantik oder ein neues Zustandsmodell)? → Stopp.
Per CLAUDE.md-Regel: Business-Logik-Entscheidungen beim User nachfragen und erst dann
in adr.md dokumentieren, bevor Szenarien geschrieben werden.

→ TaskUpdate „1. Regelentdeckung (Dialog)": completed

---

## Schritt 2: Parallele Scenario-Entdeckung
→ TaskUpdate „2. Parallele Scenario-Entdeckung": in_progress

Starte drei Sub-Agenten **parallel** (in einer einzigen Nachricht mit drei Agent-Aufrufen).
Befülle die `[Platzhalter]` vor dem Senden mit den konkreten Werten aus Schritt 0/1.

Jeder Agent bekommt:
- Story-Kern inkl. Entitäten + Zustände (Schritt 0.A)
- Eingabefelder mit Typen und Constraints (Schritt 0.D)
- User-Antworten aus dem Dialog (Schritt 1) – **verbatim, nicht paraphrasiert**
  (Paraphrasen können implizite Regeln verlieren, die der User beiläufig formuliert hat)
- Constraints aus adr.md (Schritt 0.C; nur US-bezogene + allgemeine Architekturregeln)
- Bestehende Szenarien (Schritt 0.B; „keine" wenn neu)
- UX-Kontext (Schritt 0.E) – welche UX-Prinzipien gelten, mit Relevanzbewertung

**Warum parallel?** Jede Technik hat blinde Flecken. Example Mapping findet Business Rules,
State-Transition findet vergessene Zustandskombinationen, Input-Partition findet
Feldvalidierungen. Zusammen decken sie systematisch mehr ab als jede Technik allein.

Der Prompt für jeden Agent ist der Inhalt der jeweiligen Referenz-Datei, befüllt mit deinen
Werten aus Schritt 0/1. Lies jede Datei unmittelbar vor dem Agent-Aufruf und füge den Inhalt
als Instruktionen in den Prompt ein:
- **Agent A – Example Mapping** → `references/agent-a-example-mapping.md`
- **Agent B – State-Transition-Analyse** → `references/agent-b-state-transition.md`
- **Agent C – Input-Partition-Analyse** → `references/agent-c-input-partition.md`

Starte alle drei Agents parallel (drei unabhängige Agent-Aufrufe in einer Antwort) –
nicht sequentiell. Warum: Sequentielle Starts würden es späteren Agents ermöglichen, die
Outputs früherer zu sehen und unbewusst zu kopieren, statt eigenständig zu analysieren.

Warte auf alle drei Outputs bevor Schritt 3 beginnt. Wenn ein Agent-Output leer oder
offensichtlich inkonsistent mit dem Input ist, wiederhole diesen Agent-Aufruf.

→ TaskUpdate „2. Parallele Scenario-Entdeckung": completed

---

## Schritt 3: Synthese
→ TaskUpdate „3. Synthese": in_progress

Führe die Outputs von A, B, C zusammen:

1. **Deduplizierung:** Semantisch gleiche Szenarien zusammenführen. Behalte die präzisere
   Formulierung. Verliere keine Information – nur echte Duplikate entfernen.

2. **Widersprüche auflösen:** Wenn Agents verschiedene Outcomes für denselben Fall beschreiben,
   prüfe gegen adr.md und US-Akzeptanzkriterien. Nicht auflösbar?
   → Als offene Frage markieren und User fragen (kein Weitermachen mit Widerspruch).

   Wie Widersprüche erkennen:
   - Gleicher Szenario-Titel oder gleicher Given+When → unterschiedliches Then = Widerspruch
   - Komplementäre Fälle (ein Agent: „Zutat existiert", anderer: „Zutat existiert nicht")
     sind **kein** Widerspruch – beide in den Pool aufnehmen

3. **Vollständige Gherkin-Szenarien formulieren** (Formatregeln: `docs/process/e2e-testing.md`):
   - Background: übernehmen wenn vorhanden und die Given-Steps noch mit docs/reference/glossary.md-Entitäten
     und adr.md-Zustandsmodell übereinstimmen; bei Zweifel verwerfen und neu definieren –
     ein unpassender Background korrumpiert still alle darunterliegenden Szenarien, während
     Redundanz nur kosmetisch ist. Neu definieren wenn Voraussetzungen für alle Szenarien
     identisch sind.
   - Konkrete Werte statt Platzhalter (z.B. „Tomaten" statt „[Zutat]")
   - Mutierende Szenarien (create/delete/update): Then beschreibt vollständigen sichtbaren
     Endzustand, nicht nur die geänderte Eigenschaft
   - Parametrisierbare Szenarien: Wenn mehrere error-Szenarien dieselbe Fehlermeldung und
     denselben Prozessfluss haben, nur der Eingabewert variiert, mit Kommentar
     `# Kandidat für Scenario Outline` markieren – Entscheidung trifft der User in der Freigabe

4. **Sortierreihenfolge:**
   - Kategorienreihenfolge: happy-path → error → edge-case
   - **Innerhalb jeder Kategorie – Aufbau-/Abhängigkeitsprinzip (PRIMÄR):** Ein Szenario, dessen
     Vorbedingung oder Then-Aussage ein Verhalten *voraussetzt*, das ein anderes Szenario erst
     etabliert, kommt **nach** diesem. Atomare/grundlegende Verhaltensbausteine vor den darauf
     komponierten. Prüffrage je Szenario-Paar: „Setzt B voraus, dass das in A geprüfte Verhalten
     bereits funktioniert?" Ja → A vor B; steht es andersherum → umsortieren.
     Kanonisches Beispiel (echte Inversion, die ohne diese Regel durchrutschte): „Abbrechen
     schließt Dialog und verwirft Eingaben" (atomar: Abbrechen schließt + leert) muss VOR „Felder
     nach Abbrechen beim erneuten Öffnen wieder leer" (komponiert: setzt Schließen+Leeren voraus,
     um den Reopen-Zustand überhaupt prüfen zu können). Folge der Inversion: das komponierte
     Szenario muss beide Verhaltensteile auf einmal erzwingen, und das atomare wird zum
     wirkungslosen Guard-Test ohne eigenen RED-Beitrag.
   - **Innerhalb happy-path (SEKUNDÄR, bei gleicher Abhängigkeitsstufe):** trivialster Anwendungsfall
     zuerst, dann zunehmend komplexer (z.B. erst „Leere Liste anzeigen", dann „anlegen", dann
     „mehrere sortiert anzeigen"). Szenarien ohne Backend-Interaktion (reine UI-Zustandsprüfungen
     wie Feld-Init, Abbrechen) kommen vor Szenarien mit mutierenden Server-Anfragen.
   - Innerhalb error: häufigster Fehler im Produktivbetrieb zuerst
   - Innerhalb edge-case: schwerwiegendste Konsequenz bei fehlendem Test zuerst

Der Entwurf muss vollständig ausformuliert sein, bevor Schritt 4 beginnt –
der Review-Agent kann nur prüfen, was er lesen kann.

→ TaskUpdate „3. Synthese": completed

---

## Schritt 4: Review-Loop
→ TaskUpdate „4. Review-Loop": in_progress

Lies `references/agent-review.md` – der Inhalt ist der Prompt für den Review-Agenten.
Füge ihn zusammen mit diesen Inputs in den Agent-Aufruf ein:
- Feature-Entwurf aus Schritt 3 (vollständig, verbatim)
- User Story + Akzeptanzkriterien (verbatim aus Schritt 0, nicht paraphrasiert)
- Constraints aus adr.md (aus Schritt 0)

**Nach dem Review – Loop (max. 3 Iterationen):**

Schreibe „Review-Loop Iteration N/3" als sichtbare Überschrift vor jeden Review-Start,
damit der User den Fortschritt sehen kann.

1. Review-Agenten starten, Findings auswerten
2. CRITICAL oder HIGH vorhanden → Entwurf überarbeiten, weiter mit nächster Iteration
3. MEDIUM vorhanden:
   - **Formal behebbar** (z.B. falsche Sortierung, fehlender Whitespace-Test, falscher Tag):
     selbst beheben, Review wiederholen
   - **Business-Entscheidung erforderlich** (die Korrektur hätte Business-Impact – d.h. eine
     falsche Annahme würde ungewolltes Verhalten im Produkt erzeugen, z.B. eine implizite
     Validierungsregel die bestimmt was erlaubt oder verboten ist, oder Zustandsübergangs-
     semantik): User fragen, warten
   - **Nicht lösbar**: in `docs/open-questions.md` dokumentieren (Format dort) mit Kontext [US-ID],
     Problem, warum nicht gelöst, konkretes Action Item
4. LOW → Formulierungskorrekturen selbst beheben; inhaltliche LOW-Findings in der
   Freigabe-Nachricht an den User notieren
5. Keine CRITICAL/HIGH mehr → weiter mit Schritt 5

**ABBRUCHBEDINGUNG:** Nach Iteration 3 noch CRITICAL/HIGH vorhanden →
Findings + Kontext dem User präsentieren, fragen wie weiter.

→ TaskUpdate „4. Review-Loop": completed

---

## Schritt 5: Feature-File schreiben & Freigabe
→ TaskUpdate „5. Feature-File & Freigabe": in_progress

**A) Feature-File schreiben:**
Pfad: `features/<entity-plural-english>.feature`
Konvention: englischer Plural des Domain-Entitätsnamens aus docs/reference/glossary.md
(z.B. `features/ingredients.feature` für Zutat, `features/recipes.feature` für Rezept).
Wenn eine US mehrere Entitäten betrifft, benenne die Datei nach der primären Entität
(der, die in der US-Überschrift dominant ist); falls unklar: User fragen.
Datei vollständig ersetzen (oder neu anlegen) mit dem finalen Entwurf.

**B) Entscheidungen dokumentieren:**
Wurden im Workshop explizite Entscheidungen getroffen (z.B. Fehlermeldungstext,
Grenzfall-Verhalten), die noch nicht in adr.md stehen?
Falls ja: Einträge in `docs/history/adr.md` ergänzen.

**C) Freigabe vom User einholen:**
Präsentiere:
1. Zusammenfassung: Anzahl Szenarien je Tag-Kategorie, was ist neu vs. vorher?
2. Vollständiger Inhalt der Feature-Datei
3. Verbleibende MEDIUM/LOW-Findings (falls vorhanden) mit kurzem Kontext

Frage: „Bitte prüfe die Szenarien. Gibt es Anpassungsbedarf, bevor wir mit
implementing-scenario starten?"

Warte auf explizite Freigabe. Bei Anpassungsbedarf: überarbeiten und erneut vorlegen.

Falls User-Feedback ein Szenario fordert, das einer Regel in adr.md oder dem docs/reference/glossary.md
widerspricht: Konflikt explizit benennen, Regel zitieren, fragen ob das Szenario angepasst
oder die Regel aktualisiert werden soll. Business-Logic-Entscheidungen gehören dem User
(CLAUDE.md-Regel: Business-Impact → nachfragen).

→ TaskUpdate „5. Feature-File & Freigabe": completed

---

## Schritt 6: Szenario-Clustering
→ TaskUpdate „6. Szenario-Clustering": in_progress

Erst möglich, wenn die Szenarien vollständig und freigegeben sind (Schritt 5).

Die freigegebenen Szenarien in Implementierungs-Läufe gruppieren – ein Lauf bündelt die
Szenarien, die zusammen umgesetzt werden. Folge dem Algorithmus in
`references/scenario-clustering.md` und schreibe für jedes Szenario den dort beschriebenen
Lauf-Kommentar-Tag in die Feature-Datei.

Dem User das Ergebnis kurz vorlegen (Anzahl Läufe, grobe Gruppierung) und freigeben lassen.
Kommt später doch ein Szenario hinzu, diesen Schritt für die betroffenen Läufe erneut anwenden.

→ TaskUpdate „6. Szenario-Clustering": completed

---

## Nach dem Workshop

Das Feature-File ist implementierungsbereit und in Läufe gruppiert (`# @run-N`).
Nächster Schritt: `implementing-scenario` in Lauf-Reihenfolge – beginne mit `# @run-1`.
