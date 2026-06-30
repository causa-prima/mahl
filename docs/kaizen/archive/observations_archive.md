# Observations – Archiv

<!--
Zweck: Aufgelöste Beobachtungen aus docs/kaizen/observations.md. Beim Drain (Skill draining-observations)
       werden Einträge mit Status UMGESETZT oder VERWORFEN hierher VERSCHOBEN (nicht kopiert), damit die
       Live-observations.md scannbar bleibt. obs-drain.py erinnert am Session-Start an noch nicht
       verschobene aufgelöste Einträge (Hygiene-Reminder).

Format der Einträge: wie observations.md zum Zeitpunkt der Archivierung – ältere Einträge können
                     entfallene Felder (z.B. das frühere `Kandidaten:`) tragen.
-->

> **Quelle:** `docs/kaizen/observations.md`
> **Format-Referenz:** `docs/kaizen/process.md`

---

## OBS-S085-5 – Doku-Links per Anchor statt Sektions-Position
- Quelle: User
- Status: UMGESETZT (S086)
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: TOOLING    Kontext: Doku
- Beobachtung: Links in der Doku verweisen auf Positionen („Sektion 6"), die stale werden; Agenten suchen ineffizient.
- Entscheidung/Maßnahme: Aufgegangen im Prinzip „Single Source of Truth" (grep-barer Anchor / Heading-Text / ID statt „Sektion N"-/Zeilen-Position). → CM (S086, AKTIV).
- Bezug: OBS-S085-15

## OBS-S085-6 – lessons_learned-Format wird in closing-session wiederholt eingelesen
- Quelle: User
- Status: UMGESETZT (S086)
- Impact: GERING    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Skill-Nutzung
- Beobachtung: Das Format wurde regelmäßig per Datei-Einlesen geprüft → Zeit/Token-Verschwendung.
- Entscheidung/Maßnahme: Präzise Ursache (S086): die LL-Datei muss zum Edit ohnehin gelesen werden – die echte Verschwendung war ein *separater* `process.md`-Read für das Format (closing-session Schritt 5 zeigte dorthin). Fix: Format kanonisch im `lessons_learned.md`-Header (+ Mini-Beispiel); `process.md` §Eintrag-Format, closing-session Schritt 5 und das Template referenzieren nur noch den Header (Single Source gegen Drift).
- Bezug: OBS-S085-15

## OBS-S085-9 – index.md-Einträge werden zu lang
- Quelle: User
- Status: UMGESETZT (S086)
- Impact: GERING    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: Einträge in `docs/history/sessions/index.md` wurden über die Sessions hinweg immer länger.
- Entscheidung/Maßnahme: Drift per Plot als **Verbosity-Ratchet** belegt (nicht Scope-Wachstum – frühe Sessions leisteten mehr in weniger Zeichen). **A+B:** Soft-Ziel 150 / harter Cap 300 Zeichen (Kurzfassung = ein Satz, *was* sich änderte, kein „warum"); `check-index-length.py` als CLI-Report **und** PreToolUse-Hook (grandfathered: nur neueste/geänderte Zeilen), geteilte Logik in `_index_length.py`; closing-session Schritt 6 gehärtet; S76–S85 gekürzt. Live verifiziert.

## OBS-S085-11 – ID-Retrofit für bestehende lessons_learned-Einträge (deferred Meta-Änderung)
- Quelle: Agent
- Status: UMGESETZT (S085)
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: Neue LL-Einträge bekommen IDs; ~99 Bestands-Findings haben keine. Nutzen spekulativ.
- Entscheidung/Maßnahme: **A — kein Retrofit**; IDs nur für neue Einträge (gängige Praxis). Entschieden S085.
- Bezug: OBS-S085-10

## OBS-S085-13 – Retro-/Findings-Präsentation pro Punkt strukturieren
- Quelle: User
- Status: UMGESETZT (S086)
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Kommunikation
- Beobachtung: Bei vielen Findings war schwer erkennbar, was Problem/Warum-jetzt/Vorschlag/Alternativen ist; leere Findings-Abschnitte wurden still weggelassen.
- Entscheidung/Maßnahme: **A+B** in `kaizen` SKILL Schritt 5: pro Finding vier Facetten explizit (Problem / Warum jetzt / Vorschlag / Alternativen, auch als Tabellen-Spalten in A); leere Abschnitte nicht still weglassen, sondern kurz nennen (was + warum leer).

## OBS-S085-15 – Referenzieren statt duplizieren; greppbare Anchors/IDs statt Zeilennummern
- Quelle: User
- Status: UMGESETZT (S086)
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: Infos teils über mehrere Dateien dupliziert (Drift-Gefahr); Verweise per Position statt grep-barem Marker.
- Entscheidung/Maßnahme: **A** — Prinzip „Single Source of Truth: Information am passendsten Ort, sonst referenzieren" in `principles.md` (Abschnitt „Doku & Referenzen": kontextfrei am passendsten Ort; sonst referenzieren mit grep-barem Anchor; Zeilennummern nur für read-only-Dateien; referenzierte Stelle geändert → referenzierende mitpflegen) + Spiegel-CM (S086, AKTIV).
- Bezug: OBS-S085-5, OBS-S085-6, OBS-S085-9, OBS-S085-16

---

## OBS-S085-1 – Absolute-Pfad-Retries bei Bash verschwenden Token
- Quelle: User
- Status: UMGESETZT (S087) – `normalize_repo_paths` in `check-bash-permission.py`; `updatedInput`+`additionalContext` live verifiziert.
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Bash/Permission
- Beobachtung: Agenten versuchen wiederholt Bash mit absoluten Pfaden, laufen in den Permission-Deny und verschwenden Token (Deny-Log S086: 113/295 Zeilen mit `/mnt/c/...`, steigender Trend).
- Kandidaten: A) Hook schreibt Befehl auf relativen Pfad um | B) Deny mit gezieltem Hinweis | C) Doku/Allow-Liste schärfen
- Entscheidung/Maßnahme: **Kandidat A** (bei sauberem Scoping geringe Gefahr; spart den Retry-Round-Trip, den B kostet). `check-bash-permission.py` normalisiert als erster Schritt jeden absoluten Repo-Root-Präfix (dynamisch via `CLAUDE_PROJECT_DIR`/Skript-Pfad; ursprünglich der `/mnt/c/...`-Windows-Pfad) → relativ (**breit**, da Einheitlichkeit der Regel der Hauptnutzen ist). [S089: WSL-nativ – die `cmd.exe /c`-Ausnahme (Windows-`C:\…`) entfällt.] `# --allow-once`-Befehle unangetastet (ONE_TIME-Check zuerst). Bei Änderung `updatedInput` (umgeschriebener Befehl) + `additionalContext` (Hinweis an Agent). `defer` verworfen – würde die Hook-eigene Analyse umgehen.

---

## OBS-S085-7 – Zeilenlimits für Tests/Frontend sinnvoll?
- Quelle: User
- Status: UMGESETZT (S087) – `eslint.config.js`: `complexity`/`max-depth` error (auch Tests), `max-params` warn, `max-lines-per-function` warn 50 / aus für Test+Spec; general-Guideline „Komplexität & Refactoring" um Aspiration-vs-Backstop-Hinweis + Param-Richtwert ergänzt (Schwellen via Config-Verweis, keine Kopie). ESLint grün, kein Bestands-Verstoß.
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: QUALITÄT    Kontext: TS-Code
- Beobachtung: ESLint erzwingt `max-lines-per-function: 50` hart für **alle** `**/*.{ts,tsx}` inkl. Tests; Guideline nennt parallel „~20 Zeilen" (Mismatch). Für Tests/JSX nie evaluiert.
- Entscheidung/Maßnahme: **Differenzieren**, begründet über „was proxyt die Metrik": `complexity: error 10` überall inkl. Tests (hohe Komplexität im Test ist selbst ein Smell); `max-depth: error 4`; `max-params: warn 4` (Konstruktoren/Domänenobjekte nicht sauber per Glob ausschließbar → warn statt error; C#-Param-Limit ist separater SonarAnalyzer/`.editorconfig`-Layer); `max-lines-per-function: warn 50` (Prod) / **aus** für Tests (`**/*.{test,spec}.{ts,tsx}`). Zwei-Stufen = Guideline-Aspiration vs. Lint-Deckel (Lint ≥ Guideline), zweistufig nur bei der verrauschten Zeilen-Metrik; JSX nicht per Glob sondern über Komplexität + Review.

---

## OBS-S085-8 – (Sub-)Agenten nutzen nicht das aufgaben-passende Modell
- Quelle: User
- Status: UMGESETZT (S087) – 6 read-only-Auditoren `model: sonnet`, beide Layer-Implementer `model: inherit`; `review-code`/`implementing-scenario`/`review-workflow` um „Modellwahl vor Spawn"-Hinweis ergänzt. `kaizen` spawnt keine Subagenten → entfällt.
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Agent-Prompt
- Beobachtung: Alle 8 Agenten sind `model: inherit`; Token werden verschwendet, wenn nicht das passende Modell genutzt wird.
- Kandidaten: A) Orchestrator wählt Modell nach Schwierigkeit | B) Cap pro Agent via Frontmatter | C) Status quo
- Entscheidung/Maßnahme: **A+B kombiniert** (Tool-Vertrag bestätigt: `Agent`-`model`-Param übersteuert Frontmatter → Frontmatter = Default, kein Deckel). Defaults: 6 read-only-Auditoren `model: sonnet`, beide Layer-Implementer `inherit`. Skills (`implementing-scenario`, `review-code`, `kaizen`/`review-workflow`) weisen an: Modell vor jedem Spawn nach Schwierigkeit wählen.
- **Rezidiv + offene Design-Frage (S090, Quelle: User):** In S090 keine bewusste Pro-Spawn-Modellwahl durchgeführt (Layer-Implementer liefen via `inherit` auf Opus 4.8, Auditoren auf Sonnet-Default) — der „reicht der Default?"-Check (Maßnahme A) wurde nicht dokumentiert angewandt. Daraus die noch nicht beantwortete Default-Frage: Ist `inherit` (→ Orchestrator-Modell, hier Opus) der richtige **Implementer**-Default, oder sollte er auf `sonnet` stehen mit gezielter Opus-Eskalation für schwere Schichten?
- **Default-Frage entschieden (S095, Retro):** Implementer-Default beider Layer-Implementer auf **`model: sonnet`** umgestellt (Frontmatter); Opus-Eskalation **pro Schicht** beim Spawn, festgehalten als neuer **Schritt-0-Punkt 5** in `implementing-scenario` (löst zugleich OBS-S093-2). Damit erledigt. Folge-Idee Lead-Developer-Subagent → OBS-S095-4.

---

## OBS-S085-14 – countermeasures.md: IDs + Fließtext-Format (wie ADR/LL/OBS)
- Quelle: User
- Status: UMGESETZT (S087) – `countermeasures.md` auf Fließtext + CM-IDs (`CM-S<NNN>-<n>`) umgebaut (21 Einträge); `retro_report.py` `load_cm` parst Header/Metadaten/Problem-Zeile (am LL-Parser orientiert), `cm_id` im Datenmodell + Escalated-Report; 5 neue Tests in `test_retro_report.py` (14 grün). Format-Doku in process.md („Tabelle"→„Datei") nachgezogen. OBS-S085-10 (Schwere→Impact) NICHT gekoppelt – „Schwere" beibehalten (konsistent mit LL-Parser), bleibt deferred.
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: Die CM-Tabelle ist schwer lesbar und CMs sind schwer referenzierbar (keine IDs).
- Kandidaten: A) CM-IDs einführen (`CM-S<NNN>-<n>`) | B) Tabelle → Fließtext (`retro_report.py` `load_cm` parst die `|`-Tabelle → Script muss mit)
- Entscheidung/Maßnahme: **A + B jetzt.** A = CM-IDs. B = Tabelle→Fließtext mit Header-Sektion; `load_cm` anpassen – am bestehenden LL-Fließtext/Header-Parser orientieren bzw. Code wiederverwenden, Test-Nachweis (mittlere Gefahr). Ggf. mit OBS-S085-10 koppeln.

---

## OBS-S085-16 – AGENT_MEMORY.md verschlanken / umstrukturieren
- Quelle: Agent (Analyse) + User (Anmerkungen)
- Status: UMGESETZT (Teil A S087, Teil B S088).
  - **Teil A (S087):** physischer Split (V2): `docs/tech-debt.md` + `docs/open-questions.md` ausgelagert (eigene Header/IDs: TD-S…, OQ-S…); AGENT_MEMORY auf schlanken Auto-Inject reduziert; Pflege-Konvention in `closing-session` Schritt 8; ~8 Referenzen nachgezogen. Keyword-/Relevanz-Script für tech-debt → eigene **OBS-S087-1**.
  - **Teil B (S088) – Generator doch umgesetzt:** Die S087-Ablehnung („kein maschinelles Mapping, CamelCase-Testname ≠ Szenario-Titel") wurde aufgelöst durch die **`// Szenario: <Titel>`-Kommentar-Konvention** über jedem E2E-Test (ADR-S041-7-Addendum). `next_scenario.py` leitet DONE daraus ab und löst den `{{NEXT_SCENARIO}}`-Platzhalter beim Session-Start auf (`session-start.sh --render`); Reihenfolge-Abweichungen via expliziten Anstrich über dem Platzhalter (Feature-File-Reihenfolge bleibt unangetastet). Das **separate Header-Feld „Nächstes Szenario" entfällt** (es konkurrierte mit der Prioritätenliste → Widerspruch, der diese Session auslöste). Mapping-Integrität als Poka-Yoke-Hook `check-e2e-scenario-ref.py` (bidirektional: Spec-Edit + Feature-Edit). Anschluss-Beobachtung Hook-Sprawl → **OBS-S088-1**.
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: AGENT_MEMORY.md wird per `session-start.sh` bei JEDEM Start voll injiziert → jede Zeile kostet Token. 4-KB-Limit ohne Enforcer (S083 aufgehoben); aktuell ~7 KB.
- Leitfrage (User): „Welche Info braucht *jeder* Agent beim Start, um den Projektstatus für *seine* Aufgabe zu verstehen?" Was das nicht erfüllt → read-on-demand, referenziert.
- Kandidaten: A) Doku-Restruktur (schlanker Auto-Inject-Index + ausgelagerte Details) | B) Inject-Mechanik via Script | C) besser beschreiben, was in die Datei gehört/nicht (via Leitfrage)
- Entscheidung/Maßnahme: **A zuerst** (Doku-Restruktur; „Prioritäten/Phase" bleiben **hand-geschrieben**, Rest ableitbar) → **dann B als Generator-Script** (zieht letzte Session aus `index.md`, offene CMs aus `countermeasures.md`, prüft Größenbudget). **C ergänzt:** beim Umsetzen die Leitfrage als Filter nutzen + explizit dokumentieren, was rein-/nicht reingehört. Dateiname nach Restruktur entscheiden. Begleitprinzip: Single Source of Truth (OBS-S085-15).
- Bezug: CM „AGENT_MEMORY 4-KB-Limit" (S083, OFFEN); OBS-S085-15

---

## OBS-S093-2 – implementing-scenario Schritt 0: expliziter Modell-Eignungs-Check pro Schicht
- Quelle: User
- Status: UMGESETZT (S095) – als Schritt-0-Punkt 5 „Modell-Eignung je geplanter Schicht" in `implementing-scenario` SKILL.md ergänzt (Default `sonnet`, Opus-Eskalation pro Schicht, beim Spawn nur bestätigt). Gemeinsam mit OBS-S085-8 entschieden.
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Skill-Nutzung
- Beobachtung: Die Modellwahl für Schicht-Subagenten (OBS-S085-8: starker Default, `sonnet` nur für klar triviale Schichten) wird aktuell erst unmittelbar **vor dem Spawn** entschieden. Idee: in Schritt 0 (Architektur-Check) bereits pro erwarteter Schicht festhalten, welches Modell voraussichtlich genügt – die Komplexitätseinschätzung liegt dort ohnehin vor (YAGNI-Scope, Domain-Typen). Spart eine spätere Ad-hoc-Entscheidung und macht die Token-/Eignungs-Abwägung nachvollziehbar.
- Kandidaten: A) Schritt-0-Punkt „Modell-Eignung je geplanter Schicht" ergänzen, der beim Spawn nur noch bestätigt wird (gering) | B) Status quo (Entscheidung am Spawn) | C) Heuristik-Tabelle (Schicht-Typ → Modell) in den Skill
- Entscheidung/Maßnahme: offen (Retro) – Kandidat A wahrscheinlich; mit OBS-S085-8 abgleichen, um keine doppelte Regel zu schaffen.
- Bezug: OBS-S085-8 (Modellwahl vor Spawn)

---

## OBS-S086-1 – OBS-Kandidaten gemeinsam erarbeiten statt eigenmächtig vorab festlegen
- Quelle: User
- Status: UMGESETZT (S096)
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Skill-Nutzung
- Beobachtung: Kandidaten in OBS-Einträgen wurden bisher vom Agenten eigenmächtig vorformuliert → teils unpassende/unvollständige Vorschläge, gemeinsam-umzusetzende Optionen oder fehlende Möglichkeiten; das gemeinsame Nachdenken wird übersprungen. Erfassung sollte billig bleiben (nur Beobachtung + ggf. *als roh markierte* Idee); Kandidaten-Discovery + Bewertung gehören in den Retro-Evaluierungsschritt.
- Entscheidung/Maßnahme: **UMGESETZT (S096)** – Kandidaten-Feld aus dem OBS-Schema entfernt (poka-yoke: in ein nicht existierendes Feld lässt sich nichts vorab nudgen). Kandidaten-Discovery entsteht frisch beim Drain (Skill `draining-observations`), nicht bei der Erfassung.
- Bezug: OBS-S086-2, OBS-S086-3, OBS-S085-13

## OBS-S091-1 – `dotnet-test.py` zeigt bei RED keine Assertion-Details (MTP-Runner)
- Quelle: Agent
- Status: UMGESETZT (S096)
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: `dotnet-test.py` gibt bei Fehlschlag (Default **und** `--verbose`) nur `Failed: N, Passed: M` + einen Verweis auf eine UTF-16-`.log` aus — **keine** Assertion-Message/Expected-Actual. Empirisch verifiziert (S091, gezielt gebrochene Assertion, voller ungefilterter Output): der MTP-Runner (xunit.v3, TD-S089-1) schreibt Fehlerdetails nur in `TestResults/*.log`, nicht auf stdout im Format, das das `_RELEVANT`-Regex (`Error Message`/`at mahl.`) erwartet. Beim RED-Debugging fehlt damit genau die Info, die man braucht (der Backend-Subagent musste die UTF-16-Datei manuell lesen).
- Entscheidung/Maßnahme: **Umgesetzt S096** (war: Direktfix vor nächstem Szenario, S095-Entscheid, Batch mit OBS-S091-3): `dotnet-test.py` gibt bei RED die fehlgeschlagene Assertion aus den MTP-Failure-Logs auf stdout aus (Default + `--verbose`), empirisch verifiziert. Details/Rationale beim Code (`dotnet-test.py`).
- Bezug: TD-S089-1 (MTP-Migration); OBS-S085-3 (Wrapper-Output-Filtern)

## OBS-S091-3 – `vitest-run.py --filter` Substring-Semantik nicht offensichtlich
- Quelle: Agent
- Status: UMGESETZT (S096)
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: `vitest-run.py --filter X` matcht X als Substring über den **voll-qualifizierten** Testnamen (inkl. `describe`-Block). Ein neuer describe-Block „…(leere Einheit)" wurde dadurch zunächst übersprungen → irreführendes „N passed" statt der erwarteten Gesamtzahl (der FE-Subagent zog ungefiltert nach). Verbesserung: Filter-Semantik dokumentieren oder die Zahl gematchter/übersprungener Tests ausweisen.
- Entscheidung/Maßnahme: **Umgesetzt S096** (war: Direktfix vor nächstem Szenario, S095-Entscheid, Batch mit OBS-S091-1): `vitest-run.py` weist bei aktivem `--filter` ausgeführte/übersprungene Tests samt Substring-Semantik aus und wertet 0 gematchte Tests fail-closed als Fehler (Exit 1 statt vitests grünem 0); empirisch verifiziert. Details/Rationale beim Code (`vitest-run.py`).
- Bezug: OBS-S085-3 (Filter-/Output-Familie); OBS-S091-1

## OBS-S095-1 – OBS speisen Jenga nicht → Retro droht mit OBS-Themen vollzulaufen und lang zu werden
- Quelle: User
- Status: UMGESETZT (S096)
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Skill-Nutzung
- Beobachtung: Observations speisen den Jenga-Score bewusst nicht (kein Problemdruck) und werden nur in der Retro getrefiert. Folge: Das offene OBS-Backlog wächst monoton zwischen den Retros (aktuell ~25 offene Einträge), und Schritt 4 (Backlog-Grooming) bläht die Retro auf — viele Punkte auf einmal, kognitiv anstrengend (vgl. OBS-S086-3). Es fehlt ein Mechanismus, der das Backlog zwischen Retros abbaut oder die Grooming-Last begrenzt (z.B. Priorisierung/Stapelung, Sofort-Erledigung trivialer OBS außerhalb der Retro, OBS-Budget pro Retro).
- Entscheidung/Maßnahme: **UMGESETZT (S096)** – kontinuierlicher Drain ersetzt Retro-Voll-Grooming: SessionStart-Hook (`obs-drain.py`) schlägt jede Session einen Wert-/Alters-Lane-Satz vor (Rate `clamp(round(0.4·B),3,7)`, Gleichgewicht ~8), Skill `draining-observations` behandelt ihn (umsetzen/verwerfen/aufschieben). Mechanismus: `docs/kaizen/process.md` „Backlog-Abbau: kontinuierlicher Drain". Adressiert (a) Wachstum bremsen (Drain jede Session), (b) Hochwertiges sofort (Prioritäts-Lane statt Retro-Wartezeit), (c) Kandidaten-Discovery beim Drain statt Erfassung.
- Bezug: OBS-S086-3 (blockweise Findings), OBS-S086-1 (keine Vorab-Kandidaten), OBS-S085-12 (Noise-Review-Skalierung)

---

## OBS-S091-4 – Suppressions systematisch tracken (Script)
- Quelle: User
- Status: VERWORFEN (S096)
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Suppressions (Stryker + Analyzer/`.editorconfig`) systematisch tracken, vermutlich per Script. Zwei Ziele: **(1)** Suppressions, die ein nachfolgendes Szenario beheben soll, nicht aus den Augen verlieren — S091 hing das an manueller Erinnerung (die FE-`:53`-Suppression wurde planmäßig im „leere Einheit"-Szenario aufgelöst; ADR-S000-4 war eine solche Vertagung, die obsolet wurde und lingerte). **(2)** Suppressions ohne Szenario-Bezug periodisch, **nach Klasse gruppiert** reviewen — ändert sich etwas, das eine Klasse überflüssig macht (z.B. löste `noUncheckedIndexedAccess` den `Partial<…>`-Workaround), will man wissen, wo diese Suppressions sitzen.
- Entscheidung/Maßnahme: Großteils redundant: Suppressions tragen ihre Regel-ID im Marker (Stryker-Mutator / `#pragma warning SXXXX` / eslint-rule / editorconfig-Key) → schon klassenweise grepbar (Ziel 2); co-lokierte Suppressions sieht man beim Edit an der Stelle (Ziel 1, User-Pushback bestätigt); klassenweite Prinzip-/Config-Changes macht man ohnehin bewusst. Einzige reale Lücke = vertagte/lingernde Suppressions (ADR-S000-4) → gehört zu OBS-S090-5.
- Bezug: ADR-S000-4 (gelöschte Suppression-Vertagung), OBS-S090-5 (TD-Grooming-Lücke)

---

## OBS-S093-3 – „Nächste Prioritäten" brauchen pro Vorzieh-Item Scope + Begründung + Done-Zustand
- Quelle: User
- Status: UMGESETZT (S096)
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: In `AGENT_MEMORY.md` → „Nächste Prioritäten" wurde ein vorgezogenes Item zu weit gefasst notiert („`@US-904-error`-Block vorziehen") und ohne dauerhaft sichtbare Begründung. Folge: Der Vorzieh-Grund (S091 feld-keyed-422-Bug) wurde inertial weitergeschleppt, obwohl er längst erledigt war; ein Agent konnte weder erkennen, woraus das Vorgezogene besteht, noch wann es fertig ist. „Error-Szenarien vorziehen" ist zu weit; „Error-Szenario leerer Name + leere Einheit vorziehen, weil <Grund>" ist eng genug. Gilt auch für andere Vorzieh-Items (z.B. „Erst-Formular-UX-Baseline vor dem Feature-Fluss" braucht ebenfalls einen notierten Grund).
- Entscheidung/Maßnahme: Schreib-Hinweis in `closing-session` Schritt 7 (Projekt-Status/AGENT_MEMORY) ergänzt: jedes Vorzieh-/Prioritäts-Item eng fassen + sichtbaren Grund + Done-Zustand notieren (`<enge Aktion> — Grund: … — Done: …`), sonst wird ein erledigter Grund inertial weitergeschleppt.

---

## OBS-S094-1 – AGENT_MEMORY auf Skill-Scope eindampfen (Cruft dupliziert auto-geladene Quellen)
- Quelle: User
- Status: UMGESETZT (S096)
- Impact: GERING    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: `AGENT_MEMORY.md` wird bei jedem Session-Start voll injiziert (jede Zeile kostet Token), enthält aber Inhalte, die **andere ebenfalls auto-geladene Quellen** duplizieren: (a) die „Letzte Aktualisierung"-Zeile (Datum aus git/Index/Harness ableitbar, Änderungs-Summary ↔ Session-Index-Zeile); (b) der Navigations-Header (Session-Logs, adr via `decisions.py`, Kaizen, tech-debt, open-questions) ↔ CLAUDE.md-Navigationstabelle (die „Navigationszentrale", ebenfalls beim Start geladen). Der `closing-session`-Skill (Schritt 8) scoped die Datei ohnehin auf **Phase + Aktuelle Story + Nächste Prioritäten** – Header/Changelog stehen quer dazu.
- Entscheidung/Maßnahme: AGENT_MEMORY auf das Nötige eingedampft: Navi-Header (Dup der CLAUDE.md-Navigationszentrale) + „Letzte Aktualisierung"-Zeile entfernt; es bleiben Phase, Aktuelle Story (Input für `next_scenario.py` – muss bleiben) und Nächste Prioritäten. Retro-Trigger nicht mehr hand-gepflegt: `session-start.sh` injiziert ihn bei Jenga-Score ≤ 0 automatisch (`jenga_score.py`-grep). Folge: `closing-session`-Jenga-Schritt entfernt und kaizen-Skill vereinfacht (kein manuelles Trigger-Entfernen – nach der Retro resettet das `lessons_learned`-Archiv den Score, der Trigger klärt sich selbst).

---

## OBS-S086-2 – Verständnis vor Erfassung sichern (ggf. grill-me)
- Quelle: User
- Status: UMGESETZT (S096)
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Skill-Nutzung
- Beobachtung: OBS wurden teils falsch erfasst – Negativbeispiel OBS-S085-4 („languageServer buggy" meinte eigentlich „wir nutzen gar keinen Language-Server"). Vor dem Festhalten sicherstellen, dass Ziel/Problem richtig verstanden ist; bei Unklarheit `grill-me` nutzen.
- Entscheidung/Maßnahme: `closing-session` Schritt 2 (Erfassung) um einen Check ergänzt: beim Festhalten Ziel/Problem korrekt benennen (nicht eine vermutete Lösung), bei echter Unklarheit kurz rückfragen – die zum Verständnis nötigen Details sind beim späteren Drain oft nicht mehr ableitbar.
- Bezug: OBS-S086-1; LL-S086-2

## OBS-S086-3 – Viele Findings nicht alle auf einmal – kategorie-/blockweise
- Quelle: User
- Status: UMGESETZT (S096)
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Kommunikation
- Beobachtung: Alle OBS in einem Rutsch zu besprechen ist token-effizient, aber kognitiv anstrengend (ständiges gedankliches Hin-/Herspringen). Bei vielen Punkten kategorieweise (wie A/B/C) und/oder blockweise (nur x Beobachtungen auf einmal, dann die nächsten).
- Entscheidung/Maßnahme: `draining-observations` Schritt 2 verschärft: Items in sinnvoll gruppierten, kleinen Blöcken und nur wenige auf einmal vorlegen – schon wenige gleichzeitig sind kognitiv anstrengend (Kontext-Switch), erst recht bei Mehrrunden-Diskussion. (Ursprünglich aus der Retro-Ära mit Voll-Behandlung; gilt für den Drain genauso.)
- Bezug: OBS-S085-13

## OBS-S086-4 – `--allow-once`: Notwendigkeits- und Gefahr-Hinweise
- Quelle: User
- Status: UMGESETZT (S096)
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Bash/Permission
- Beobachtung: Drei Ideen für `check-bash-permission.py` bei `# --allow-once`-Befehlen: (a) prüfen, ob `--allow-once` überhaupt nötig ist (Befehl evtl. ohnehin allow-listed) → Hinweis zurückgeben; (b) den Deny-Grund / das Gefährliche aufbereitet bei der User-Freigabe mitgeben (highlighten, damit der User es nicht übersieht); (c) den Agenten anweisen, bei `--allow-once` zu beschreiben, was der Befehl Gefährliches tut und warum es nicht ohne geht (entfällt, wenn der User vorab manuell `--allow-once` angeordnet hat).
- Entscheidung/Maßnahme: `check-bash-permission.py` umstrukturiert: bei `# --allow-once` wird der nackte Befehl klassifiziert – (a) wäre er ohnehin erlaubt → direkt allow + Agent-Hinweis „Marker unnötig" (macht (c), den Nudge gegen inflationären Gebrauch, überflüssig); (b) wäre er deny → ask mit dem Deny-Grund/der Gefahr als `permissionDecisionReason` am Freigabe-Prompt. (b) empirisch verifiziert (S096): der Destruktiv-Grund erschien im Dialog. TDD in test-bash-permission.py.
- Bezug: OBS-S085-1

