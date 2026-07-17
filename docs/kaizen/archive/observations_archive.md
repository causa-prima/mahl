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

## OBS-S097-1 – `implementing-scenario` setzte ein Szenario pro Lauf um: zu langsam und tokenintensiv
- Quelle: User
- Status: UMGESETZT (S097)
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: gherkin-workshop / implementing-scenario
- Beobachtung: `implementing-scenario` implementierte bisher genau ein Gherkin-Szenario pro Durchlauf. Der fixe Overhead jedes Durchlaufs (Architektur-Check, TEST-REVIEW-Handshake, Review-Loop, Commit) amortisiert sich über einen winzigen Slice kaum – bei US-904 wären das 31 Einzelläufe für 31 Szenarien gewesen. Entwicklung entsprechend langsam und tokenintensiv.
- Entscheidung/Maßnahme: Mehrere Szenarien pro Lauf bündeln, aber **Homogenität vor Durchsatz** – ein homogenes Bündel (gleiches Setup, gleiche Assertion-Form, nur der Input variiert) kollabiert ohnehin zu einem parametrisierten Test (triviales 1:1-Mapping Assertion↔Szenario); ein heterogenes Bündel gleicher Größe zwingt N unabhängige Mappings gleichzeitig ins Working Memory und begünstigt Gold-Plating. Verworfene Alternativen und Gründe:
  - **Nach Dialog/Endpoint schneiden:** ein Cluster verschluckt fast die ganze Story (bei US-904 ~24 von 31 Szenarien in einem „Anlegen"-Cluster) → maximal heterogen trotz weniger Läufe.
  - **Nach Gherkin-Tag schneiden (happy/error/edge):** asymmetrisch – der error-Lauf wäre ideal homogen, der happy-path-Lauf bündelt aber Dialog-Verhalten, Anlegen, Sortierung, Löschen, Undo etc. = das heterogenste Bündel überhaupt.
  - **Nach Domänen-Capability/CRUD-Operation schneiden (ohne weitere Achse):** die Anlegen-Capability bleibt mit ~20 Szenarien weiterhin zu groß/heterogen.
  - **Capability + weicher Größendeckel (bei „zu groß" an geeigneter Stelle splitten):** führt ein Ermessenskriterium ein, das je nach Agent unterschiedlich ausfallen kann; widerspricht zudem der eigenen Prämisse – ein wirklich homogener Cluster kann nicht gleichzeitig „zu groß" sein, „zu groß" ist nur ein Signal, dass eine Homogenitäts-Achse übersprungen wurde, kein Splitkriterium für sich.
  - **Erster (intuitiver) Vier-Achsen-Schnitt:** ergab 7 Läufe, aber Gegenprobe deckte Inkonsistenzen auf (state-driven Duplikat-Tests fälschlich mit stateless Validierung verschmolzen; ein Mehrfeld-Fehlerfall stillschweigend mitgemergt) – die 7er-Zahl war Intuition + nachträgliche Rationalisierung, nicht konsequent aus der eigenen Regel abgeleitet.
  - **Umgesetzt:** vier Achsen in fester Reihenfolge – Capability (aus dem `When`) → bei Mutationen Ergebnisklasse (Validierung vs. Success/Verhalten) → Validierung weiter nach Form (stateless vs. state-driven mit Seed) dann Eingabefeld → Success/Verhalten nach Schicht (frontend-only vs. full-stack). Konsequent angewandt ergab das bei US-904 11 statt 7 Läufe, weil manche Formen (ein Mehrfeld-Fehlerfall, ein Lösch-Pending-Fall, ein Lösch-Konflikt-Fall) nur je ein Exemplar haben. Solche Singleton-Cluster bleiben bewusst eigene Läufe statt sie in einen unähnlichen Cluster zu zwingen (das schleppte genau die vermiedene Heterogenität wieder ein) – Merge in einen bestehenden Cluster ist nur zulässig, wenn Setup *und* Assertion-Form identisch sind (dann ohnehin nur eine weitere Test-Case-Zeile). Algorithmus, Hinweise und Tag-Format stehen vollständig in `.claude/skills/gherkin-workshop/references/scenario-clustering.md`. Zweiter Teil (S097): `implementing-scenario` auf Lauf- statt Einzelszenario-Konsum umgebaut (Aufruf `@US-NNN run-N`, Architektur-Check/TEST-REVIEW/Commit über alle Szenarien des Laufs, Frontend-only-Läufe ohne Backend-Subagent); `_feature.py`/`check-atdd-gate.py` um Run-Tag-Parsing erweitert, `next_scenario.py` zu `next_run.py` umgebaut (löst den nächsten offenen **Lauf** statt Einzel-Szenarios auf, ADR-S041-7-Addendum).
- Bezug: `.claude/skills/gherkin-workshop/references/scenario-clustering.md`; `.claude/skills/implementing-scenario/SKILL.md`; ADR-S041-7

## OBS-S085-10 – „Schwere" → „Impact" umbenennen (deferred Meta-Änderung)
- Quelle: Agent
- Status: UMGESETZT (S099)
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: „Impact" ist treffender als „Schwere" und schlägt die Brücke zu observations.md.
- Entscheidung/Maßnahme: **Umgesetzt (S099)** – vollständiger Rename Schwere→Impact (Feld-Key, Labels, Doku, interne Bezeichner). Entrisikt durch den Befund: Feld-Key `**Schwere:**` nur in `countermeasures.md` (Live), **nicht** in LL-Archiven (die nutzen `[HOCH]`-Tags) → keine Archiv-Migration. Ausgenommen: `review-code`-„Schweregrad" (anderes Konzept). Validiert (Tests + Scripts grün). Details: git-Diff S099.

## OBS-S092-1 – Doppelte LL/OBS-Erfassung: implementing-scenario Schritt 6.1 vs. closing-session
- Quelle: User
- Status: UMGESETZT (S099)
- Impact: GERING    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: implementing-scenario / closing-session
- Beobachtung: `implementing-scenario` Schritt 6.1 („Offene Punkte triagieren") erfasst LLs/OBSs/Tech-Debt, und `closing-session` (Schritt 2/3/5) erfasst dieselbe Klasse von Punkten erneut. Bei direktem Übergang Szenario → Abschluss ist die Vorab-Triage in 6.1 redundant – sie ist nur nötig, wenn die Session **nicht** abgeschlossen wird (Szenario fertig, Session läuft weiter). In dieser Session führte das zu doppeltem Abfragen.
- Entscheidung/Maßnahme: **Nur LL/OBS-Dedup** (Commit-Aspekt verworfen: `closing-session` committet nicht selbst – der einzige Commit sitzt in `implementing-scenario` 6.4 und staged die Abschluss-Dateien mit, also kein Doppel-Commit). Präzisierung: 6.1 leistet *mehr* als closing-session (systematisches Surfacen von Subagenten-Vorschlägen + zurückgestellten Findings) – nur das *Schreiben* der LL/OBS überschneidet sich. Umgesetzt: 6.1 surfacet + triagiert weiterhin und erledigt „direkt umsetzen"-Punkte vor dem Commit, delegiert aber das *Schreiben* der als „vermerken" entschiedenen LL/OBS an den direkt folgenden `closing-session`-Lauf (kein Doppel-Prompt); reziproke Notiz in closing-session Schritt 2 (dort nur ergänzen, was 6.1 nicht abdeckte). Kein volatiler ID-Verweis in den stabilen Skills (principles.md „Referenzen volatil→stabil").

---

## OBS-S090-1 – Vitest ist typ-blind; Typfehler erst im Stryker-Dry-Run sichtbar
- Quelle: Agent
- Status: UMGESETZT (S099)
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: frontend-tdd
- Beobachtung: `vitest` (esbuild, transpile-only) prüft **keine** Typen. Echte TS-Fehler (z.B. `ResultAsync` ≠ `Promise`; `errAsync`-`kind`-Widening) blieben bis zum Stryker-typescript-checker-Dry-Run unsichtbar (~1 Zyklus Verzögerung). Kein `tsc --noEmit`-Wrapper auf der Bash-Allow-Liste → der Layer-Implementer konnte Typen nicht isoliert **vor** dem teuren Stryker-Lauf prüfen.
- Entscheidung/Maßnahme: **Umgesetzt (S099)** – `typecheck`-npm-Script (`tsc -b`) + Exit-Gate-Schritt im `frontend-layer-implementer` (nach GREEN, vor Stryker) + Diagnose-Hinweis bei verwirrenden Testfehlern. Kein Wrapper/Allow-List-Change nötig (`npm run` bereits erlaubt).
- Bezug: OBS-S085-4 (LSP-Pilot – wenn bewährt, prüfen ob der Flow-Schritt noch nötig ist)

---

## OBS-S090-3 – Alt-Hooks überprüfen/entschlacken
- Quelle: User
- Status: UMGESETZT (S099)
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Hook/Script
- Beobachtung: Die Hook-Scripte (`check-memory.sh`, `pre-compact.sh`, `session-start.sh`, `session-end.sh`, `task-completed.sh`) stammen aus einer frühen Projektphase mit noch geringem Claude-Code-Verständnis. Mehrere tragen evtl. veraltete Annahmen (z.B. der jetzt korrigierte `/mnt/c`-Hardcode, S090). Ungeprüft, ob einzelne Hooks heute noch ihren Zweck erfüllen, redundant sind oder angepasst/entfernt gehören.
- Entscheidung/Maßnahme: **Umgesetzt (S099)** – gründlicher Audit via Fable-Subagent. Kernbefund: 4 der 5 Hooks nahmen fälschlich an, `echo`+Exit-0-stdout erreiche Claude (gilt nur bei SessionStart) → waren von Anfang an wirkungslos, dazu tote Command-Refs (`/close-session`, `/feature`) + Logikbug in session-end. Entfernt: `check-memory.sh` (Stop), `pre-compact.sh` (PreCompact), `session-end.sh` (SessionEnd), `task-completed.sh` (TaskCompleted) + ihre settings.json-Registrierungen; `session-start.sh` behalten (Mechanik korrekt). Neubau-Ideen (DoD-Gate via TaskCompleted-Exit-2 etc.) bewusst nicht verfolgt. **Teil 2 (vorausschauend, Fable-Audit):** Hook-Setup nutzt seine Möglichkeiten nach der Bereinigung weitgehend aus; **eine** hochwertige ungenutzte Chance → OBS-S095-3 (dort mit Umsetzungs-Empfehlung angereichert); übrige Schmerzpunkte (OBS-S090-4/-5) nicht hook-förmig. Details: git-Diff S099.
- Bezug: OBS-S088-1 (Dispatcher – für die verbliebenen Shell-Hooks entbehrlich, aber als reload-freier Enabler für OBS-S095-3 relevant); OBS-S095-3 (die identifizierte Hook-Chance)

## OBS-S090-5 – TD-Grooming-Lücke: Infra-Schuld fällt durchs Raster
- Quelle: User
- Status: UMGESETZT (S099)
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Sonstiges
- Beobachtung: Technische Schuld wird heute nur **opportunistisch** gegroomt (Architektur-Check in `implementing-scenario`: passende TD zum aktuellen Szenario mitnehmen). Schuld ohne Szenario-Bezug — typisch Infrastruktur, z.B. das erst in S098 (opportunistisch beim run-1-E2E) behobene **TD-S083-5** (dirty-Postgres, kein Reset zwischen E2E-Läufen) — mappt auf kein Szenario und wird so **fast nie** angefasst. Zusätzlich fehlt am Session-Ende ein Check, ob TD unbewusst miterledigt wurde (dann Eintrag schließen).
- Entscheidung/Maßnahme: **Umgesetzt (S099)** – TD-Grooming in `implementing-scenario` verankert (beide Checks dort, *nicht* in der Prozess-Retro): Schritt 0 Punkt 5 „TD-Sichtung & -Entscheidung" (vor Umsetzung je berührter TD entscheiden + begründen: mit-erledigen vs. aufschieben) + Schritt 6.1 „TD-Abgleich" (bewusst/unbewusst behobene TD schließen). Systematisiert den area-basierten opportunistischen Fang. **Rest-Lücke** (Waisen-Infra-TD, den kein Lauf je berührt) bewusst nicht hier gelöst → OBS-S099-1.
- Bezug: OBS-S087-1 (TD relevanz-filterbar); OBS-S099-1 (Rest-Lücke Waisen-TD)

---

## OBS-S090-2 – qa-check-Übergabe-Hash erzwingt Extra-Stryker-Lauf bei Re-Stage
- Quelle: Agent (Orchestrator-Beobachtung)
- Status: UMGESETZT (S099)
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: implementing-scenario / qa-check
- Beobachtung: Der `qa-check.py`-Übergabe-Hash rechnet über den **gestageten** Zustand. Stagt der Orchestrator nach der Subagent-Hash-Berechnung noch eine freigegebene Test-Änderung, mismatcht `--verify` → ein **erneuter** (teurer) Stryker-Lauf nur, um einen frischen Hash über den finalen Index zu erzeugen. In dieser Session 2× passiert (Frontend Option-A-Restage; variant-c).
- Entscheidung/Maßnahme: **Umgesetzt (S099):** qa-check-Hash rechnet jetzt über den **Working-Tree-Content** (`_worktree_content_fingerprint`) statt den git-Index; alle Checks lesen index-unabhängig (`git diff HEAD` + `--no-index` für untracked). Stagen ändert den Hash nicht mehr → kein Doppel-Stryker. Real gegen das Repo validiert (Hash invariant über `git add`). Gemeinsam mit OBS-S090-4 gelöst.

---

## OBS-S090-4 – Subagent-`git add` umgeht den Test-Review-Gate
- Quelle: User
- Status: UMGESETZT (S099)
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: TDD
- Beobachtung: Die Layer-Implementer haben das `Bash`-Tool und die Allow-Liste erlaubt `git add <datei>` → ein Subagent kann (und tat es in S090) Dateien selbst stagen. Der `qa-check`-Übergabe-Hash rechnet über den **gestageten** Zustand, weshalb der Subagent sogar stagen *muss*. Damit ist der dokumentierte Gate „Haupt-Thread reviewt Tests, *dann* staged er" faktisch nicht erzwungen: Ein Subagent könnte ungeprüfte Assertions stagen und trotzdem einen grünen 100%-Hash erzeugen. **Mutation-Score + Hash beweisen „getestet+gemutet", nicht „vom Orchestrator inhaltlich freigegeben".** Kein konkreter Schaden in S090 (Review fand statt) — Integritäts-Risiko, kein Fehlausgang.
- Entscheidung/Maßnahme: **Umgesetzt (S099):** Zwei-Teile-Lösung. (1) Der Übergabe-Hash ist jetzt index-unabhängig (Working-Tree-Content) → Stagen bringt dem Subagenten nichts mehr, der Anreiz entfällt. (2) Der eigentliche Gate ist ein **Blob-Anker**: der Orchestrator friert die freigegebenen Tests nach dem Review als immutable git-Blob ein (`git hash-object -w`), und `qa-check --verify --approved-tests` vergleicht mechanisch die aktuellen Test-Blobs gegen die Freigabe – zeigt jede Änderung seit Freigabe als Diff (Setup erlaubt, Assertions verboten). Content-addressed → immun gegen Subagent-`git add`. `--verify` erzwingt `--approved-tests` bei geänderten Tests (Vergessens-Schutz). Attack-Szenario real validiert: valider Hash + nachträglich geänderte Assertion → Hash verifiziert, Audit deckt Diff auf. Siehe CM-S070-1. Der Fable-Befund „nicht per Hook lösbar" bleibt gültig – die Lösung ist Script-basiert, kein Hook.
- Bezug: OBS-S090-2 (qa-check-Hash/Staging-Reihenfolge; gemeinsam gelöst); CM-S070-1

## OBS-S101-2 – Orchestrator pollt arbeitende Subagenten (missverständliches Team-Tooling?)
- Quelle: User
- Status: UMGESETZT (S102)
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: TOOLING    Kontext: Agent-Prompt
- Beobachtung: Der Orchestrator fragte den Layer-Subagenten während laufender ~2-min-Stryker-Läufe mehrfach nach dem Status, obwohl dieser noch arbeitete – ausgelöst durch `idle_notification`/„available"-Signale, die mehrdeutig sind (Abschluss vs. Zwischenzustand), und ein fehlendes klares „arbeite noch"-Signal. Der User berichtet, das Muster tritt session- und orchestratorübergreifend auf → vermutlich missverständliches Claude-Code-Team-Tooling, kein Einzelfehler.
- Entscheidung/Maßnahme: UMGESETZT (S102) – Ursache aus dem eigenen Harness-Kontext verifiziert statt spekuliert: „Subagents run in the background by default; you'll be notified when one completes" + „polling is wasted." Die **Completion-Notification** ist das Signal, idle-/available-Zwischensignale sind es nicht. Leitplanke daher gegen **beide** möglichen Ursachen (mehrdeutiges Signal *oder* Orchestrator-Missverständnis) robust: Spawn-Regel „Arbeitende Subagenten nicht pollen" im inneren Loop von `implementing-scenario` – auf den inhaltlichen Return warten, Zwischensignale nicht mit Status-Nachfragen beantworten. Gespiegelt als CM-S102-3 (evaluierbar). Option B (erst `claude-code-guide`-Agent zur `idle_notification`-Mechanik) verworfen – die Harness-Semantik war bereits belastbar und die Leitplanke ursachen-robust.
- Bezug: CM-S102-3

## OBS-S100-1 – Zustandsdokumente sammeln Erledigtes / Verweise auf gelöschte Artefakte
- Quelle: User
- Status: UMGESETZT (S102)
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Doku-Hygiene
- Beobachtung: Agenten halten wiederkehrend **bereits Erledigtes** an Stellen fest, die nur den *offenen/aktuellen* Zustand tragen sollten (Changelog-artig; diese Session „erledigt in run-2" in TD-S077-1, vom User korrigiert – laut User ein Muster über viele Sessions). Allgemeiner: **Verweise zeigen auf Artefakte, die beim Erledigen gelöscht werden** – z.B. „siehe TD-SXXX" auf ein TD, das beim Abschluss entfernt wird → toter Verweis, die referenzierte Info existiert danach nur noch in der git-Historie. Ergebnis: aufgeblähte Zustandsdokumente + dangling references / Informationsverlust. Betrifft nicht nur umgesetzten Code, sondern jede Referenz auf inzwischen irrelevante/gelöschte Dinge. **Aktuell kein akuter Schaden, weil der User beim Mitlesen manuell abfängt – aber das ist ein fehlerträchtiger, nicht garantierter, ermüdender *menschlicher* Guard, kein struktureller; der scheinbar geringe Impact ruht also auf User-Aufwand (Verstärker: OBS-S100-2).**
- Entscheidung/Maßnahme: UMGESETZT (S102) – Prinzip „Zustandsdokumente tragen nur den offenen/aktuellen Zustand – kein Erledigtes" in `principles.md` (Abschnitt „Doku & Referenzen") mit **beiden** Richtungen: präventiv (nichts Erledigtes hineinschreiben) + kurativ (erledigte Einträge aktiv entfernen, sie leben in git/Archiv weiter). Gespiegelt als CM-S102-1 (evaluierbar). Der mechanisierbare Teilaspekt „tote Refs auf volatile IDs" wird vom geplanten Poka-Yoke-Hook OBS-S095-3 mit abgedeckt (dort als Bezug vermerkt). Konsequent nach OBS-S100-2: menschlicher Guard reicht nicht, so viel wie möglich mechanisieren.
- Bezug: OBS-S100-2, OBS-S095-3, CM-S102-1

---

## OBS-S100-2 – Agent-Auffälligkeiten erodieren User-Vertrauen → mehr Kontrolle → Ermüdung (Verstärker)
- Quelle: User
- Status: UMGESETZT (S102)
- Impact: HOCH    Häufigkeit: dauerhaft
- Kategorie: AGENT    Kontext: Mensch-Agent-Zusammenarbeit
- Beobachtung: Jede Auffälligkeit (nicht nur OBS-S100-1) hat neben dem lokalen Defekt einen versteckten Zweitschaden: sie erodiert das Vertrauen des Users in die Agenten, woraufhin er *alles* genauer prüft – anstrengend, ermüdend, ein sich selbst verstärkender Kreislauf. Der wahre Kostenfaktor einer Auffälligkeit ist damit größer als der lokale Defekt; scheinbar „geringe" Auffälligkeiten summieren sich über diesen Kanal.
- Entscheidung/Maßnahme: UMGESETZT (S102) – als Priorisierungs-Linse in `docs/kaizen/process.md`, Abschnitt „Gefahr & Kandidaten-Bewertung", verankert (Bullet „Vertrauens-/Ermüdungs-Multiplikator"): der Multiplikator zählt zum lokalen Impact hinzu, und bei gleichem lokalem Impact schlägt der strukturelle Poka-Yoke-Guard den Wachsamkeits-Guard. Dort verankert statt als abstraktes principle, weil die Linse genau am Kandidaten-Bewertungspunkt wirken soll. Keine CM (Meta-Linse im Prozess selbst, kein trackbares Einzel-Verhalten).
- Bezug: OBS-S100-1

---

## OBS-S086-5 – Session-Datei-Inhalt: Scope definieren
- Quelle: User
- Status: UMGESETZT (S102)
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: Unklar/unausgewertet, was in `docs/history/sessions/session_NNN.md` gehört – ist es sinnvoll, alles festzuhalten? Welche Teile können/sollten weg, was fehlt? (Analog zu OBS-S085-9 für `index.md`, aber für die Session-Dateien.)
- Entscheidung/Maßnahme: UMGESETZT (S102) – **beide** Dimensionen empirisch geprüft (auf User-Nachfrage, gegen den Zerlegungs-Fehler „nur eine Richtung"): (i) *„fehlt etwas?"* → keine Reibung in lessons_learned/Archiv gefunden (anders als das analoge S085-9 „index.md zu lang", das einen konkreten Auslöser hatte). (ii) *„kann weg?"* → Session-Dateien real gesichtet (session_100/101): „Offene Punkte/Nächster Lauf" dupliziert `AGENT_MEMORY` „Nächste Prioritäten" + `next_run.py` und ist in read-only Historie sofort stale; „Learnings/Beobachtungen" sind ein knapper ID-Index (milde Redundanz). **Umsetzung:** `closing-session` Schritt 4 um eine Scope-Disziplin ergänzt – Session-Datei = Historie (was passierte); KEIN vorwärtsgerichteter Zustand; Learnings/Beobachtungen nur als ID+Ein-Satz+Verweis. Einmal-Skill-Regel (keine CM, GERING). Verzahnt mit OBS-S100-1 / CM-S086-1 (Single Source of Truth).

## OBS-S095-2 – review-docs: Check auf „Low-Value-Content" (grenzwertiger Mehrwert, Kosten > Nutzen)
- Quelle: User
- Status: UMGESETZT (S102)
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: Skills/Docs könnten Selbstverständlichkeiten enthalten — Regeln, gegen die ohnehin nie verstoßen würde, oder Inhalte mit grenzwertigem Mehrwert, deren Token-/Lesekosten den Nutzen nicht rechtfertigen. Offen, ob der `review-docs`-Skill dafür einen expliziten Check hat. Die Skill-Beschreibung nennt „Minimalität", aber das zielt eher auf Redundanz/Länge — „Low-Value-Content" (Regel ist korrekt, aber unnötig, weil der Fehler praktisch nie passiert) ist ein anderer, schärferer Winkel und evtl. nicht abgedeckt.
- Entscheidung/Maßnahme: UMGESETZT (S102) – Discovery bestätigte die Lücke: `review-docs` Agent 1 prüft nur Progressive Disclosure / Redundanz / Länge, nicht den Low-Value-Winkel. Agent 1 um ein Kriterium „Low-Value-Content" ergänzt, bewusst als **Prüf-Linse** (flaggen + begründen, nicht blind streichen – die Beurteilung „wird nie verletzt" ist selbst unsicher). Einmal-Skill-Regel (keine CM, MITTEL, aber gezielt in bestehenden Skill integriert).
- Bezug: —

---

## OBS-S095-3 – Poka-Yoke-Hook: stabile Datei darf keine volatile ID referenzieren (Referenz-Richtung)
- Quelle: User
- Status: UMGESETZT (S102)
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Das principles.md-Prinzip „Referenzen laufen volatil → stabil, nie umgekehrt" wird nur manuell durchgesetzt (S094: LL-S094-2; S095: 2 weitere Funde in Skills). Ein **syntaktischer** Check ist poka-yoke-bar (kein Ermessen): Beim Edit/Write einer **stabilen** Datei prüfen, ob neuer Inhalt ein **volatiles** ID-Schema (`OBS-`/`OQ-`/`LL-`/`TD-S…`) referenziert. Empirie S095: nur 5 Bestands-Treffer in 3 stabilen Dateien (FP-Risiko niedrig) — **sofern** die kaizen-internen Bookkeeping-Dateien (`observations.md`, `countermeasures.md`, `lessons_learned.md`, `process.md`) aus dem „stabilen" Set ausgeschlossen werden.
- Entscheidung/Maßnahme: UMGESETZT (S102) – als **eigenständiges PreToolUse-Script** `.claude/hooks/check-ref-direction.py` gebaut (nach dem Zwilling-Muster `check-e2e-scenario-ref.py`), via TDD (14 Tests in `tests/test_ref_direction.py`), in `settings.json` unter `Edit|Write` registriert, exit 2. **Design-Korrektur zur S099-Empfehlung:** NICHT in den `check-code-quality-blocking.py`-Dispatcher gehängt – der ist PostToolUse + auf C#-Code-Fragmente ausgelegt; der Zwilling ist bewusst ein eigenes Pre-Script. Das entkoppelt S088-1 (verliert seinen Enabler-Zug). Datei-Scope (User-Entscheid S102): **default-protected** (`docs/**`, `.claude/skills/**`, `.claude/agents/**`, `CLAUDE.md`) **+ explizite Ausnahmen** (kaizen-Bookkeeping, `archive/`, volatile Tracker tech-debt/open-questions/AGENT_MEMORY, `history/sessions/`, `skills/kaizen/`) – robuster gegen neue Dateien als eine Whitelist. Zeilen-Ausnahme via `ref-ok`-Marker. Bestand bereinigt: adr.md 2 Beleg-Verweise entfernt, adr.md 2 + TS-Pilot als `ref-ok` markiert; `principles.md` bewusst geschützt (sauber). Deckt zugleich den toten-Ref-Teil von OBS-S100-1 ab. → CM-S102-2.
- Maßnahme: (frühere Bestandsnotiz) 2 von 5 Refs in S095 bereinigt; **Fable-Hook-Audit S099** bestätigte den Hook als einzige hochwertige ungenutzte Poka-Yoke-Chance (Prio HOCH), FP-arm, ermessensfrei.
- Bezug: principles.md „Referenzen volatil→stabil"; CM-S086-1 (Referenz-Hygiene/stale Anchors); LL-S094-2; OBS-S100-1 (Hook soll den toten-Ref-Teilaspekt „Verweis auf volatile/gelöschte ID" mit abdecken)

---

## OBS-S095-4 – „Lead-Developer"-Subagent als Eskalations-Instanz für Layer-Implementer
- Quelle: User
- Status: VERWORFEN (unzuverlässiger Trigger + YAGNI + Kommunikations-Overhead)
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: AGENT    Kontext: Agent-Prompt
- Beobachtung: Statt anspruchsvolle Schichten komplett auf Opus laufen zu lassen, könnte ein dedizierter „Lead-Developer"-Subagent (stark, z.B. Opus) als Eskalations-Instanz dienen, an den schwächere Implementer (sonnet/haiku) gezielt **Fragen** übergeben — wie in echten Teams, wo Juniors Hilfestellung von Seniors holen. So liefe nur der punktuelle Rat auf dem teuren Modell, nicht die ganze Schicht. Vorausschauende Optimierung der Modell-/Token-Ökonomie; baut auf der S095-Entscheidung „Implementer-Default = sonnet, Opus-Eskalation pro Schicht" auf.
- Entscheidung/Maßnahme: VERWORFEN (S102). **Kern-Einwand (User):** Der Mechanismus hängt an einem **Selbst-Eskalations-Trigger** – der schwächere Implementer müsste seine eigene Grenze erkennen und um Hilfe bitten. Genau diese Metakognition ist bei LLM-Subagenten unzuverlässig (systematische Überkonfidenz, Dunning-Kruger-artig): der Auslöser feuert gerade dann nicht, wenn er am nötigsten wäre → struktureller Konstruktionsfehler, nicht bloß „noch nicht nötig". **Zusätzlich:** (a) YAGNI – „ganze Schicht auf Opus" (S095) ist nicht als zu teuer belegt; (b) ein Fragen-Protokoll verschärft die ohnehin reibende Orchestrator↔Subagent-Kommunikation (vgl. OBS-S101-2). Die *proaktive* Variante (ungefragtes Senior-Review) existiert bereits als Review-Auditoren → nichts Eigenständiges bleibt übrig. Re-Aufgriff nur bei belegtem Bedarf (Opus-Schicht-Eskalation nachweislich zu teuer *und* ein zuverlässigerer, nicht selbst-eingeschätzter Trigger).
- Bezug: OBS-S085-8 / OBS-S093-2 (Modellwahl pro Schicht); OBS-S101-2 (Kommunikations-Reibung)

---

## OBS-S087-1 – Technische Schuld durchsuchbar/relevanz-gefiltert machen
- Quelle: User
- Status: VERWORFEN (konsolidiert in OBS-S096-3, S104)
- Impact: GERING–MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: `docs/tech-debt.md` wird heute per Volltext-grep durchsucht (bei 10 Einträgen ausreichend). Wächst die Datei, wäre es nützlich, wenn der Architektur-Check in `implementing-scenario` (oder ein eigenes Script) die zum bearbeiteten Code-Bereich **potentiell relevante** technische Schuld automatisch identifiziert/auflistet – z.B. über kuratierte Bereichs-Keywords pro Eintrag. Bewusst NICHT jetzt umgesetzt (YAGNI): Keyword-Vokabular sollte **gemeinsam mit dem konsumierenden Script** entworfen werden, sonst spekulative Tags ohne Abnehmer + Drift.
- Entscheidung/Maßnahme: **Verworfen als eigener Eintrag (S104) – Gegenstand entfällt NICHT** (nicht Kalt-Abwertung): TD-Relevanz-Filterung ist ein **Spezialfall** von OBS-S096-3 (Scripted-Access-Layer) und lebt dort als Facette + Re-Trigger (1) „implementing-scenario TD-Sichtung reibt" weiter (deckungsgleicher Abnehmer). Getrennte Verfolgung wäre Redundanz.
- Bezug: OBS-S096-3 (konsolidiert); OBS-S085-16 (AGENT_MEMORY-Restruktur, in deren Zuge tech-debt.md ausgelagert wurde)

## OBS-S087-2 – Gemeinsame „Tracker-Datei-Konvention" einmal dokumentieren
- Quelle: Agent
- Status: VERWORFEN (Low-Value + Drift-Last, S104)
- Impact: GERING–MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: `observations.md`, `countermeasures.md`, `tech-debt.md`, `open-questions.md` teilen inzwischen dasselbe Muster (Header `wann-lesen/wann-schreiben/Eintrag-Format`, Session-basierte IDs `XX-S<NNN>-<n>`, Fließtext statt Tabelle, `---`-Trenner zwischen Einträgen, Sortierung nach ID aufsteigend). Das Muster ist nirgends zentral beschrieben → beim Anlegen einer neuen Tracker-Datei wird es ad-hoc re-derived (S087: tech-debt.md ~4× überarbeitet, s. LL-S087-1). Eine einmalige Konventions-Beschreibung (z.B. in `process.md` oder einem kurzen Doku-Styleguide) würde das vermeiden.
- Entscheidung/Maßnahme: **Verworfen (S104).** Low-Value: eine *neue* Tracker-Datei anzulegen ist sehr selten (die 4 bestehenden decken den Bedarf); eine zentrale Konventions-Doku kostet laufende Wartung + Drift-Risiko gegen die realen Dateien, ohne verlässlichen Abnehmer. Simpelste Baseline genügt: beim Anlegen eine bestehende Tracker-Datei als Vorlage nehmen. Kein Kalt-Abwertungs-Verwerf – der Nutzen wäre auch bei Frisch-Beobachtung gering und selten.
- Bezug: LL-S087-1

## OBS-S096-1 – Vor OBS-Erfassung mit bestehenden Einträgen zusammenfassen (parametrisiert/Klasse/Referenz)
- Quelle: User
- Status: UMGESETZT (S104)
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Kaizen
- Beobachtung: Vor dem Festhalten einer neuen OBS prüfen, ob sie mit einem bestehenden Eintrag zusammenfassbar ist – analog parametrisierten Tests: dieselbe Beobachtung an anderer Stelle → bestehendes OBS erweitern statt neu anlegen. Auch nach Problemklassen/anderen Gruppierungen bündeln. Zudem per `Bezug:` mehrere OBS an derselben Stelle gemeinsam lösbar machen (auch bei unterschiedlichen Problemen). Senkt Backlog-Redundanz und Drain-Last.
- Entscheidung/Maßnahme: **Umgesetzt (S104) im Drain statt bei Erfassung.** Pushback zum Original-Zeitpunkt „Erfassung": systematischer Backlog-Abgleich ist teure Klassifikation und würde das Prinzip „Erfassung ist billig, Klassifikation ist teuer" (`process.md`) verletzen. Stattdessen `draining-observations` Schritt 3 um **„Thematisch/parametrische Konsolidierung"** erweitert (dasselbe/eng verwandte Problem → tragenden Eintrag erweitern, anderen `VERWORFEN (konsolidiert in …)` bzw. via `Bezug:` koppeln) – zusätzlich zur bestehenden Same-Artefakt-Kolokation. Genau in diesem Drain praktiziert (S087-1 → S096-3).
- Bezug: OBS-S086-2 (Verständnis vor Erfassung); OBS-S086-3 (blockweise)

## OBS-S096-2 – Welche Skill-Schritte deterministisch per Script erledigbar?
- Quelle: User
- Status: UMGESETZT (S104)
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Skill/Script
- Beobachtung: Systematisch prüfen, welche Skill-Schritte deterministisch per Script statt freihändig vom Agenten erledigt werden könnten – inkl. Schritte, die erst Voraussetzungen brauchen (z.B. „zum Parsen muss das Header-/Eintragsformat deterministisch bestimmbar sein"). Senkt Token/Varianz, erhöht Verlässlichkeit.
- Entscheidung/Maßnahme: **Umgesetzt (S104) als stehendes Prinzip statt Big-Bang-Audit** (dauerhaft wirksam, nicht Momentaufnahme): (a) `docs/kaizen/principles.md` → „Deterministische Skill-Schritte mechanisieren" (Prozess-Disziplin, Session-Start geladen); (b) Prüfpunkt in `.claude/agents/workflow-auditor.md` Dimension 5 (Ressourceneffizienz) → greift beim `review-workflow`-Audit. Bewusst dort statt `review-docs`: Mechanisierbarkeit ist Prozess-/Effizienz-Design, nicht Textqualität (Projekt-Abgrenzung review-docs↔review-workflow). Ein mechanisch erzwingendes Gate ist unmöglich (Mechanisierbarkeit = semantisches Urteil, kein Muster) → Nudge ist die Obergrenze. Bekannte Kandidaten (z.B. nächste Session-Nummer bestimmen, gerade manuell per grep gemacht) opportunistisch umsetzen.
- Bezug: OBS-S096-3

## OBS-S102-2 – `qa-check` TEST-FREIGABE-AUDIT sieht die geänderte Testdatei nicht (mögliches Poka-Yoke-Loch)
- Quelle: Orchestrator
- Status: UMGESETZT (S104)
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: In run-3 meldete `qa-check.py --verify --approved-tests` wiederholt „Check 1: GEÄNDERTE TEST-DATEIEN: keine" und im TEST-FREIGABE-AUDIT „`…IngredientsEndpointsTests.cs`: freigegeben, taucht aber nicht unter den geänderten Test-Dateien auf (committet/zurückgesetzt?)", obwohl `git status` die Datei klar als `M` (unstaged) zeigt und sie inhaltlich neue Tests enthält. Der Audit vergleicht die freigegebene Datei nur, wenn er sie als „geändert" erkennt; erkennt Check 1 die Änderung nicht, unterbleibt der Anker-Abgleich still. Damit könnte eine nachträgliche Assertion-Manipulation (genau das, was der CM-S070-1-Blob-Anker fangen soll) durchrutschen. In run-3 kein Schaden (Orchestrator hat den Diff manuell reviewt, Inhalt = Anker), aber der mechanische Guard versagte hier lautlos – die Ursache (warum Check 1 die geänderte Datei nicht sieht) ist unverstanden. Klasse „Poka-Yoke schlägt Wachsamkeit" (OBS-S100-2).
- Entscheidung/Maßnahme: **Umgesetzt (S104, TDD).** Ursache belegt: Backend-xUnit-Tests liegen unter `Server.Tests/`, aber `qa-check.py` setzte `_LAYER_PATHS["backend"] = "Server/"` – `"Server.Tests/…".startswith("Server/")` ist False → `check_changed_test_files("backend")` war systematisch blind (Frontend nie betroffen, Tests unter `Client/src/`). **Tragweite größer als erfasst:** nicht nur der Blob-Anker-Audit, auch `_worktree_content_fingerprint("backend")` band den Backend-Testcode NICHT in den Übergabe-Hash → da `--verify` Stryker nicht neu laufen lässt, blieb ein Hash nach Assertion-Entfernung gültig; CM-S070-1 war für Backend faktisch aus. Fix: `_LAYER_PATHS` auf Prefix-Tupel (`Server/`, `Server.Tests/`); `_changed_paths`/`_worktree_diff` nehmen ein Tupel, `str.startswith(tuple)` + git-Multi-Pathspec. 3 Regressionstests (`test_check_changed_test_files_backend_in_server_tests_dir`, `…_content_fingerprint_backend_binds_server_tests`, `…_audit_approved_tests_backend_server_tests_dir`). Kein neuer CM (Bug-Fix an bestehendem Guard).
- Bezug: CM-S070-1 (Blob-Anker-Audit); OBS-S100-2 (Poka-Yoke vs. Wachsamkeit)

## OBS-S102-3 – Team-Subagenten liefern ihren Endbericht inkonsistent (plain text statt `SendMessage` → Orchestrator sieht ihn nicht)
- Quelle: Orchestrator
- Status: UMGESETZT (S104)
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: AGENT    Kontext: Agent-Prompt
- Beobachtung: In run-3 lieferten 3 von 4 Review-Auditoren (code-quality/functional-correctness/test-quality) ihren Findings-Report per `SendMessage` an den Orchestrator; der vierte (security-auditor) gab ihn als **plain-text-Output** aus und wurde damit idle. Plain-Text-Output eines Team-Subagenten ist für den Orchestrator **nicht sichtbar** (SendMessage-Tool-Doku: „to communicate, you MUST call this tool") → der Report lag im Subagent-Log, kam aber nie beim Orchestrator an, bis dieser ihn nach User-Hinweis per `SendMessage` aktiv anforderte. Weder die Auditor-Agent-Definitionen (`.claude/agents/*-auditor.md`) noch der `review-code`-Spawn-Prompt schreiben den Ausgabekanal (Endbericht per `SendMessage` an den Orchestrator) explizit vor → inkonsistentes Berichtsverhalten, ein Review-Finding kann komplett übersehen werden. Der Orchestrator-Fallback (CM-S102-3: bei finished ohne Report aktiv abrufen) fängt es ab, behebt aber nicht die Ursache beim Subagenten. Verifiziert per Log-Nachschau (Subagent-Log `agent-asec-run3-*`, plain-text-Report um 20:07, `SendMessage` erst um 20:11 nach Nachfrage).
- Entscheidung/Maßnahme: **Umgesetzt (S104).** Ausgabekanal zentral im `review-code`-Spawn-Prompt vorgeschrieben (Block „Agent-Prompts enthalten"): Endbericht **per `SendMessage` an den Orchestrator**, nicht als plain-text-Output – mit Begründung (Team-Subagent-plain-text ist für den Orchestrator unsichtbar) und Standalone-Ausnahme (kein Team → Rückgabewert ist der Kanal). Bewusst zentral statt in die 5 `*-auditor.md` dupliziert: hält die Agent-Defs kontext-frei (wissen nicht, ob Team-Spawn). CM-S102-3 bleibt als Orchestrator-Fallback; diese Zeile behebt die Ursache beim Subagenten.
- Bezug: CM-S102-3 (Orchestrator-Fallback); OBS-S101-2 (Subagent-Signal-Semantik)

---

