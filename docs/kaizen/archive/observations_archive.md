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

## OBS-S092-3 – kaizen-Workshop prüft LL-Metadaten (v.a. Impact) vor dem Retro-Skript
- Quelle: User
- Status: UMGESETZT (S107)
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Review
- Beobachtung: LL-Metadaten (insb. Impact) könnten falsch/inkonsistent gesetzt sein und damit Jenga-/Prioritäts-Matrix verzerren. Idee: Der kaizen-Workshop listet vor dem Retro-Skript potentielle Metadaten-Fehler auf. Nutzen ist empirisch prüfbar: mehrere Subagenten bewerten bestehende Einträge (oder ein Sample) **blind** neu; viele Abweichungen → analysieren und Schlüsse ziehen (echte Fehlklassifikation vs. bloßer Drift / subjektive Streuung).
- Entscheidung/Maßnahme: **S099 (Drain) aufgeschoben bis S105** – kein Drain-Quick-Edit, sondern erst die Blind-Rebewertung als Sonde nötig. Diese läuft in der nächsten Kaizen-Retro billig mit (LLs werden dort ohnehin angefasst): zu Beginn mehrere Subagenten ein LL-Sample **blind** re-raten lassen, Abweichungen prüfen → dann über einen festen Workshop-Schritt entscheiden. In AGENT_MEMORY „Nächste Prioritäten" als Retro-Auftakt vermerkt (sonst vergessen). Re-Trigger: nächster Kaizen-Lauf. **S107 (Sonde durchgeführt → UMGESETZT):** 3 Subagenten rateten ein 12-Einträge-Sample (tag-entfernt) blind neu → hohe Inter-Rater-Reliabilität (11/12 einstimmig) + ~⅓ Abweichung vom Ist, wobei die Rater in den Divergenzen näher an der process.md-Definition lagen (LL-S096-1 als GERING klar fehl-getaggt). Befund: reales Fehl-Rating (nicht bloße Streuung); Ursachen (a) Fehl-Raten bei Erfassung, (b) grobe Impact-Definitionen. Umsetzung: process.md-Impact-Rubrik geschärft (Klasse≠Einzelfall, Neuheit≠Impact, „schnell bemerkt" kein Kriterium) + billiger fester Impact-Sanity-Check in kaizen Schritt 0 (blinder Multi-Rater nur als Eskalation, nicht als stehender Schritt – Token-Kosten); 5 Impacts der Periode korrigiert.
- Bezug: Impact-Vokabular geteilt mit lessons_learned

---

## OBS-S106-3 – `dotnet-stryker.py --mutate <Datei>` untauglich für Test-Removal-Gegenprobe
- Quelle: Subagent
- Status: UMGESETZT (S109)
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Mutation-Testing
- Beobachtung: Für die Gegenprobe „bleibt der Score 100 %, wenn Test X entfernt wird?" (Gold-Plating-Nachweis) lieferte `dotnet-stryker.py --mutate <Zieldatei>` keine verwertbare Aussage – alle Mutanten wurden als „Excluded" gemeldet (0/0/0). Erst der volle `qa-check.py`-Lauf war belastbar. Der Quick-Check adressiert einen anderen Zweck (eine Zieldatei fokussiert prüfen) und ist für die „Survivor durch Testentfernung"-Frage strukturell ungeeignet.
- Entscheidung/Maßnahme: **Umgesetzt (S109) – die Diagnose der Beobachtung war falsch, was der Fix sichtbar macht.** „Alle Mutanten Excluded (0/0/0)" war kein struktureller Mangel des Quick-Checks, sondern derselbe Pfad-Fehlgriff wie in OBS-S103-1: ein repo-root-relatives `--mutate`-Ziel leert den Scope, und das Ergebnis kam als scheinbar valides „100 %" zurück – weshalb es wie eine Eigenschaft des Werkzeugs aussah statt wie ein Bedienfehler. Genau dieser Fall bricht jetzt vor dem Lauf mit Korrekturvorschlag ab (`_stryker_target.py`), und ein leerer Report gilt nicht mehr als bestanden. Damit ist `--mutate <Datei>` für die Removal-Gegenprobe brauchbar: Der Lauf misst entweder die Zieldatei oder sagt, dass er nichts gemessen hat. Nicht als „konsolidiert" verworfen, weil die Fehl-Diagnose selbst das Lehrstück ist: ein stilles 0-Ergebnis wird als Werkzeug-Eigenschaft fehlinterpretiert.
- Bezug: OBS-S103-1

## OBS-S103-1 – `dotnet-stryker.py --mutate` unklar bei Einzeldatei-Ziel / stillem 0-Treffer
- Quelle: Subagent
- Status: UMGESETZT (S109)
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Mutation-Testing
- Beobachtung: `dotnet-stryker.py --mutate` akzeptiert nur eine einzelne Datei (keine Kommaliste/Brace-Expansion), und der Pfad muss relativ zu `Server/` sein (`Endpoints/Foo.cs`, nicht `Server/Endpoints/Foo.cs`). Bei falschem Muster oder 0 gefundenen Mutanten für die Zieldatei meldet das Tool stillschweigend `0/0/0` statt einer klaren Fehlermeldung → der Subagent brauchte zwei unnötige Läufe, bis er es per Doku-Beispiel (`--mutate Domain/Foo.cs`) korrigierte.
- Entscheidung/Maßnahme: **Umgesetzt (S109)** – alle drei Teilprobleme: (1) *Kommaliste* statt Einzeldatei (s. OBS-S102-1); (2) *falsche Basis* wird vor dem Lauf erkannt – `_stryker_target.py` prüft jedes Muster projekt-relativ und schlägt bei einem repo-root-relativen Pfad den korrigierten vor („Meintest du `Endpoints/Foo.cs`?"), statt den Subagenten raten zu lassen; (3) *stiller 0-Treffer* endet mit Exit 2 vor dem Lauf bzw. – falls die Config den Scope leert – mit dem Null-Mutanten-Gate danach. Verworfen: die Doku nachschärfen, ohne den Mechanismus zu ändern; der Pfad ist gerade deshalb eine Falle, weil praktisch jedes andere Script hier repo-root-relativ arbeitet – Wissen allein hätte den Fehler weiter zugelassen. Die Doku-Korrektur ist trotzdem erfolgt (`dev-workflow.md`).
- Bezug: –

## OBS-S100-3 – `qa-check` gibt bei <100 % nur den Score aus, nicht die Survivor-Zeilen
- Quelle: Orchestrator
- Status: UMGESETZT (S109)
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Mutation-Testing
- Beobachtung: Meldet `qa-check` einen Stryker-Score < 100 %, nennt es nur die Prozentzahl, nicht *welche* Zeilen überlebten. Man muss danach separat `stryker-frontend.py` (bzw. den Backend-Pendant) bemühen, um die Survivor-Stellen zu sehen – ein zusätzlicher Lauf für Information, die der eben abgeschlossene Lauf bereits hatte. Konkret in dieser Session beim 98,1-%-Survivor (Fokus-Guard) aufgetreten.
- Entscheidung/Maßnahme: **Umgesetzt (S109) als Mitnahme** beim Stryker-Guard-Umbau (gleiche Dateien): `qa-check` gibt Survivors und NoCoverage jetzt direkt mit Datei/Zeile/Mutator aus – die Formatierung liegt in `_stryker_report.py` und wird mit `stryker-summary.py` geteilt, statt sie zu duplizieren. Zusätzlich steht der **Umfang** (Dateien / valide Mutanten) in der Ausgabe, was im Test dieser Session sofort einen zu eng gelaufenen Report auffliegen ließ. Verworfen: auf `--verbose` verweisen – das wäre wieder ein zweiter Lauf für Daten, die der erste schon hatte.
- Bezug: OBS-S085-3

---

## OBS-S102-1 – `dotnet-stryker.py --mutate` akzeptiert nur einen einzelnen Dateipfad
- Quelle: Subagent
- Status: UMGESETZT (S109)
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: `--mutate` nimmt nur einen Dateipfad; ein komma-getrenntes Mehrfach-Argument scheitert („unrecognized arguments" bzw. beim String-Workaround „Excluded" auf allen Dateien). Wer mehrere geänderte Dateien in einem Lauf gezielt mutieren will, muss mehrere separate Läufe machen (kleine Zeitkosten). Aufgetreten in run-3, als der Backend-Implementer zwei Dateien in einem Lauf mutieren wollte.
- Entscheidung/Maßnahme: **Umgesetzt (S109):** beide Wrapper nehmen jetzt eine Kommaliste (`--mutate a,b`) und übersetzen sie in die CLI-Form, die die jeweilige Stryker-Variante tatsächlich versteht – empirisch geklärt statt angenommen, weil die beiden sich hier unterscheiden: **Stryker.NET** akzeptiert mehrere `--mutate`-Flags, aber **keine** Kommaliste (verifiziert: Kommaliste → 0 Mutanten; zwei Flags → 2 Dateien / 13 Mutanten = exakt die Summe der Einzelläufe); **StrykerJS** umgekehrt, es parst `--mutate` selbst als Kommaliste (`createSplitter(',')` in `stryker-cli.js`), ein zweites Flag überschriebe das erste. Die abgelehnte Alternative – die Wrapper-Signatur an die jeweilige Stryker-Syntax anzulehnen – hätte den Unterschied an den Aufrufer durchgereicht; die Kommaliste ist für beide Schichten dieselbe. Brace-Globs bleiben bewusst ungültig (beide splitten am Komma und zerreißen sie) und werden mit Hinweis abgelehnt.
- Bezug: –

---

## OBS-S108-3 – Mutations-Läufe können erfolgreich aussehen, ohne etwas mutiert zu haben
- Quelle: Subagent (backend- + frontend-layer-implementer, run-8)
- Status: UMGESETZT (S109)
- Impact: HOCH    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Drei unabhängige Wege, auf denen ein Mutations-Lauf als bestanden erscheint, obwohl er nichts oder nur einen Bruchteil geprüft hat. (a) `dotnet-stryker.py --mutate` erwartet einen **projekt**-relativen Pfad (`Endpoints/Foo.cs`); mit einem repo-root-relativen Pfad (`Server/Endpoints/Foo.cs` – die Form, die praktisch jedes andere Script im Repo nutzt) wird die Zieldatei als „Excluded" gewertet und der Lauf endet mit „Score: 100.0 %, Valid: 0". (b) `--mutate` mit Brace-Glob (`"src/{a.tsx,b.ts}"`) wird am Komma zerlegt → ungültige Globs → Dry-Run über 0 Dateien, Exit 0. (c) `qa-check.py` weicht bei einem erkannten konkurrierenden Stryker-Lock auf einen bereits vorhandenen Report aus – auch wenn dieser aus einem `--mutate`-Einzeldatei-Lauf stammt und damit einen ganz anderen Scope hat; der Output war in sich widersprüchlich („Score: 100.0 %" oben, „ACHTUNG: Mutation-Score 100.0 % < 100 %" unten) und kostete den Subagenten mehrere Minuten Diagnose. Gemeinsamer Nenner: In allen drei Fällen ist die ausgegebene Zahl 100 %, und in keinem Fall belegt sie, was sie zu belegen scheint. Der Übergabe-Hash bindet den Report-Inhalt, nicht dessen Umfang – bei (c) wäre er also formal gültig gewesen. Der Orchestrator hat den Report-Scope (Dateizahl, Mutantenzahl) in dieser Session deshalb einmal von Hand nachgezählt; das ist kein Bestandteil des regulären Gates.
- Entscheidung/Maßnahme: **Umgesetzt (S109) – drei Guards, je einer pro Weg.** (1) *Null-Mutanten-Gate:* die Score-Formel stand wörtlich doppelt (`stryker-summary.py`, `qa-check.py`) und lieferte bei `total_valid == 0` eine 100 %; sie liegt jetzt einmalig in `_stryker_report.py`, gibt in diesem Fall `score = None` aus und lässt das Gate fehlschlagen – `qa-check` bricht dabei VOR dem Übergabe-Hash ab, analog zum bestehenden Veraltet-Report-Abbruch. Damit ist (a) und (b) unabhängig von der Ursache geschlossen. (2) *Ziel-Validierung vor dem Lauf* (`_stryker_target.py`): jedes `--mutate`-Muster muss projekt-relativ real treffen, sonst Exit 2 mit Korrekturvorschlag; Brace-Globs werden mit Begründung abgelehnt. (3) *Lock-Abbruch unterscheidbar:* `_run_lock.py` beendet mit eigenem Code 99 („Lauf gar nicht gestartet"), `qa-check` behandelt das als harten Fehler statt auf den Report des Fremdlaufs auszuweichen. Zusätzlich nennt jede Auswertung den **Umfang** (Dateien / valide Mutanten), weil der Hash den Report-Inhalt bindet, nicht dessen Scope. Verworfen wurde die Alternative „Orchestrator zählt den Scope weiter von Hand nach" – sie war schon einmal nötig und ist genau die Disziplin-Lösung, die der Fall unterläuft. Abgesichert durch `test-stryker-guards.py` (24 Fälle); alle drei Wege zusätzlich real reproduziert (u.a. Kommalisten-Lauf, der vorher „100 %" gemeldet hätte).
- **Vierter Weg, beim Verifizieren gefunden (S109):** Ein Lauf, dessen Mutanten sämtlich am Checker scheitern (`CompileError`), erzeugt bei StrykerJS einen **NaN**-Score – und Stryker lässt ihn durch das *eigene* break-Threshold: „Final mutation score of NaN is greater than or equal to break threshold 100", Exit 0. Der Fall ist also nicht auf Bedienfehler beschränkt und wäre auch mit korrektem `--mutate`-Pfad aufgetreten; das Null-Mutanten-Gate deckt ihn mit ab, weil es am Ergebnis (0 valide Mutanten) ansetzt statt an der Ursache. Die Fehlermeldung gibt zusätzlich die Status-Verteilung aus, damit „gar keine Mutanten erzeugt" von „alle in einem Nicht-Bewertungs-Bucket" unterscheidbar ist.
- Bezug: OBS-S102-1

---

## OBS-S108-4 – Wrapper-Ergonomie: kein Fortschritt sichtbar, Pfad-Zwang, verdrehte Log-Reihenfolge
- Quelle: Subagent (backend- + frontend-layer-implementer, run-8)
- Status: UMGESETZT (S109)
- Impact: GERING    Häufigkeit: häufig
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Drei kleine Reibungspunkte an den Script-Wrappern, alle ohne Fehlsignal-Risiko. (a) Langlaufende Wrapper geben ihre kuratierte Ausgabe erst am Ende aus; bei Läufen über 120 s bleibt die Task-Output-Datei minutenlang leer, und der Ersatz-Pollpfad `.claude/tmp/stryker_frontend_out.txt` wird am Ende gelöscht – währenddessen ist nicht unterscheidbar, ob der Lauf arbeitet oder hängt. (b) `npm run typecheck` ist nur aus dem `Client/`-Verzeichnis heraus erlaubt, `npm --prefix Client run typecheck` wird geblockt. (c) `dotnet-stryker.py` schreibt seine eigenen `print()`-Ausgaben („Starte: …", „Report verschoben → …") gepuffert, während der `dotnet stryker`-Subprozess ungepuffert auf denselben fd schreibt – im nicht-TTY-Output erscheint der Report-Score dadurch **vor** der „Starte:"-Zeile, was beim schnellen Lesen wie ein Fehlgriff des Aufrufers aussieht.
- Entscheidung/Maßnahme: **Umgesetzt (S109), alle drei.** (a) Die Live-Log-Datei wird am Laufende **nicht mehr gelöscht** – sie ist der einzige Weg, einen laufenden Wrapper zu beobachten, und enthält danach mehr als die ausgegebenen letzten 30 Zeilen; der nächste Lauf überschreibt sie ohnehin. Die Startzeile weist explizit auf sie hin. Verworfen: eine eigene Fortschritts-Anzeige zu bauen – der Log existiert bereits, er wurde nur weggeräumt. (b) `--prefix <dir>` ist in der Bash-Allow-Liste jetzt zugelassen, damit npm-Scripts kein `cd Client` mehr erzwingen. Dabei fiel eine Falle auf, die den naiven Fix zum Sicherheitsloch gemacht hätte: alle Wrapper-Pflicht-Muster verlangen `npm` und `run` direkt nebeneinander, `npm --prefix Client run test` wäre also an ihnen vorbeigelaufen – Allow- und Wrong-Approach-Muster teilen sich deshalb ein gemeinsames Fragment (`_NPM_RUN`), abgesichert durch neue Fälle in `test-bash-permission.py`. (c) Die Wrapper flushen jetzt vor jedem Subprozess-Aufruf; die verdrehte Reihenfolge kam daher, dass der Python-Puffer erst am Prozessende leerlief, während der Subprozess ungepuffert auf denselben fd schrieb.
- Bezug: –

---

## OBS-S085-2 – Zu verbose Kommunikation (Orchestrator↔Subagenten) verschwendet Token
- Quelle: User
- Status: VERWORFEN (Phase-1-Messung: der vermutete Posten liegt bei 8,6 %, der reale Treiber ist ein anderer)
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Agent-Prompt
- Beobachtung: Kommunikation im implementing-scenario (und ggf. allen Prozessen) ist unnötig verbose.
- Entscheidung/Maßnahme: Aufgeschoben – Spike mit hoher Gefahr (Knappheit ↔ Subagent-Qualität), kein Schnellschuss. Plan: **Phase 1** an einem realen `implementing-scenario`-Lauf messen, *wo* die Tokens hingehen (Orchestrator→Subagent-Prompts vs. Subagent→Orchestrator-Reports vs. Narration); **Phase 2** nur die verbose Richtung straffen, qualitäts-gegated (Tests/Review/Mutation-Score). **Re-Trigger:** erst nach dem geplanten `implementing-scenario`-Umbau (mehrere Szenarien gleichzeitig) – wenn der stabil läuft (~5–10 Sessions); Backstop bis S105.
- **S109: Phase 1 durchgeführt** (23 Sessions mit Subagent-Einsatz, 112 Subagent-Logs, ~23,5M Zeichen ≈ 5,9M Token-Proxy; Zeichen als Proxy, es geht um Anteile). Verteilung: **Tool-I/O 82,5 %** (Subagenten 54,1 %, Orchestrator 28,5 %), Orchestrator-Narration 4,5 %, echte User-Eingaben 4,1 %, injizierte Skill-Texte 3,2 %, Subagent-Fließtext 2,9 %. **Orchestrator↔Subagent-Kommunikation gesamt: 8,6 %** – Task-Prompts 1,5 %, Task-Reports 0,6 %, `SendMessage` 6,6 %.
- **S109-Entscheid: VERWORFEN – die Prämisse trägt nicht.** Phase 2 hätte einen qualitätsriskanten Eingriff in die Subagent-Kommunikation bedeutet (Knappheit ↔ Ergebnisqualität, so im Plan benannt), um an 8,6 % zu sparen – während **`Read` allein 49,5 % des Gesamtvolumens** ausmacht. Das Kosten-Risiko-Verhältnis ist damit gemessen ungünstig, unabhängig davon, wie gut die Straffung gelänge. Der reale Treiber ist in OBS-S109-1 erfasst.
- **Methodische Warnung für spätere Messungen dieser Art** (drei Fehler, die in S109 nacheinander auffielen und das Ergebnis jeweils verschoben): (1) **Subagent-Logs liegen unter `<projekt>/<session-id>/subagents/agent-*.jsonl`**, nicht flach im Projektverzeichnis – ein Glob auf `*.jsonl` findet sie nicht und suggeriert, es gäbe keine Aufzeichnung; mit ihnen verdoppelt sich das gemessene Volumen. (2) **`role: user` ist nicht „vom Menschen getippt"** – geladene Skill-Texte werden als user-Message injiziert (bis 31k Zeichen pro Aufruf) und dominieren die Kategorie sonst. (3) **`SendMessage` ist Agent-Kommunikation**, nicht Werkzeug-I/O – wer es unter Tool-I/O führt, unterschätzt den Kommunikationsanteil um das Vierfache.

## OBS-S085-12 – Noise-Review skaliert nicht: Archive jede Retro neu zu filtern wird teuer
- Quelle: Agent
- Status: UMGESETZT (S109)
- Impact: GERING    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Skill-Nutzung
- Beobachtung: kaizen-Schritt 0 sah vor, alle Archiv-Dateien jede Retro neu gegen den Filter zu prüfen → Token-Kosten steigen, Grenznutzen gering.
- Entscheidung/Maßnahme: **B gewählt** — Staffel B (nur zuletzt archivierte Periode doppelprüfen) → (kein Rückfall) → A (Archiv-Scan weglassen). Umsetzung: kaizen Schritt 0 (bereits angewandt). Gekoppelt an CM „Noise als LL" (AKTIV + beobachten).
- **S109-Abschluss: als UMGESETZT geschlossen, ohne den geplanten Schritt B→A.** Staffel B läuft und ist im Skill verankert (`kaizen/SKILL.md`: „die **zuletzt archivierte Periode**"); das beobachtete Problem – *jede* Retro *alle* Archive neu zu filtern – existiert damit nicht mehr, über mehrere Retros hinweg ohne Rückfall. Der Weiterzug zu A (Archiv-Scan ganz weglassen) wurde bewusst **nicht** gegangen: Er wäre eine zusätzliche Sparmaßnahme ohne belegten Bedarf, erkauft mit dem Risiko, dass Noise im Archiv unentdeckt bleibt. Die Staffel war als Absicherung gedacht, nicht als Fahrplan, der bis zum Ende gegangen werden muss.

## OBS-S092-2 – Dokumentiertes Kommando zum Header-Lesen (statt eigenes Script)
- Quelle: User
- Status: VERWORFEN (Re-Trigger seit 14 Sessions nicht eingetreten; Nutzen gering, Kern zur unbearbeiteten Designfrage gewachsen)
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: TOOLING    Kontext: Doku/Hook/Script
- Beobachtung: Viele Doku-Dateien tragen im Header die Meta-Infos inkl. Schema/Format (z.B. lessons_learned, observations, adr, tech-debt). Agenten lesen sie ad-hoc (sed/Read), teils unvollständig. Es genügt ein **dokumentiertes Kommando-Pattern** mit bestehenden Tools (z.B. `sed -n '1,/^-->/p' <datei>` o.ä.), aufgenommen in den Startup-Hinweis bzw. die `--list`-Referenz – **kein eigenes Script** (Wartung) und **nicht** alle Header im Startup injizieren (zu teuer). Ggf. zweigeteilt (Metadaten vs. Schema), aber evtl. besser immer beides gemeinsam, da Schema ohne Metadaten selten nützt.
- Entscheidung/Maßnahme: Aufgeschoben – beim Drain zur Doku-Architektur-/Progressive-Disclosure-Designfrage gewachsen, kein Quick-Edit mehr: (1) welche Dateien brauchen überhaupt einen Header (vs. Name/Index erklärt sich selbst)? (2) was gehört in den Header (Leitfrage: *wann* liest ein Agent die Datei und *welche* Header-Info braucht er dann)? (3) In-Datei-Header vs. **Wiki-Struktur** (eigene Index-/Header-Dateien mit MD-Links). Der kleine Slice (sed-Pattern + Endmarker-Konvention `-->` vs. `---`) ist durch genau diese offenen Fragen blockiert. Re-Trigger: nächster Doku-Struktur-/`review-docs`-Durchgang.
- **S109-Entscheid: verworfen.** Der Re-Trigger ist seit dem letzten `review-docs`-Durchgang (S095, 14 Sessions) nicht eingetreten, und ein dritter Aufschub wäre reine Vertagung. Gegen den Kalt-Abwertungs-Bias geprüft („wäre der Punkt heute frisch beobachtet noch wertvoll?"): Nein – Agenten lesen die betreffenden Dateien ohnehin mit `Read` samt Header; ein separates Header-Kommando spart wenig, und die dahinter gewachsene Doku-Architekturfrage (welche Datei braucht überhaupt einen Header, In-Datei vs. Wiki) hat seit 17 Sessions keinen Bedarfsträger gefunden. Fällt der Bedarf doch an, entsteht er im Rahmen des Access-Layers (OBS-S096-3), der Lesen und Schreiben der Tracker-Dateien ohnehin neu ordnet – dort wäre er eine Facette, kein eigener Eintrag.

---

## OBS-S111-1 – gherkin-workshop fand die Konflikt-Variante eines Nebenläufigkeits-Szenarios nicht
- Quelle: User
- Status: UMGESETZT (S113)
- Impact: HOCH    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: gherkin-workshop
- Beobachtung: US-904 run-11 („Reaktivierung") kam mit vier abgenommenen Szenarien in die Implementierung. Eines davon deckt den Nebenläufigkeitsfall „Zutat wurde parallel bereits wiederhergestellt" ab – aber nur in der Variante, in der die parallel wiederhergestellte Zutat **dieselben** Daten trägt. Die Variante mit **abweichenden** Daten fehlte, obwohl sie fachlich die folgenreichere ist: dort überschreibt der Request stillschweigend fremde Werte (Lost Update), also ein Fall mit Datenwirkung und eigenem UI-Verhalten. Gefunden hat die Lücke der User beim Lesen der Implementierungs-Rückfragen – nicht der Workshop, nicht sein Review-Agent. Ohne den Zufallsfund wäre ein Contract entstanden, der fremde Daten ohne Hinweis überschreibt. Zu klären ist, warum die drei RE-Techniken (Example Mapping, State-Transition-Analyse, Input-Partition-Analyse) und der Review-Agent diese Variante nicht erzeugt haben; auffällig ist, dass der Workshop im übersehenen Punkt selbst eine Spur hinterließ – das abgenommene Szenario trägt den Kommentar „Einheit im Then bewusst nicht spezifiziert, weil im Parallelfall nicht kontrollierbar", also eine bewusst hingenommene Unbestimmtheit im Then genau an der Stelle, an der die fehlende Partition saß. Ob dieselbe Blindstelle andere Storys betrifft, ist offen.
- Entscheidung/Maßnahme: **Zwei Ebenen – Erzeugung und Netz.** Ursachenbefund beim Drain: Keine der drei Techniken hat eine Achse für *parallele Zustandsänderung*. Agent C partitioniert Eingabefelder, „paralleler Schreiber hat gleiche vs. abweichende Daten" ist keine Feld-Partition; Agent Bs Matrix ist `Quellzustand × Operation → Zielzustand` und kennt damit nur den Zustand VOR der Operation, nicht seine Veränderung währenddessen. Der CRITICAL-Punkt „Zustand aus der Zustands-Matrix nicht abgedeckt" im Review-Agenten läuft leer, wenn die Matrix die Variante nie enthielt. **(1) Erzeugung** – `references/agent-b-state-transition.md`: neue **Nebenläufigkeits-Regel**, analog zur dort bereits bestehenden Pending-Zustand-Regel formuliert. Für jede Transition, deren Vorbedingung zwischen Lesen und Schreiben veralten kann, sind drei eigene Prüfdimensionen zu decken: parallel mit denselben Daten geschrieben / mit abweichenden Daten geschrieben / parallel entfernt; „(a) abgedeckt" heißt ausdrücklich nicht „(b) abgedeckt", weil (b) der Lost-Update-Fall ist und eine explizite Entscheidung braucht (übernehmen, melden, ablehnen). **(2) Netz** – `references/agent-review.md`: neuer HIGH-Punkt **Unbestimmtheits-Detektor**. Lässt ein Then einen beobachtbaren Wert bewusst offen („nicht kontrollierbar", „bewusst nicht spezifiziert", „hängt vom Timing ab"), gilt das nicht als zulässiger Verzicht, sondern als Hinweis auf eine unpartitionierte Eingangsdimension – Dimension benennen, je Partition ein Szenario mit bestimmtem Then. Setzt genau an der Spur an, die der Workshop hier hinterlassen hatte, und greift über Nebenläufigkeit hinaus. **Warum beide:** (2) allein fängt nur, wenn bereits ein halb-unbestimmtes Szenario existiert – hier zufällig der Fall, aber keine Garantie; (1) allein hat kein Netz, wenn die Analyse erneut versagt. **Verworfen:** ein zusätzlicher Lost-Update-Prüfpunkt im Review-Agenten (redundant zu (1), und er läge zu spät in der Kette).
- Bezug: OBS-S108-2 (gemeinsam gelöst, gleiche Dateien – verschiedene Ursachen)

## OBS-S106-1 – Szenario-Clustering (Run-Generierung) modelliert Cross-Run-State-Abhängigkeiten nicht
- Quelle: User + Orchestrator
- Status: UMGESETZT (S113)
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: gherkin-workshop / scenario-clustering
- Beobachtung: Beim Einstieg in US-904 run-7 fiel auf, dass die Run-Generierung (gherkin-workshop Schritt 6, `.claude/skills/gherkin-workshop/references/scenario-clustering.md`) Cross-Run-**Zustands-Abhängigkeiten** nicht abbildet. Konkret der Soft-Delete-Lebenszyklus: (1) run-7 S3 „Soft-deleted Zutat erscheint nicht in der Liste" ist ein **Reader** von `DeletedAt`, aber **kein vorausgehender Run schreibt** `DeletedAt` (der DELETE-Writer ist run-8/run-10) → das E2E-Arrangement „existiert und gelöscht wurde" hat keinen echten Vordertür-Weg, erzwingt entweder einen Test-only-Endpoint oder das Vorziehen eines späteren Runs. (2) run-8 Sz.1 fordert „Then ist die Zutaten-Liste leer" nach dem Löschen – das **setzt run-7's GET-Filter voraus**, run-8 kann also nicht vor run-7. Das Clustering ordnet/splittet also einen Zustands-Lebenszyklus so, dass Reader vor Writer landen bzw. eine Reihenfolge entsteht, die eine echte Abhängigkeit verletzt. Kostete diese Session eine mehrrundige Design-Diskussion.
- Entscheidung/Maßnahme: **Neuer Schritt 5 „Zustands-Abhängigkeiten auflösen" in `references/scenario-clustering.md`.** Ursachenbefund beim Drain: Die Schritte 1–4 gruppieren rein strukturell (Capability → Ergebnisklasse → Form/Feld → Schicht); Zustands-Semantik kommt im Algorithmus nirgends vor, und die Reihenfolge-Regel in den Hinweisen war ausdrücklich „weich" mit genau einer harten Bedingung (Validierung nach Success desselben Endpoints). Schritt 5 erfasst je Cluster, welche Lebenszyklus-Zustände seine `Given` voraussetzen (Reader) und welche seine `Then` herstellen (Writer), operationalisiert über die Prüffrage *„Lässt sich sein `Given` mit dem, was bis zu diesem Lauf gebaut ist, über die Oberfläche herstellen?"*, und fordert Writer-Cluster vor Reader-Cluster desselben Zustands. **Entscheidend war ein beim Drain nachgeschobener Befund: Umordnen allein löst den S106-Fall nicht** – run-7 S3 braucht den DELETE-Writer aus run-8, run-8 Sz.1 braucht den GET-Filter aus run-7, die Abhängigkeit ist zirkulär und keine Reihenfolge erfüllt beide Seiten. Deshalb nennt der Schritt drei Auswege in fester Prüfreihenfolge: umordnen (einseitige Abhängigkeit), **Szenario verschieben** (Zyklus – das lesende Szenario gehört in den Lauf, der den Zustand schreibt, weil es die Wirkung dieser Mutation beschreibt und nicht die Grundfunktion des lesenden Endpoints), zusammenlegen (beide Cluster umkreisen dieselbe Mutation). Die Zustands-Bedingung ist zugleich als zweite **harte** Reihenfolge-Bedingung in den Hinweisen nachgezogen. **Verworfen:** nur die weiche Reihenfolge-Regel härten – hätte den Zyklus-Fall nicht auflösen können.
- Bezug: OBS-S106-2 (gemeinsam gelöst, gleiche Datei)

## OBS-S106-2 – Run-Planung flaggt Querschnitts-Policy-Rollout beim ersten Endpoint-Typ nicht vorab
- Quelle: Orchestrator + Subagent
- Status: UMGESETZT (S113)
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: gherkin-workshop / scenario-clustering
- Beobachtung: Dass run-10 den **ersten mutierenden Single-Resource-Endpoint** (DELETE) einführt und damit die Querschnitts-Policy ETag/If-Match/Optimistic-Concurrency (ADR-S058-1/-3) auslöst, wurde nicht in der Run-/Szenario-Planung sichtbar, sondern kam erst als PLANUNG-Eskalation des Backend-Subagenten mitten in der Implementierung hoch → mehrrundige Design-Diskussion über Scope (ETag jetzt vs. aufschieben), die vorab hätte eingeplant werden können. Verallgemeinert: Wenn ein Run den ERSTEN Endpoint eines Typs einführt (erster Single-Resource-Mutator; erste zweite Seite → Navigation; …), zieht das eine Querschnitts-Policy nach, die die feature-orientierte Clusterung nicht abbildet. **Zweite Ausprägung (S112), Szenario-Autorenschaft statt Run-Planung:** Dieselbe fehlende Unterscheidung trifft die Frage, in welche Feature-Datei ein Szenario gehört. Der Workshop läuft je User Story und legt Szenarien in der Story-Feature-Datei ab; für Querschnitts-Verhalten gibt es genau **eine** hartkodierte Ausnahme (Checklisten-Zeile „Erreichbarkeit (Navigation)" → `features/navigation.feature`, ADR-S103-1). Eine allgemeine Regel, wann ein entdecktes Verhalten querschnittlich ist und eine eigene Feature-Datei bekommt, existiert nicht. Folge in S112: Löschen-mit-Undo, Pending-Sperren und Toast-Bedienbarkeit landeten als US-904-Verhalten in `ingredients.feature`, obwohl keines davon zutatenspezifisch ist – sie wären in jeder Liste identisch zu fordern. Zusatzproblem, das die Ausnahme mitbringt: Eine querschnittliche Feature-Datei nutzt laut eigener Konvention „eine Seite als Vertreter" – wodurch gesichert ist, dass sich die übrigen Seiten ebenso verhalten, ist nirgends festgelegt.
- Entscheidung/Maßnahme: **Der Eintrag trug zwei verschiedene Mechanismen; beide adressiert, ein dritter Teil war bereits erledigt.** **(a) Erstmaligkeit** – neuer Schritt 6 „Erstmaligkeiten flaggen" in `references/scenario-clustering.md`: Je Lauf in der festgelegten Reihenfolge die Frage *„Was tut dieser Lauf, das noch kein Lauf zuvor getan hat?"*; führt er den ersten Vertreter einer Klasse ein (erster mutierender Single-Resource-Endpoint, erste zweite Seite, erste Liste mit Pagination …), wird die dadurch fällige Querschnitts-Policy beim Lauf benannt und **vor** dessen Implementierung geklärt, statt als PLANUNG-Eskalation mitten im Lauf hochzukommen. Bewusst als offene Frage statt als feste Klassenliste formuliert – eine solche Liste wäre nie vollständig. **(b) Querschnitts-Zuordnung** – neue **Ablage-Regel** in `SKILL.md` direkt hinter der UI-Verhaltens-Checkliste, die die bisher einzige, hartkodierte Ausnahme (Navigation) durch einen allgemeinen Test ersetzt: *Lässt sich Given/When/Then ohne Bezug auf die konkrete Entität formulieren, und würde es auf einer zweiten Seite identisch gefordert?* Beide ja → `@CROSS-<domain>`-Datei statt Story-Feature-Datei; das Tag-Schema existierte bereits (`docs/process/e2e-testing.md`), Navigation ist jetzt ein Beispiel der Regel statt ihre Ausnahme. **(c) Bereits erledigt, nur referenziert:** Das im Eintrag genannte Zusatzproblem („eine Seite als Vertreter – wodurch sind die übrigen gesichert?") wurde nach der Erfassung durch **ADR-S112-5** beantwortet (geteilte Implementierung, Import-Guard, parametrisierte Suite über ein Page-Object-Interface, Fähigkeits-Deklaration je Seite). Die Ablage-Regel verweist darauf, statt es neu zu regeln. **Bewusste Grenze:** Dieser Skill entscheidet nur über **neu entdeckte** Szenarien; der Umzug **bestehender** bleibt ADR-S112-5 Migrationsschritt (5) und ist dort an die zweite Seite gebunden.
- Bezug: OBS-S106-1 (gemeinsam gelöst, gleiche Datei); ADR-S112-5 (Nachweis-Schichten + Migration)

## OBS-S088-1 – Hook-Registrierung: ein Dispatcher je Matcher/Event statt Einzeleinträge
- Quelle: User
- Status: UMGESETZT (S113)
- Impact: GERING–MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Pro Tool-Matcher stehen mehrere Hook-Scripts einzeln in `settings.json` (PreToolUse `Edit|Write`: dependency-allowlist, code-quality-blocking, index-length, e2e-scenario-ref). Ein neuer/entfernter Check erfordert eine `settings.json`-Änderung → **Claude-Code-Reload** nötig, bevor er greift. `check-code-quality-blocking.py` ist bereits ein In-Process-Dispatcher (`CHECKS`-Liste + `checks/`-Package) – Checks dort sind reload-frei. Verallgemeinert man das (ein Dispatcher je Matcher *und* Event, der die Einzel-Checks aufruft), würde künftiges Hinzufügen/Entfernen eines Checks nur den Dispatcher-Inhalt ändern → sofort live, ohne Reload. Designpunkte: Pre (blocking, exit 2) vs. Post (non-blocking) getrennt; uneinheitlicher Input-Vertrag (Fragment-`HookInput` vs. voller Post-Edit-Inhalt + Datei-Reads bei e2e-scenario-ref → Dispatcher gibt rohes JSON, Checks adaptieren); Output-Stil je Dispatcher einheitlich (Bash nutzt JSON-`permissionDecision`); fail-open je Check.
- Entscheidung/Maßnahme: **Umgesetzt (S113-Drain) – auf User-Entscheid, nachdem die Kosten-Annahme des zweifachen Aufschubs empirisch nicht hielt.** Vorgeschichte: aufgeschoben (S102) bis S110 mit der Begründung, der Enabler-Zug sei entfallen, der Eigenwert gering (kein Poka-Yoke) und die Reload-Friktion selten. Beim S113-Drain zunächst zur Verwerfung empfohlen (Single-Point-of-Failure-Argument, plus die aus dem Eintrag übernommene Annahme uneinheitlicher Input-Verträge). **Der User widersprach der Aufwandseinschätzung, und die Prüfung gab ihm recht:** Alle sechs Scripts hatten bereits denselben Input-Vertrag (`json.load(sys.stdin)` → `tool_name` → `tool_input` → `file_path`); die im Eintrag behauptete Uneinheitlichkeit betraf nicht den Input, sondern die daraus abgeleitete Post-Content-Berechnung, die drei Scripts in fast identischer Form dupliziert hatten. Real unterschiedlich war nur der Blockier-Mechanismus (zwei Scripts JSON-`permissionDecision: deny`, vier `sys.exit(2)`) – eine ohnehin fällige Vereinheitlichung, kein Hindernis. **Umsetzung:** neuer `.claude/hooks/dispatch-edit-write.py`; Vertrag je Modul `check(data: dict) -> str | None`; stdin wird einmal im Dispatcher gelesen und als Dict durchgereicht (danach ist es konsumiert); `parse_input()` in `checks/common.py` nimmt optional ein vorgelesenes Dict. Jedes der sechs Scripts behielt sein `main()` und bleibt standalone lauffähig, weshalb alle bestehenden Tests unverändert grün blieben (272 vorher, 279 nachher – sieben neue Dispatcher-Tests). Blockier-Mechanismus vereinheitlicht auf `deny`; alle Checks laufen immer und ihre Gründe werden gesammelt ausgegeben, statt beim ersten Treffer abzubrechen (bisher sah man Verletzung 2 erst nach Behebung von 1). Fail-open je Check einzeln, damit ein defekter Check die übrigen nicht mitreißt – das entkräftet das Single-Point-of-Failure-Argument bis auf den Dispatcher-Rahmen selbst. `settings.json`: sechs Einträge → einer. Parität empirisch belegt (identischer Blockier-Grund bei einem realen Referenz-Verstoß, geprüft gegen das Einzel-Script). **Bewusst nicht gemacht:** die drei duplizierten `compute_post_content()` zusammenführen (YAGNI – der Reload-Nutzen hängt nicht daran, und an ihnen hängen Tests); ein Dispatcher über alle Events (nur dieser eine Matcher führte überhaupt mehrere Scripts, und Pre-/Post-Semantik gehören nicht in einen Prozess).
- Bezug: OBS-S085-16 (Reload-Friktion-Familie)

## OBS-S093-1 – SonarAnalyzer S125 feuert auf deutsche Kommentare mit Satz-Ende „;"
- Quelle: Agent
- Status: VERWORFEN (Schaden pro Vorkommen trivial, jede Gegenmaßnahme teurer als das Problem)
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Build/Analyzer
- Beobachtung: SonarAnalyzer S125 („Sections of code should not be commented out") interpretiert deutschsprachige Kommentare, die mit „…;" enden, als auskommentierten Code und bricht den Build. In dieser Session musste ein korrekter Erklär-Kommentar nur umformuliert werden, um S125 zu beruhigen – inhaltlich unnötiger Eingriff.
- Entscheidung/Maßnahme: **VERWORFEN – Schaden pro Vorkommen trivial, jede Gegenmaßnahme teurer als das Problem.** Der Kalt-Abwertungs-Prüfsatz wurde angewandt und trägt die Verwerfung nicht über den Zeitablauf: Auch frisch beobachtet bliebe der Schaden ein umformulierter Kommentar, einmalig, rund eine Minute; ein zweites Vorkommen ist in 20 Sessions nicht dokumentiert. Geprüfte Alternativen: S125 global abschalten (nimmt die Regel auch für echten auskommentierten Code aus dem Verkehr), S125 auf `warn` herabstufen (kollidiert mit `TreatWarningsAsErrors` und mit dem Befund, dass ein Wrapper Warnungen bereits als Fehlschlag meldet), Stilregel „deutsche Kommentare nicht mit ‚;' beenden" in die C#-Guideline (vergrößert genau die Pflichtlektüre, deren Kosten als größter Token-Posten belegt sind – `coding-guideline-csharp.md` liegt mit 694k gelesenen Zeichen unter den Top-5-Dateien). Bleibt der Workaround: umformulieren.

---

## OBS-S108-2 – gherkin-workshop-Checkliste deckt transiente Feedback-Elemente (Toast/Snackbar) nicht ab
- Quelle: User
- Status: UMGESETZT (S113)
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Gherkin
- Beobachtung: Die Vollständigkeits-Checkliste in `.claude/skills/gherkin-workshop/SKILL.md` (Zeilen ~155-157) fragt „Nach erfolgreicher Aktion", „Abbrechen" und „Feld-Initialisierung" ab – durchgehend dialog- und formularzentriert. Für transiente Feedback-Elemente (Toast/Snackbar) fragt sie nichts: weder Lebensdauer, noch wodurch sie verschwinden, noch was bei mehrfacher Auslösung kurz hintereinander passiert. „Klick außerhalb" kommt vor, aber nur als Abbrechen-Pfad eines Dialogs. In run-8 führte das dazu, dass der Undo-Toast als einzige Wiederherstellungsmöglichkeit im UI (UX-Guideline Prinzip 5) ohne jedes Szenario zu seinem Verhalten implementiert wurde. Erst der Review deckte drei beobachtbare Verhaltensaspekte auf, für die Szenarien fehlten (Klick daneben schließt den Toast; zweiter Toast erbt die Restlaufzeit des ersten und verkürzt das Undo-Fenster; nur der letzte Löschvorgang ist rückgängig). Zwei davon waren bereits implementiertes Verhalten ohne Spec, einer ein realer, im Browser reproduzierter Bug. Die Szenarien wurden nachträglich ergänzt – also in umgekehrter Reihenfolge zum Outside-In-Prinzip (ADR-S041-5). Aufgefallen ist die Lücke dem User, nicht dem Workshop und nicht den Review-Agenten. **Ursache in S112 genau lokalisiert – und weiter reichend als Toasts:** Die Checkliste selbst enthält den passenden Prüfpunkt („Async-Zustände & Sperren während Pending … **alle** konfliktträchtigen Kontrollen, nicht nur der Auslöser"). Ausgeschlossen wird er durch die Anwendbarkeits-Bedingung direkt über der Tabelle: „Prüfe jeden Punkt für jede Operation aus Schritt 0.A, **die ein Formular oder einen Dialog hat**." Löschen und Rückgängig haben weder Formular noch Dialog – Löschen ist ein IconButton in einer Listenzeile, Rückgängig ein Button im Toast. Betroffen sind damit nicht nur transiente Elemente, sondern **jede** Operation, die über Listen-/Zeilen-Bedienelemente ausgelöst wird. In S112 fehlten dadurch drei beobachtbare Verhaltensweisen ohne Szenario: „Rückgängig" ist während des laufenden Wiederherstellens nicht gesperrt, zwei gleichzeitige Löschvorgänge überschreiben sich, und der Toast ist auf Touch-Geräten nicht manuell schließbar.
- Entscheidung/Maßnahme: **Anwendbarkeits-Gate geöffnet + eigener Checklisten-Aspekt für transientes Feedback.** Die in S112 lokalisierte Ursache ist bestätigt: Die Bedingung über der Tabelle („für jede Operation …, **die ein Formular oder einen Dialog hat**") schloss listen- und toastbasierte Operationen komplett aus, samt der eigentlich passenden Zeile „Async-Zustände & Sperren während Pending". **(1)** Bedingung ersetzt durch „für **jede** Operation aus Schritt 0.A – auch ohne Formular und ohne Dialog (Bedienelement in einer Listenzeile, Button in einem Toast)"; trifft ein Punkt nicht zu, wird er über das bereits bestehende Notat-Schema als „Nicht relevant" abgehakt statt die Tabelle für die Operation still zu überspringen. **(2)** Neue Tabellenzeile **Transientes Feedback (Toast/Snackbar)** mit fünf eigenen Prüffragen: Lebensdauer; wodurch es außer durch Zeitablauf verschwindet; manuelle Schließbarkeit (auf Touch Pflicht – kein Hover, das die Zeit anhält); ob eine zweite Auslösung die Restlaufzeit der ersten erbt; auf welchen Vorgang eine Aktion im Toast wirkt, wenn mehrere kurz nacheinander liefen. **(3)** Der Klammerzusatz „Formular-/Dialog-Baseline" im Titel der Träger-Regel entfernt – er verengte die generelle Trägerfrage („liefert das Framework das Verhalten?") auf Formulare. Der Prinzip-8-Verweis bleibt im Regeltext stehen; „Formular-/Dialog-Baseline" ist der Anker von UX-Guideline Prinzip 8 (`coding-guideline-ux.md`) und wird aus `review-checklist.md` und `ux-ui-auditor.md` referenziert – dort unverändert. **Warum (1) nicht allein:** (1) bringt die Sperr-Zeile ins Spiel und deckt damit zwei der drei S112-Lücken, aber keine der toastspezifischen Fragen – Lebensdauer, Restlaufzeit-Erbe und manuelles Schließen stehen in keiner bestehenden Zeile.
- Bezug: OBS-S111-1 (gemeinsam gelöst, gleiche Dateien – verschiedene Ursachen)

---

## OBS-S112-1 – `tech-debt.md`-Feld „Behebung/Trigger" trägt zwei Bedeutungen in einem
- Quelle: User
- Status: UMGESETZT (S114)
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: tech-debt
- Beobachtung: Die Eintrags-Vorlage im Kopf von `docs/tech-debt.md` definiert das Feld als „<geplante Behebung **oder** auslösende Bedingung>". Ein Eintrag erfüllt die Vorlage damit bereits, wenn er nur beschreibt, *wie* behoben wird – ohne jede Angabe, *wann* das geschehen soll. Beim vollständigen Durchgang durch die Datei in S112 trat das mehrfach auf: Einträge trugen ausformulierte Behebungswege und als Auslöser entweder eine Formulierung, die keinen realen Zeitpunkt benennt („eigene UX-Foundation-Aufgabe", „bei der ersten Härtungs-/Resilience-Aufgabe" – solche Aufgaben stehen in keinem Plan), oder eine, die verfallen war, ohne je gefeuert zu haben („mit run-4", während alle Läufe der Story längst implementiert sind). Im selben Durchgang ist es dem Orchestrator beim Neuschreiben eines Eintrags erneut unterlaufen, obwohl das Muster kurz zuvor besprochen worden war. Risiko: Einträge sehen vollständig aus, obwohl niemand einen Zeitpunkt schuldet; sie bleiben unbegrenzt liegen, ohne dass beim Lesen etwas auffällt.
- Entscheidung/Maßnahme: **Umgesetzt (S114), gemeinsam mit OBS-S112-2 und OBS-S112-6** – alle drei betreffen dieselbe Datei und dieselbe Ursache: Das Eintragsformat kodierte die Fälligkeit nicht verbindlich. Das kombinierte Feld ist in `**Fällig:**` (wann) und `**Behebung:**` (wie) getrennt, das „oder" entfällt. Verifiziert vor der Entscheidung: Die im Eintrag zitierten Beispiele („mit run-4", „eigene UX-Foundation-Aufgabe") waren durch den S112-Durchgang bereits bereinigt – die Vorlage als Ursache stand unverändert. Abgesichert per Hook statt Lese-Disziplin, weil LL-S112-1 belegt, dass das Muster dem Orchestrator unmittelbar nach seiner Diagnose erneut unterlief. → CM-S114-1
- Bezug: LL-S112-1

---

## OBS-S112-2 – Das Prioritätsfeld in `tech-debt.md` steuert nichts
- Quelle: Orchestrator
- Status: UMGESETZT (S114)
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: tech-debt
- Beobachtung: TD-S089-1 trägt seit Session 089 die Priorität „Hoch" samt der Feststellung, dass das Branch-Coverage-Gate aus NFR/DoD dadurch wirkungslos ist. Beim Durchgang in S112 – rund 22 Sessions später – war der Eintrag unverändert und unbearbeitet, und seine technische Beschreibung zeigte auf einen Stack-Stand, den es längst nicht mehr gibt. Dieselbe Form zeigte sich außerhalb der Datei: `npm audit` meldete über mehrere Sessions hinweg Advisories, darunter vier für eine Produktions-Dependency, ohne dass daraus etwas folgte. Gemeinsam ist beiden, dass das Signal korrekt, sichtbar und dauerhaft vorlag – nur folgte keine Handlung. Risiko: Das Feld erzeugt den Eindruck einer Steuerung, die es nicht ausübt; „Hoch" und „Niedrig" unterscheiden sich im Ergebnis nicht.
- Bezug: OBS-S112-1
- Entscheidung/Maßnahme: **Umgesetzt (S114) – Feld ersatzlos gestrichen.** Am Bestand verifiziert statt aus dem Eintrag übernommen: Eine Suche über alle Skills, Hooks, Scripts und Prozessdocs fand **keinen einzigen Leser** des Feldes – `implementing-scenario` sichtet TD area-basiert (Schritt 0.5), nicht nach Priorität, und kein Script parst `tech-debt.md` überhaupt. Damit war es Dekoration, die eine Steuerung vortäuschte. Verworfen: das Feld behalten und ihm per Script einen Abnehmer bauen (Tooling für 19 Einträge, und es griffe OBS-S096-3 vor). Was es zu regeln vorgab, trägt jetzt `**Fällig:**`; die tatsächlich wirksame Steuerung ist die Kopplung `jetzt` → `AGENT_MEMORY.md`, die S112/S113 empirisch gefunden hatten. → CM-S114-1

---

## OBS-S112-6 – Verletzungen geltender Regeln werden als aufschiebbare Schuld geführt
- Quelle: Orchestrator
- Status: UMGESETZT (S114)
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: tech-debt
- Beobachtung: Drei Einträge in `docs/tech-debt.md` beschreiben keine bewusst aufgeschobene Schuld, sondern die Verletzung einer bereits geltenden Regel – und wurden trotzdem wie optionale Posten mit weichem Auslöser geführt. TD-S083-2 verletzt die Accessibility-Anforderung „Touch-Targets ≥ 44×44px" aus `nfr.md` und stand als UX-Politur mit dem Auslöser „eigene UX-Foundation-Aufgabe". TD-S083-4 wich von Guideline §2 ab und war als „kein Szenario, YAGNI" eingeordnet. TD-S089-1 hält fest, dass das Branch-Coverage-Gate aus NFR/DoD wirkungslos ist, und lag mit Priorität „Hoch" rund 22 Sessions unbearbeitet. Eine geltende Regel wartet auf keine Bedingung – sie ist erfüllt oder verletzt, und der einzig sinnvolle Zeitpunkt ist „jetzt". Risiko: Die Datei mischt zwei Sorten von Einträgen, deren Dringlichkeit sich grundsätzlich unterscheidet; die dringendere Sorte erbt dabei die Unverbindlichkeit der anderen und wird über viele Sessions mitgeschleppt, während die Anwendung die Regel weiter verletzt.
- Bezug: OBS-S112-1
- Entscheidung/Maßnahme: **Umgesetzt (S114) als stehende Regel im Datei-Header:** Verletzt ein Eintrag eine heute geltende Regel (NFR, Guideline, DoD), ist `**Fällig:** jetzt` – Regel 4. Soll sie doch warten, ist das eine Entscheidung über die *Regel* (ändern oder Ausnahme als ADR, so ADR-S083-2 für TD-S101-1), nicht über den Eintrag. Abgrenzung ergänzt, weil sie beim Durchgang gebraucht wurde: Ein noch **ungeprüfter Verdacht** ist keine Verletzung – dann ist die Prüfung selbst die Behebung (so bei TD-S112-2 entschieden). Verifiziert: Zwei der drei zitierten Beispiele waren durch S112/S113 bereits aufgelöst (TD-S083-2, TD-S089-1 terminiert), das dritte lebte – TD-S083-4 verletzt Guideline §2 (Kapselung; §2 nennt als Motivation genau dessen Signatur `restoreIngredient(id, name, defaultUnit)`) und wartete auf „die nächste Frontend-Story". Nach Regel 4 auf `jetzt` gestellt und in `AGENT_MEMORY.md` terminiert. Nicht mechanisch prüfbar, deshalb Header-Regel statt Hook-Check. → CM-S114-1

---

## OBS-S111-2 – ADR-Übergabe an Schicht-Subagenten skaliert nicht mehr mit der Zahl der ADRs
- Quelle: User + Orchestrator
- Status: UMGESETZT (S114)
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: implementing-scenario
- Beobachtung: `implementing-scenario` (Schritt 0 Punkt 4 und der Message-Block in Schritt 1–3) schreibt vor, die vollständige `--full`-Ausgabe von `decisions.py list --tag scope:cross-cutting` und `--tag story:us-NNN` in **jede** Subagenten-Message zu kopieren. In S111 gemessen: 74.311 Zeichen allein für `scope:cross-cutting` (60 ADRs) plus 22.655 für `resource:ingredients` – bei zwei Schicht-Subagenten pro Full-Stack-Lauf also grob 50k Tokens, von denen der weit überwiegende Teil mit dem Lauf nichts zu tun hat. Die Vorschrift stammt aus einer Zeit mit deutlich weniger ADRs und wächst monoton mit jedem weiteren Eintrag, während der pro Lauf tatsächlich relevante Anteil ungefähr konstant bleibt. In S111 wurde nach Rückfrage bewusst davon abgewichen (kompakte Gesamtliste + gezielt vollständige Auszüge), was den Konflikt zwischen Vorschrift und Praxis offenlegt statt ihn zu lösen.
- Entscheidung/Maßnahme: **Umgesetzt (S114).** Am Bestand geprüft statt aus dem Eintrag übernommen – und dabei widerlegt: Die Vorschrift wurde **nie befolgt**. Über 24 Schicht-Aufträge liegt der größte Subagenten-Prompt bei 11.099 Zeichen, der vorgeschriebene Voll-Dump allein wäre 101.722. Übergeben wurden stets handverlesene IDs plus `decisions.py get`. Der Kostenpunkt sitzt daher nicht in der Message, sondern in den Aufrufen des Orchestrators selbst (33× `list --full` gegenüber 19× kompaktem `list`); im Log war das unsichtbar, weil Ausgaben über ~60 KB ausgelagert werden. Kernbefund: `scope:cross-cutting` trägt 65 von 87 ADRs und trennt damit nichts, während jede ADR mindestens einen trennscharfen Tag hat und mehrere `--tag` sich schneiden. Maßnahme: `implementing-scenario` filtert `--full` nicht mehr auf `scope:`, sondern auf die fachlichen Dimensionen; in die Message geht der Volltext der bewerteten ADRs (der Orchestrator hat ihn ohnehin – IDs statt Text hätten den Subagenten einen Aufruf gekostet, nichts gespart) plus die Suchbefehle für seine unabhängige Gegenprobe. Verworfen: nur IDs übergeben (opfert die zweite Meinung), Voll-Dump beibehalten (wächst monoton). → CM-S114-2
- Bezug: OBS-S109-1

## OBS-S096-3 – Scripted-Access-Layer für TD/OBS/LL/Doc (Lesen/Schreiben, Metadaten listen/filtern/move)
- Quelle: User
- Status: UMGESETZT (S114)
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Doku/Script
- Beobachtung: Möglichst viel über Script(e) zugänglich machen: Lesen + Schreiben von TD/OBS/LL etc., idealerweise auch Lesen von Doc-Teilen; ein Auflisten aller Inhalts-Header/Metadaten (schneller Überblick + Suche), Filtern nach Metadaten (wie ADRs via `decisions.py`), ggf. Status-Update/Move wo passend. Vorher bewerten, wo es sich (besonders) lohnt. (`obs-drain.py`/`obs-archive.py` sind ein erster Schritt für OBS.) **Facette (aus OBS-S087-1 konsolidiert, S104):** technische Schuld durchsuchbar/relevanz-gefiltert machen – der Architektur-Check in `implementing-scenario` (oder ein Script) listet die zum bearbeiteten Code-Bereich potentiell relevante TD automatisch auf (kuratierte Bereichs-Keywords pro Eintrag).
- Entscheidung/Maßnahme: **Umgesetzt (S114), auf einen schmalen Zuschnitt.** Die S109-Reaktivierung stützte sich auf die ADR-Schreibseite – die Messung zeigt das Gegenteil: `docs/history` wird mit 74 % bereits am besten gezielt gelesen (`decisions.py` wirkt), während `docs/kaizen` mit 1.952k Zeichen zu **50 % erzwungener Vor-Edit-Read** ist und davon nur 23 % gezielt – für die Änderung eines Eintrags wird meist die ganze Datei gelesen. In Drain-Sessions steigt der Vor-Edit-Anteil auf 80 %. Gebaut: `obs.py` (get/add/set) und `lessons.py` (get/add) plus die Module `obs_entry.py`/`lessons_entry.py`. Zweiter, gleichrangiger Nutzen: **Form durch Konstruktion statt nachträglicher Prüfung** – `add` setzt das Entscheidungsfeld auf den einzigen zulässigen Erfassungswert, sodass ein Eintrag gar nicht erst in der Form entstehen kann, die `check-obs-capture.py` blocken müsste. Gemessen: ein Eintrag lesen kostet 1.418 statt 52.360 Zeichen (37×), bei LL 1.090 statt 23.530 (21×). Verworfen: der volle Access-Layer über TD/Doc (kein belegter Bedarf), und das Verwerfen des ganzen Eintrags (stand auf einer falsch gerechneten 9-%-Zahl). Bewusst offen gelassen: ob ein bestehendes Memory-System das besser löste, sobald mehr Zugriffs-Scripte entstehen. → CM-S114-2
- **S109-Reaktivierung (User):** Der beim S104-Aufschub fehlende **konkrete Abnehmer ist jetzt da** – und zwar gemessen statt vermutet. Die Phase-1-Messung (s. OBS-S109-1) zeigt: `docs/kaizen/observations.md` wurde über 23 Sessions mit **759k Zeichen** vollständig gelesen, `docs/history/adr.md` mit 303k, und die `adr.md`-Voll-Reads **steigen** trotz `decisions.py` (1,5k → 12,3k je Session), weil das Script zwar das Suchen abdeckt, nicht aber das Schreiben: Wer eine ADR ergänzt, muss die 1.263-Zeilen-Datei vorher lesen. Damit ist die Schreib-Seite des Access-Layers – beim S104-Aufschub noch als spekulativ eingestuft – als eigener Kostenpunkt belegt. Beide Backstop-Schwellen sind ebenfalls überschritten (`observations.md` 264 Zeilen > ~250). Der Bewertungsauftrag bleibt: **wo lohnt es sich besonders** – die Messung legt Schreib-/Ergänzungs-Operationen auf den großen Tracker-Dateien nahe, weil dort der erzwungene Vor-Edit-Read den eigentlichen Preis ausmacht.
- Bezug: OBS-S092-2 (Doku-Header lesen, geparkt); OBS-S096-2 (Skill-Mechanisierung, umgesetzt S104); OBS-S109-1 (Messung)

---

## OBS-S091-2 – Wrapper-Aufrufpfad cwd-relativ, kollidiert mit Projekt-Tooling-cwd
- Quelle: Agent
- Status: UMGESETZT (S115)
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Die Wrapper liegen im Repo-Root (`.claude/scripts/`) und lösen ihren Root intern via `_util.REPO_ROOT` auf — aber der **Aufrufpfad** `python3 .claude/scripts/foo.py` ist cwd-relativ. Projekt-Tooling (`npm`/`dotnet`/`vite`) zieht die Shell in `Client/`/`Server/`-Subdirs; der nächste Wrapper-Aufruf scheitert dann mit „No such file" (S091: beide Subagenten + Orchestrator betroffen).
- Entscheidung/Maßnahme: **Umgesetzt S115 – dem `cd` die Grundlage genommen, statt das Symptom zu reparieren.** Re-Trigger war eingetreten: in S111 (29.07., nach der `--prefix`-Freigabe) scheiterten vier Wrapper-Aufrufe aus `Client/` (stryker-frontend, vitest-run, check-bash-permission, dotnet-build). Die Recherche zeigte aber, dass der S109-Schluss unvollständig war, nicht falsch: Von den vier beobachteten cd-Gründen blockt der Hook drei längst – die npx-Direktaufrufe von Vitest und tsc sowie das ESLint-npm-Script laufen in WRONG_APPROACH, am 29.07. im denied-Log belegt. Offen war **allein** das typecheck-npm-Script. Dessen historische Ursache steht im Archiv (OBS-S091-Eintrag, Punkt b): Die `--prefix`-Form war damals geblockt, der Wechsel also erzwungen – seit S109 ist er es nicht mehr, der `cd` vom 29.07. war reine Gewohnheit. **Maßnahme:** `cd_npm_conflict()` in `check-bash-permission.py` – verlässt ein Segment den Repo-Root und nutzt ein späteres Segment npm, folgt deny mit Hinweis auf die `--prefix`-Form. Auf Segment- statt Regex-Ebene, weil `cd .` (auch der normalisierte bare-root) erlaubt bleiben muss. **Bewusst KEIN typecheck-Wrapper** (User-Einwand, am Bestand bestätigt): Der Erfolgsfall sind gemessene drei Zeilen, im Fehlerfall sind die tsc-Diagnosen bereits minimal – ein Wrapper hätte nichts zu kuratieren, und S099 hatte ihn aus genau diesem Grund schon verworfen. **Bewusst KEIN Hook-Rewrite** (`cd <root> &&`-Präfix): nach dem Befund unnötig, und er wäre die Umkehrung der bestehenden Pfad-Normalisierung im selben Hook. **Doku mitgezogen:** `dev-workflow.md` stellte sechs `cd Client &&`-npm-Befehle auf `--prefix` um; alle Varianten außer ci/update/audit-fix wurden real ausgeführt (der Build schreibt nach `../Server/wwwroot/` → beweist cwd=Client). **Restrisiko, bewusst offen:** `cd Client && grep …`/`cp …` bleiben erlaubt und wechseln ebenfalls das Verzeichnis – sie waren nie Ursache eines Fehlschlags, ein Deny darauf wäre unverhältnismäßig.
- Bezug: —

## OBS-S108-1 – Check 6 (`decisions.py`/`qa-check`) erkennt ADR-Referenzen nur mit `//` unmittelbar davor
- Quelle: Subagent (backend-layer-implementer, run-7)
- Status: UMGESETZT (S115)
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Check 6 (`decisions.py check` / `qa-check.py`) erkennt eine `ADR-SXXX-N`-Referenz nur, wenn ein `//` unmittelbar davorsteht (Kommentar am Zeilenanfang) – nicht, wenn zwei ADRs mid-line in einem Fließtext-/Prosa-Kommentar kombiniert werden. In run-7 blieben dadurch zwei in einem Kommentar kombinierte ADR-Referenzen zunächst unerfasst; sichtbar wurde es erst durch den qa-check-Rerun (ein zusätzlicher Lauf, kein Blocker). Risiko: eine real vorhandene ADR-Referenz bleibt unverlinkt/ungeprüft, wenn sie stilistisch in Prosa eingebettet statt als eigene `//`-Zeile geschrieben wird.
- Entscheidung/Maßnahme: **Umgesetzt S115.** Am Code verifiziert: `decisions.py` verlangte die ID unmittelbar nach dem Kommentar-Marker (Muster `//\s*ADR-…`), womit jede in Prosa eingebettete Referenz unsichtbar war – und unsichtbar heißt hier *gilt als nicht vorhanden*, also stilles Grün statt eines Befunds. **Maßnahme:** Logik in die testbare Funktion `adr_refs_in_line()` extrahiert – Kommentarbeginn suchen, dann ALLE IDs dahinter einsammeln. **Wirkung am Bestand belegt:** `decisions.py check` liefert jetzt Zeilen mit zwei Referenzen (`useDeleteIngredientWithUndo.ts:40` → ADR-S111-1 + ADR-S108-2; `useCreateIngredientWithReactivation.ts:42` → ADR-S004-1 + ADR-S111-1; `IngredientValidationError.cs:19` → ADR-S004-1 + ADR-S051-3), die vorher sämtlich unerfasst blieben. Exit 0, keine toten Referenzen – der Bestand war sauber, ist jetzt aber vollständig prüfbar, was auch die Rückrichtung („welche ADRs sind unverlinkt?") genauer macht. **Nebenbefund mitbehoben:** Für `decisions.py` existierten überhaupt keine Tests, obwohl es als qa-check-Schritt 6 läuft; 11 Tests in `tests/test_decisions.py` angelegt, die jetzt im Tooling-Gate mitlaufen. **Bewusst nicht erweitert:** Blockkommentare bleiben unabgedeckt – im Bestand wird ausschließlich der Zeilenkommentar verwendet. Kein echtes Kommentar-Parsing: Ein Marker in einem String-Literal könnte formal als Kommentarbeginn gelten, erzeugt aber nur bei einer gültigen ADR-ID dahinter einen Treffer, und die wäre dort ohnehin eine Referenz.
- Bezug: –

---

## OBS-S111-3 – Stryker-Wrapper meldet Survivors ohne Block-Ende und ohne Coverage-Angabe
- Quelle: Orchestrator
- Status: UMGESETZT (S115)
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: TOOLING    Kontext: Mutation-Testing
- Beobachtung: `format_mutant_group` in `.claude/scripts/_stryker_report.py` gibt pro Survivor genau drei Felder aus: `location.start.line`, `mutatorName` und `replacement`. Der Stryker-JSON-Report enthält daneben `location.end`, `location.start.column`, `coveredBy`, `killedBy` und `id` – die werden verworfen. Bei zeilenbezogenen Mutatoren (Statement, Equality, String) genügt die Startzeile; bei `Block removal mutation` ist sie strukturell mehrdeutig: Liegt die Zeile in einem `try`/`catch` mit verschachtelten Blöcken, geht aus „Zeile 304 → {}" nicht hervor, welcher der Blöcke entfernt wurde. Ebenso fehlt die Angabe, ob den Mutanten überhaupt ein Test abdeckt (`coveredBy` leer vs. gefüllt) – die Unterscheidung „Test deckt ab, tötet aber nicht" gegen „gar nicht ausgeführt" ist für die Reaktion entscheidend, steht im Report und geht in der Ausgabe verloren. In S111 eingetreten: Der Backend-Fix-Subagent schrieb für genau diese Felder zwei Wegwerf-Scripte unter `.claude/tmp/`; in derselben Session setzte der Orchestrator `jq` auf denselben Report an; und in einer früheren Session existierte bereits ein `.claude/tmp/check_stryker_scope.py` – drei Ad-hoc-Auswertungen desselben Reports über drei Sessions. Für die Wiedervorlage von OBS-S085-3 relevant: Dessen S115-Messung zählt nachgelagerte Filter auf Wrapper-Output (`| grep`, `| tail`) und würde diese Fälle nicht erfassen, weil sie als eigenständige Script-Läufe auftreten.
- Entscheidung/Maßnahme: **Umgesetzt S115 – mit einer Korrektur am Eintrag.** Widerlegt: Die Behauptung, die Unterscheidung „Test deckt ab, tötet nicht" gegen „gar nicht ausgeführt" gehe in der Ausgabe verloren, trifft nicht zu – `collect_undetected` trennt Survived und NoCoverage längst über das `status`-Feld in zwei separate Gruppen. Valide blieb der Rest, am echten Report verifiziert (Felder: coveredBy, id, killedBy, location, mutatorName, replacement, static, status, statusReason). **Maßnahme:** `format_mutant_group` gibt jetzt (a) die **Zeilenspanne** statt nur der Startzeile – das behebt die Mehrdeutigkeit bei Block-removal-Mutanten, den stärksten Punkt des Eintrags; (b) die **Anzahl deckender Tests** aus `coveredBy`, stumm wenn leer oder null (bei NoCoverage wäre „0 Tests" nur Rauschen); (c) `statusReason`, das im Eintrag nicht erwähnt war, aber im Bestand den Suppression-Grund aus dem Code trägt. 12 Tests in `tests/test_stryker_report.py` – die Funktion war zuvor ungetestet. **Fund aus dem Probelauf gegen echte Report-Objekte:** `statusReason` kann einen Assertion-Diff mit komplettem DOM-Dump enthalten, hunderte Zeilen pro Mutant. Die Fixtures der Tests zeigten das nicht. Ungekürzt hätte die Ergänzung eine Output-Explosion in genau das Script gebaut, dessen Ausgabe S109 gekürzt hat – daher `_status_reason()`: erste Zeile, auf 110 Zeichen gedeckelt, Kürzung mit Auslassungszeichen markiert. **Nicht übernommen:** `killedBy` (bei Survivors per Definition leer), `id` und `static` (kein belegter Bedarf).
- Bezug: OBS-S085-3

## OBS-S108-6 – `open-questions.md` hat keinen Lese-Trigger: Fragen werden abgelegt, nie vorgelegt
- Quelle: User
- Status: UMGESETZT (S115)
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: Alle Verweise auf `docs/open-questions.md` in Skills, Hooks und Prozessdocs sind **Schreib**-Verweise („dort eintragen"): `gherkin-workshop` legt nicht lösbare Fragen ab (Schritt ~292), `kaizen` und `closing-session` verweisen aufs Eintragen, `implementing-scenario` ebenso. Kein Prozessschritt liest die Datei, legt Einträge zur Klärung vor oder erzwingt eine Wiedervorlage. Alle anderen Tracker haben einen solchen Trigger: `tech-debt.md` wird in `implementing-scenario` Schritt 0.5 gesichtet und in 6.1 abgeglichen, `observations.md` treibt der Drain-Vorschlag am Session-Start, `lessons_learned.md` die Retro über den Jenga-Score. Folge im Bestand: OQ-S083-1/-2 liegen seit 25 Sessions offen, OQ-S094-1/-2 seit 14. Konkret in dieser Session: OQ-S083-1 fragt „ADR vs. technische Schuld: Taxonomie klären" – genau diese Abgrenzung wurde hier dreimal ad hoc neu verhandelt (ADR-S000-3 löschen statt Superseded; Undo-Toast-Touch-Punkt als TD statt OBS; CORS-Punkt als OBS statt OQ), ohne dass die offene Frage konsultiert wurde. Sichtbar wurde sie nur, weil der User sie beiläufig erwähnte. Anders als bei OBS-Einträgen (Feld `Status: IN BEOBACHTUNG bis S<NNN>`) gibt es im OQ-Format zudem kein Feld für einen Wiedervorlage-Termin.
- Entscheidung/Maßnahme: **Umgesetzt S115 – an den bestehenden Vorlage-Mechanismus angehängt statt einen neuen gebaut.** Am Bestand verifiziert: Alle fünf Verweise auf `open-questions.md` (kaizen, closing-session, gherkin-workshop, implementing-scenario, nfr.md) sind **Schreib**-Verweise; kein einziger legt Fragen vor. Alle vier Fragen lagen noch (OQ-S083-1/-2 ~32 Sessions, OQ-S094-1/-2 ~21). **Maßnahme:** `obs-drain.py` um die Sektion „Offene Fragen (Termin erreicht / überaltert)" erweitert – `parse_open_questions()` und `due_questions()`, max. 3 Einträge, älteste zuerst. Fällig ist eine Frage, wenn ihr **optionales** `Fällig: S<NNN>` erreicht ist oder sie ohne Termin ~10 Sessions alt wurde; ein gesetzter Termin **unterdrückt** die Alters-Regel, sonst wäre er wirkungslos. Liegende Fragen verhindern zudem das Verdikt „Backlog leer" – sonst blieben sie genauso unsichtbar wie zuvor. 10 Tests. **Warum kein eigenes Script mit eigener SessionStart-Injektion:** Der Drain-Vorschlag ist der vorhandene Vorlage-Weg, die Alters-Logik existierte dort schon, und die Script-Zahl wächst nicht weiter (OBS-S114-1). **Warum kein Pflichtschritt in closing-session:** Das wäre ein Lese-Trigger am Session-**Ende**, wo nicht mehr gehandelt wird. **Abgrenzung dokumentiert:** Offene Fragen sind kein Drain-Item – sie werden dem User zur Klärung vorgelegt, nicht im Drain entschieden (Skill-Schritt 1 ergänzt). Mitgezogen: `Fällig`-Feld im Format-Kommentar von `open-questions.md` samt aktualisiertem `wann-lesen`, Lane-Beschreibung in `process.md`. **Am echten Bestand belegt:** Der Vorschlag zeigt jetzt OQ-S083-1, OQ-S083-2 und OQ-S094-1.
- Bezug: –

---

## OBS-S112-8 – Lösungsfreie OBS-Erfassung erzwingen kostet mehr, als das eigentliche Ziel verlangt
- Quelle: User
- Status: UMGESETZT (S115)
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: Hook/Script
- Beobachtung: Die Erfassungsregel für neue OBS verbietet jede Lösungsangabe und wird von `check-obs-capture.py` mechanisch durchgesetzt (nur zwei erlaubte Werte im Feld `Entscheidung/Maßnahme`, abschließende Feldliste, Blockade bei Lösungs-Ansagen im Text). Das eigentliche Ziel ist aber enger als die Regel: Beim **Drain** sollen die möglichen Maßnahmen möglichst vollständig und möglichst unvoreingenommen erzeugt und bewertet werden. Die Regel setzt dafür an der Erfassung an – und trifft damit auch Fälle, in denen die Beobachtung vom User kommt und bereits eine konkrete Maßnahme benennt. Dann bleiben nur zwei Wege: die Angabe tilgen (Informationsverlust, die Begründung ist beim späteren Drain nicht mehr rekonstruierbar) oder den `obs-ok`-Marker setzen (Ausnahme wird zur Routine). In S112 trat genau das innerhalb einer Session zweimal auf – bei OBS-S112-7 und bei diesem Eintrag selbst, der die Regel beschreibt, an der er scheitern würde. Risiko: Eine Regel, deren Ausnahme regelmäßig gezogen werden muss, verliert ihre Bindungskraft, und der Marker wird zur Formalie statt zur bewussten Einzelfallentscheidung. <!-- obs-ok: Die folgende Zielrichtung stammt vom User als Auftraggeber, nicht aus agentenseitiger Vorwegnahme – und ihre Tilgung wäre genau der Informationsverlust, den dieser Eintrag beschreibt. --> Der User weist darauf hin, dass die Unvoreingenommenheit des Drains auch anders gesichert werden könnte als über die Erfassung, etwa indem der bewertende Schritt in einem Subagenten läuft, der ausschließlich die dafür nötigen Informationen erhält.
- Bezug: OBS-S112-7
- Entscheidung/Maßnahme: **Umgesetzt S115 – eigenes Feld `Vorprägung`, beim Standardzugriff verborgen.** Der Drain dieser Session lieferte eine Doppel-Evidenz, die beide Extreme ausschließt: Die im Eintrag konservierte Zielvorstellung des Users machte den Drain von OBS-S112-7 überhaupt erst handlungsfähig (ohne sie hätte der Plan neu erfunden werden müssen) – **und** derselbe, agentenformulierte Text hatte das Ziel verschoben (Nummerierung statt Navigation) und wurde als Auftrag gelesen, bis der User korrigierte. Tilgen und ungeprüftes Konservieren sind also beide falsch. **Verworfener Zwischenvorschlag (User-Einwand, zutreffend):** „eigenes Feld + Verifikationspflicht im Drain" hätte den Bias nicht verhindert, weil `get` den Volltext ausgibt – eine Pflicht *nach* dem Lesen kommt zu spät, eine Regel kann nicht ungelesen machen, was gelesen wurde. **Ebenfalls verworfen:** die Bewertung in einen Subagenten zu legen (teuerste Variante; der Orchestrator muss die Notiz zum Entscheiden ohnehin lesen und trägt den Bias dann doch). **Gewählt (User-Vorschlag):** ein **generelles** Feld für alles, was die Kandidatenbildung prägt – genannte Lösungen, vermutete Ursachen, Analogieschlüsse –, nicht ein Feld je Quelle. Es wird erfasst, beim normalen `obs.py get` aber **nicht ausgegeben**; stattdessen erscheint ein Hinweis mit dem Abrufbefehl `--vorprägung`. **Drei Absicherungen, alle end-to-end verifiziert:** (1) Standardzugriff verbirgt und weist hin; (2) `--vorprägung` gibt aus; (3) der Drain-Satz markiert betroffene Einträge mit `+Vorprägung` – ohne diesen Marker wäre ein verborgenes Feld so verloren wie ein getilgtes, nur unauffälliger. Dazu die Skill-Regel: erst eigene Kandidaten bilden **und dem User vorlegen**, dann abrufen, und den Inhalt gegen das tatsächliche Ziel verifizieren statt ihn als Auftrag zu lesen. Abgrenzung dokumentiert (Beobachtung = Ist-Zustand und Schaden; Vorprägung = Ursache, Bewertung, Lösung). `check-obs-capture.py` kennt das Feld als optional – ohne das hätte es jeden Eintrag geblockt. Der `obs-ok`-Marker bleibt nur für echte Einzelfälle. Mitgezogen: Format-Header in `observations.md`, Lane-/Bias-Absatz in `process.md`, Skill-Schritt 2. 12 neue Tests.

## OBS-S099-1 – Waisen-Infra-TD: Schuld ohne Lauf-Bezug bleibt uncaught
- Quelle: Orchestrator
- Status: UMGESETZT (S117)
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Sonstiges
- Beobachtung: Die S099-Lösung für OBS-S090-5 (TD-Sichtung in `implementing-scenario` Schritt 0 P5 + TD-Abgleich Schritt 6.1) fängt TD nur, wenn ein Lauf die betroffenen Bereiche real berührt (area-basiert – systematisiert den opportunistischen Fang, wie TD-S083-5 in S098). Infra-/Waisen-TD in Bereichen, die **kein** Lauf je anfasst, bleibt weiter uncaught. Der periodische Voll-Sweep wurde bewusst aus der Kaizen-Retro verbannt (Retro = Prozess, nicht Technik) → ein anderer Träger für einen periodischen TD-Sweep ist offen.
- Entscheidung/Maßnahme: Anker-Grammatik für **Fällig:** (td_anchors.py, erzwungen von check-td-capture.py) + Agenda-Modul td-due. Jeder TD-Eintrag braucht mindestens einen TERMINIERTEN Anker; US-NNN und ein Szenario ohne Lauf-Zuordnung terminieren nicht und verlangen einen Backstop – genau der Fall, in dem ein Eintrag verwaiste. td-due meldet eingetretene und defekte Anker, u.a. „Szenario implementiert, Schuld nicht mitgenommen". Verworfen: alters-basierte Lane (im Bestand wartet ein 73 Sessions alter Eintrag zu Recht; jede Schwelle ≤ 16 flaggte 15 von 17 Einträgen = Rauschgenerator). Alle 20 Einträge migriert, Zyklus TD-S090-2 ↔ TD-S101-1 dabei aufgelöst.
- Bezug: OBS-S090-5 (TD-Grooming, S099 umgesetzt); OBS-S087-1 (TD relevanz-filterbar)

## OBS-S112-3 – Kein anerkannter Weg für Infrastruktur-Arbeit ohne treibendes Szenario
- Quelle: User
- Status: UMGESETZT (S117)
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: TDD
- Beobachtung: Der Prozess verlangt für jeden Zweig ein ausübendes Szenario – Begründung ausbuchstabiert in TD-S110-1(c): vorab umgesetzt entstünde ein Zweig, den kein Szenario ausübt → Stryker-Survivor → Suppression außerhalb des treibenden Szenarios, genau die Konstellation, die ADR-S083-2 vermeiden will. Für querschnittliche Infrastruktur existiert jedoch keine Kategorie: Ein globaler Exception-Handler, ein Request-Body-Limit oder ein try/finally in einer Middleware werden von keinem Nutzer-Szenario getrieben. In S112 zeigte sich, dass vier solcher Punkte gemeinsam auf eine Aufgabe warteten, die in keinem Plan existiert. ADR-S106-3 kennt eine verwandte Ausnahme (Querschnitts-Protokoll-/Invarianten-Tests ohne US-Tag), sie deckt aber die Tests ab, nicht die Produktionsarbeit, die sie prüfen würden. Risiko: Infrastruktur-Härtung sammelt sich unbegrenzt an, weil der Prozess sie weder verbietet noch einen gangbaren Weg für sie beschreibt.
- Entscheidung/Maßnahme: Absatz „Infrastruktur-Arbeit ohne treibendes Szenario" in docs/process/tdd-process.md (Outside-In-Sektion): legitim wenn NFR/ADR/Guideline sie fordern; TDD unverändert, nur die äußere Schleife entfällt – die prüfbare Anforderung wird aus der fordernden Quelle abgeleitet, das RED liefert ein ausgewiesener Infra-Test nach ADR-S106-3. Verworfen: eigene Arbeitskategorie „Infra-Lauf" (Overkill, kein belegter Fall in dem das terminierte-TD-Vorgehen versagt hätte). Der Terminierungs-Teil der Beobachtung war bereits durch die S115-Fällig-Regeln erledigt.

---

## OBS-S116-2 – AGENT_MEMORY-Prioritäten tragen Volltext für alle Punkte, obwohl je Session nur einer bearbeitet wird
- Quelle: User + Orchestrator
- Status: UMGESETZT (S117)
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: Doku
- Beobachtung: Die Liste 'Nächste Prioritäten' in docs/AGENT_MEMORY.md umfasst neun Punkte und 6.395 Bytes; sie wird bei jedem Session-Start vollstaendig injiziert. Jeder Punkt traegt fuenf bis acht Zeilen Volltext-Begruendung, damit ein Agent ohne Vorwissen ihn anfassen kann - eine Anforderung, die bestehen bleibt. Bearbeitet wird pro Session aber hoechstens einer, und welcher, ergibt sich aus der Listenreihenfolge. Fuer die uebrigen Punkte wird die Detailtiefe also geladen, ohne gebraucht zu werden. Die Ansammlung selbst ist mechanisch erzwungen und sachlich richtig: tech-debt.md hat 22 Eintraege, davon genau drei mit 'Faellig: jetzt' (TD-S083-2, TD-S083-4, TD-S089-1), und check-td-capture.py koppelt 'jetzt' hart an einen AGENT_MEMORY-Eintrag; die uebrigen Punkte stammen aus dem S112-tech-debt-Durchgang und dem S115-Drain. Das Problem ist damit nicht die Anzahl offener Punkte, sondern dass Vorlage-Pflicht und Detailtiefe im selben Dokument zusammenfallen. Zusaetzlich verletzen die drei TD-Punkte die Kurzzusammenfassung-statt-Kopie-Regel: ihre Begruendung steht dort im Volltext statt als Verweis auf tech-debt.md.
- Vorprägung: Vom User bei der S116-Retro genannt: Details der Prioritaeten in eine andere Datei auslagern und im injizierten Dokument nur Kopf-Informationen fuehren - oder beim Injizieren nur die Kopf-Informationen einspielen. Detailtiefe braeuchte dann nur der jeweils naechste Punkt, fuer die uebrigen genuegen Kopf-Informationen.
- Entscheidung/Maßnahme: AGENT_MEMORY „Nächste Prioritäten" ist jetzt reiner Terminplan: Titel + Zeiger auf den besitzenden Tracker + Done-Kriterium + Fällig-Anker, kein Volltext (Format-Regel im Datei-Header). Nichts zog um – alles schrumpfte. Zusätzlich session-agenda.py: ein Marschbefehl im Volltext, alle übrigen Kandidaten als Stub mit Messwert plus Einzelabruf. Injektion am Session-Start 18.812 → 13.046 Bytes, gemessen. Verworfen: Abschnitts-Split blockierend/weitere (wäre ein zweiter Sumpf ohne Regeln) und Umzug der nicht-blockierenden Punkte in andere Tracker (docs/stories hat keinen Lese-Trigger – das hätte sie begraben).
- Bezug: CM-S083-3, CM-S086-1

## OBS-S111-4 – Bash-Hook blockt erlaubte Befehle, sobald sie verkettet, umgeleitet oder als Heredoc formuliert sind
- Quelle: Subagent + Orchestrator
- Status: UMGESETZT (S121)
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: `check-bash-permission.py` dokumentiert „Verknüpfung mit `|`, `||`, `&&`, `;` ist erlaubt – jedes Segment wird einzeln geprüft". In der Praxis scheitern regelmäßig Aufrufe, deren fachlicher Kern erlaubt ist: ein Heredoc (`python3 - <<'EOF'`) wird abgewiesen, ebenso `cat > datei <<'EOF'`, und ein Compound kippt vollständig, sobald ein einzelnes Segment nicht auf der Liste steht – auch wenn dieses Segment read-only ist. In S111 dreimal eingetreten: Der Frontend-Implementierer meldete es unaufgefordert als Reibung (`git stash`, Redirect-Ziele) und wich auf den bereits gelesenen Transcript-Zustand aus; der Backend-Fix-Subagent musste seine Wegwerf-Auswertung über zwei zusätzliche `Write`-Aufrufe umleiten; der fortsetzende Orchestrator lief beim Aufräum-Check (`ls … && git check-ignore …`) in dieselbe Sperre. Die Folge ist keine Blockade, sondern ein Umweg: Agenten bauen Ersatzkonstruktionen, die dasselbe Ergebnis liefern. Damit misst das Deny-Log an dieser Stelle nicht abgewehrte Absichten, sondern Formulierungsvarianten – und die Umwege kosten Tool-Aufrufe, ohne dass ein Sicherheitsgewinn entsteht. **Zweite Ausprägung, andere Ursache (S115): Erwähnung wird als Aufruf gewertet.** Die Wrapper-Zwang-Regeln matchen den Befehls*text*, ohne zu unterscheiden, ob ein Wrapper ausgeführt oder nur genannt wird. In S115 dreimal eingetreten, jedes Mal in reiner Recherche *über* die Wrapper: eine Pickaxe-Suche in der git-Historie, deren Suchmuster einen Wrapper-Namen enthielt; eine Log-Suche nach demselben Namen; und schließlich ein Tracker-Schreibzugriff, dessen **Beschreibungstext** die Namen zitierte – eine Dokumentation über Tooling galt damit als Umgehung des Tooling-Zwangs. Jeder Fall kostete eine Runde plus einen Umweg über ein tmp-Script. Bemerkenswert am dritten Fall: Er trifft strukturell jeden Drain, der Tooling-Befunde festschreibt. Die trennscharfe Abgrenzung existiert im Projekt bereits – `tool-usage.py` zählt ausdrücklich nur Wrapper-*Ausführungen* und nimmt Datei-Inspektion aus. **Weiterer Datenpunkt (S116-Retro, vier Denies in Folge bei rein lesenden Analysen):** Zwei zeigen eine bislang nicht notierte Ausprägung – geblockt wurde nicht der Befehl, sondern ein **Suchmuster im Argument**: ein grep nach dem Literal 'npm run <script>' in einer Markdown-Datei galt als npm-Aufruf, eine Volltextsuche nach 'npx vitest' in Session-Logs als Vitest-Start. Der Hook prüft den rohen Befehlstext und trifft damit auch Zitate von Befehlen, die gerade untersucht werden sollen. Ein dritter Deny betraf eine for-Schleife über zwei Dateien, deren Rumpf nur ein erlaubtes grep enthielt. Der vierte traf den Versuch, genau diesen Absatz per obs.py zu schreiben: Der beschreibende Text enthaelt die Zeichenkette und wurde deshalb als Vitest-Start gelesen – das Problem laesst sich also nicht dokumentieren, ohne selbst darueber zu stolpern (dieser Eintrag entstand per --allow-once). Alle vier waren durch Umformulieren aufloesbar; Kosten je Vorfall ein zusaetzlicher Roundtrip. **Dritte Ausprägung, neue Ursache (S117): nicht die Formulierung, sondern der Ort.** Der Hook verlangt Repo-relative `python3`-Pfade; das Scratchpad-Verzeichnis der Harness liegt strukturell ausserhalb des Repos. Ein Wegwerf-Script dort ist damit ohne `--allow-once` gar nicht aufrufbar – beide Vorgaben sind einzeln richtig und zusammen unerfuellbar, ein Umformulieren gibt es hier nicht. Ausweichweg war `.claude/tmp/` im Repo plus manuelles Loeschen. Vierter Formulierungs-Deny derselben Session: Prozess-Substitution (`diff <(…)`) faellt wie das bekannte Heredoc aus dem Segment-Parsing.
- Entscheidung/Maßnahme: Umgesetzt in check-bash-permission.py. Splitter zerlegt jetzt auch: Newline als Segmenttrenner, Heredoc-Bodies als Daten (strip_heredoc_bodies), Zuweisungspraefixe, $()/Backtick/Prozess-Substitution, for/while-Rumpf, find -exec und xargs (expand_segment) – jedes Teilstueck wird einzeln geprueft. Scratchpad ist Schreibziel und python3-Ort, .claude/tmp/ nicht mehr. String-Argumente nicht-ausfuehrender Befehle werden vor der Wrapper-Pflicht maskiert (mask_data_strings). Neu erlaubt: awk, printf, date mit Argument, xargs generisch. Neue Sicherheitsnetze: indirekte Ausfuehrung blockt hart, Datei-Operationen im Schleifenrumpf und in -exec/xargs blocken ohne Eskalation, kein prueffaehiges Kommando bedeutet deny. Verworfen: Freigabe von python3 -c (kein verlaesslicher Weg, lesende von schreibenden Scripten zu trennen) und Verschaerfung von mv/cp auf Projektziele (User: bisher kein Problem, git als Netz). Messung ueber die Logs seit S096: von 214 harten Denies waeren 57 jetzt erlaubt; 30 von 3147 Allows blocken neu, davon 18 gewollte tmp-Redirects. Dabei aufgedeckt und geschlossen: ohne Newline-Trenner erlaubte der Hook jeden mehrzeiligen Befehl komplett, sobald die erste Zeile ein Muster traf. Gegenprobe je Freigabe als Guard-Test plus Live-Probe.
- Bezug: OBS-S085-3

## OBS-S120-4 – Für Textersetzung über mehrere Dateien gibt es kein Werkzeug – jedes Mal entsteht ein Wegwerf-Script
- Quelle: Orchestrator
- Status: VERWORFEN (Werkzeug nicht noetig - Disziplinfrage, und der S120-Schaden war ein Baseline-Fehler)
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: In S120 war dreimal dieselbe Tätigkeit nötig: dieselbe Zeichenkette in mehreren Dateien ersetzen (DefaultUnit → BaseUnit über zehn Stellen in Client/, das Entfernen eines mehrzeiligen OQ-Eintrags, das Prüfen des Rename-Ergebnisses). Jedes Mal entstand dafür ein Wegwerf-Script unter .claude/tmp/. Die vorhandenen Werkzeuge decken den Fall nicht ab: Edit arbeitet je Datei, replace_all wirkt nur innerhalb einer Datei, und der Bash-Weg über eine Schleife wird von check-bash-permission.py geblockt – dessen Hinweistext nennt das Wegwerf-Script ausdrücklich als vorgesehenen Ausweg. Das ist als Poka-Yoke gegen unkontrollierte Massenoperationen sinnvoll, lässt aber offen, dass die dahinterliegende Tätigkeit legitim, häufig und immer gleich geformt ist. Kosten je Vorkommen: Script schreiben, ausführen, Ergebnis prüfen, Datei wieder löschen – dazu die Fehlerquelle, die in S120 auch zuschlug, nämlich dass das Prüfscript gegen die falsche Baseline verglich (HEAD statt des freigegebenen Blobs) und ein falsches Ergebnis meldete. Das Muster ist älter als S120: In `.claude/tmp/` liegen unter anderem sechs durchnummerierte Varianten `grepdll.py` bis `grepdll6.py` aus einer einzigen Session – dass die Wegwerf-Scripte dort liegenbleiben und nummeriert weiterwachsen, zeigt, dass sie iterativ zurechtgebogen statt einmal geschrieben werden.
- Entscheidung/Maßnahme: User-Entscheidung (M1): Ein replace-across.py haette den S120-Schaden nicht verhindert, denn der entstand nicht beim Ersetzen, sondern beim Pruefen gegen die falsche Baseline (HEAD statt freigegebener Blob). Gegen das Werkzeug sprachen drei Einwaende des Users: es erzeugt keine Pruef-Disziplin, es muss erst gelernt werden, und es ist unflexibler als Bash – belegt durch grepdll.py bis grepdll6.py, also ein starres Wegwerf-Script, das iterativ zurechtgebogen wurde. Der Weg bleibt: grep -rn zum Sichten, sed -i per --allow-once, git diff --stat zur Gegenprobe. Wird daraus ein Muster, wird neu entschieden. Teilweise entschaerft durch die S121-Aenderungen aus OBS-S111-4: Schleifen mit lesendem Rumpf und Wegwerf-Scripte im Scratchpad brauchen keinen Umweg mehr.

## OBS-S119-2 – Fuenf PreToolUse-Hooks tragen identischen Boilerplate; Beispiel-IDs im Tooling kollidieren mit dem Dangling-Check
- Quelle: Subagent
- Status: UMGESETZT (S121)
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: TOOLING    Kontext: Hook/Script
- Beobachtung: Zwei zusammenhaengende Befunde aus dem S119-Review. (a) Duplikation: read_file_text() ist in check-obs-capture.py, check-td-capture.py, check-ref-direction.py, check-adr-capture.py und check-dangling-refs.py byte-identisch; compute_post_content() in drei Modulen identisch und in zwei weiteren fast identisch; main() in allen fuenf bis auf den geloggten Modulnamen wortgleich. In Summe ueber 100 Zeilen Copy-Paste. Die drei in S119 neu gebauten Hooks (check-adr-capture.py, check-dangling-refs.py, check-oq-capture.py) loesen das nicht auf, sondern schreiben es fort – der Bestand waechst damit von fuenf auf sechs Kopien. Eine kuenftige Aenderung am Fail-open-Verhalten (Exit-Code, stderr-Format) muss fuenfmal nachgezogen werden. (b) Beispiel-IDs: check-td-capture.py, .claude/scripts/td_anchors.py und mehrere Testfixtures verwenden TD-S089-1 als illustratives Beispiel im Anker-Vokabular. TD-S089-1 ist ein echter, aktiver Eintrag in docs/tech-debt.md mit Faelligkeit jetzt. Sobald er regulaer erledigt und geloescht wird, blockiert der neue check-dangling-refs.py diese Loeschung und listet neben den zwei echten Referenzen in .claude/scripts/dotnet-test.py rund acht irrelevante Beispieltext-Stellen auf, die einzeln mit dangling-ok quittiert werden muessen. Der Autor von check-dangling-refs.py war sich der Gefahr fuer die eigene Datei bewusst und nutzt dort bewusst IDs aus dem nicht vergebenen S001-Raum; auf die uebrigen Tooling-Dateien wurde diese Disziplin nicht angewendet.
- Vorprägung: Der Reviewer schlug fuer (a) ein gemeinsames Modul mit read_file_text, compute_post_content und einem run(check_fn, prefix)-Wrapper vor, wobei die Standalone-Lauffaehigkeit der Module erhalten bliebe. Fuer (b) schlug er vor, entweder die Beispiel-IDs im Tooling auf einen nicht vergebenen Nummernraum umzustellen oder den Einmalaufwand vor dem Schliessen von TD-S089-1 einzuplanen.
- Entscheidung/Maßnahme: Beide Teile umgesetzt, beide Behauptungen des Eintrags vorher am Code geprueft und korrigiert. (a) Duplikation: read_file_text und compute_post_content nach .claude/hooks/_hook_io.py extrahiert, die fuenf capture-Hooks importieren daraus. Redundanz 99 auf 35 Zeilen (3 auf 1 Prozent). Der Eintrag behauptete zusaetzlich, main() sei in allen fuenf wortgleich – das ist falsch, es gibt 11 Varianten in 12 Dateien; die Vorpraegung baute mit ihrem run(check_fn, prefix)-Wrapper auf derselben falschen Annahme auf und wurde deshalb nicht uebernommen. Bewusst nicht zusammengelegt: die abweichende compute_post_content-Variante in check-ref-direction und check-e2e-scenario-ref, sie hat eine andere Signatur. Zunaechst wollte ich read_file_text als trivial ausklammern; auf Nachfrage des Users verworfen, weil der Kopplungspreis durch das ohnehin entstehende Modul schon bezahlt ist und eine halbe Extraktion Willkuer hinterliesse. (b) Beispiel-IDs: geloest ueber _SKIP_PREFIXES in check-dangling-refs.py – Tooling-Testverzeichnisse werden nicht mehr gescannt, weil IDs dort Fixtures sind und keine Verweise. Der Eintrag nannte nur TD-S089-1; gemessen waeren 8 der 30 aktiven TD-/OQ-Eintraege blockiert gewesen, im schwersten Fall 34 Fundstellen ohne einen einzigen echten Verweis. Nach der Aenderung: 0 blockierte Eintraege, echte Verweise aus Produktionsscripten bleiben erhalten. Verworfen wurde B1 (Beispiel-IDs auf reservierte Nummernraeume umstellen): 50 Fundstellen Aufwand, und beim naechsten neuen Fixture laeuft es wieder auf. Verifikation: 662 Tests gruen, zwei neue Guard-Tests (Fixture blockt nicht, echter Verweis blockt weiter), plus Live-Probe – alle fuenf Hooks als Script aus fremdem Arbeitsverzeichnis lauffaehig und der Dangling-Check blockt weiterhin mit exit 2.

## OBS-S099-2 – Test-Freigabe-Anker verlangt manuelle Zustandshaltung im Orchestrator
- Quelle: Orchestrator
- Status: VERWORFEN (bewusster Trade-off, Alternative waere unsicherer)
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: implementing-scenario / qa-check
- Beobachtung: Die S099-Lösung für OBS-S090-4 (Blob-Anker-Audit) verlangt vom Orchestrator mehrstufige manuelle Schritte: pro freigegebener Test-Datei `git hash-object -w`, die `pfad=sha`-Paare über den GREEN/REFACTOR-Zyklus hinweg im Kontext halten und in Schritt 4 an `qa-check --verify --approved-tests` durchreichen. Bewusster Trade-off (mechanischer Gate statt „dran denken"), aber die manuelle Zustandshaltung ist selbst vergessbar/fehleranfällig – nur der `--verify`-Abbruch bei geänderten Tests ohne `--approved-tests` fängt das Weglassen.
- Entscheidung/Maßnahme: User-Entscheidung R1. Die vorgeschlagene Alternative R2 (qa-check legt die Freigabe-Hashes in einer Datei ab, statt dass der Orchestrator sie mitfuehrt) wurde vom User verworfen, und der Einwand ist staerker als die urspruengliche Einordnung: Die Schutzwirkung des Anker-Verfahrens beruht darauf, dass der ORCHESTRATOR den Wert haelt, nicht der gepruefte Subagent. Eine Datei im Arbeitsbaum kann der Subagent selbst ueberschreiben – der Anker pruefte sich dann gegen einen Wert, den der Gepruefte gesetzt hat. R2 haette den Mechanismus nicht bequemer gemacht, sondern entwertet. Die manuelle Zustandshaltung bleibt damit der bewusste Preis fuer einen faelschungssicheren Gate; das vorhandene Netz (qa-check --verify bricht ab, sobald ein Lauf Test-Dateien beruehrt und --approved-tests fehlt) faengt den praktisch relevanten Fall. Impact war ohnehin als GERING eingestuft. Kein erneutes Aufschieben: der Eintrag lag rund 22 Sessions in der Alters-Lane, eine dritte Vertagung waere die eigentliche Fehlentscheidung gewesen.
- Bezug: OBS-S090-4 (S099 umgesetzt); CM-S070-1

---

## OBS-S117-4 – Offene Fragen haben eine Vorlage, aber keinen erzwungenen Ausgang
- Quelle: User
- Status: UMGESETZT (S121)
- Impact: MITTEL    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: Skill-Nutzung
- Beobachtung: Offene Fragen in docs/open-questions.md werden seit S115 jede Session vorgelegt, aber ihr Nicht-Entscheiden hinterlaesst keine Spur. OBS kennen drei erzwungene Ausgaenge (umsetzen / verwerfen / aufschieben mit Pflicht-Wiedervorlage), TD seit S117 eine Anker-Grammatik mit Terminierungspflicht. OQ kennen nur "bei Klaerung entfernen": Wird eine vorgelegte Frage nicht beantwortet, wird nichts festgehalten - kein Grund, kein neuer Termin, kein Vermerk, dass sie gesehen wurde. Sie erscheint in der naechsten Session unveraendert wieder, und die Wiederholung ist von der ersten Vorlage nicht unterscheidbar. Belegt am Bestand: OQ-S083-1/-2 liegen seit rund 34 Sessions, OQ-S094-1 seit rund 23; seit S115 wurden sie in jeder Session vorgelegt und sind jedes Mal ohne Vermerk vorbeigezogen, zuletzt in S117. Verstaerkend, aber nicht ursaechlich: In session-agenda.py ist open-questions ein reines Stub-Modul und beansprucht die Naechste Aufgabe nie. Das ist richtig so - eine 34 Sessions alte Frage darf keine laufende Story verdraengen -, hat aber zur Folge, dass es keinen Zeitpunkt gibt, an dem die Klaerung Vorrang bekommt. Abgrenzung zu Geloestem: Der fehlende Lese-Trigger ist behoben (OBS-S108-6, umgesetzt S115) und ein optionales Faellig-Feld existiert seither. Die Luecke ist der fehlende Entscheidungszwang, nicht die fehlende Vorlage. Bis S117 stand dieser Befund nur als Nebensatz in OBS-S117-2, dessen Thema die Uebergabe injizierter Bloecke an den User ist - bei dessen Aufloesung waere er mit ins Archiv gewandert.
- Entscheidung/Maßnahme: P2: **Fällig** ist bei offenen Fragen jetzt Pflicht – check-oq-capture.py blockt neue und geaenderte Eintraege ohne Anker, Header von open-questions.md nachgezogen. Der Eintrag war bei der Behandlung zu grossen Teilen ueberholt: Seit S119 nutzen offene Fragen dieselbe Anker-Grammatik wie Tech-Debt, check-oq-capture.py erzwingt die Gueltigkeit eines GESETZTEN Ankers, und die im Eintrag genannten Belege (OQ-S083-1/-2, rund 34 Sessions offen) wurden in S118 geklaert. Uebrig blieb genau eine Luecke: Das Feld war optional, wer es weglaesst faellt auf die Alters-Regel zurueck – belegt an OQ-S094-2, das ohne Termin seit 27 Sessions in jeder Session vorgelegt wird, ohne dass die Wiederholung von der ersten Vorlage unterscheidbar waere. Verworfen: P3 (Vermerk 'Zuletzt vorgelegt: SNNN' beim Session-Abschluss) – erzeugt Buchhaltung ohne Konsequenz; das Problem ist der fehlende Entscheidungszwang, nicht die fehlende Sichtbarkeit. Die Alters-Regel in open_questions.py bleibt als Netz fuer Bestandseintraege. Gegenprobe am Hook: Frage ohne Faelligkeit blockt, Frage mit gueltigem Anker geht durch; 662 Tests gruen.
- Bezug: OBS-S117-2

## OBS-S110-2 – `implementing-scenario` Schritt 4 hat keinen Weg, wenn der Schicht-Subagent nicht zurückkehrt
- Quelle: Orchestrator
- Status: VERWORFEN (Wiederaufnahme geregelt, Restschaden zu selten fuer den Pruefaufwand)
- Impact: MITTEL    Häufigkeit: häufig
- Kategorie: PROZESS    Kontext: Agent-Prompt
- Beobachtung: Schritt 4 („Mechanische Verifikation") ist vollständig darauf aufgebaut, dass der Schicht-Subagent in seinem Return einen frischen `=== VERIFIKATIONS-HASH ===`-Block liefert, den der Orchestrator per `qa-check.py --verify` prüft. Der Skill beschreibt keinen Fall, in dem dieser Return ausbleibt, weil der Subagent-Prozess endet, bevor er antworten konnte. In S110 eingetreten: ein WSL-Absturz beendete Orchestrator und Subagent gleichzeitig; nach dem Neustart lagen fertiger Produktionscode und ein durchgeführter Refactor im Working Tree, aber kein Hash und keine Aussage darüber, welche Schritte noch offen waren. Der Zustand ließ sich nur rekonstruieren, weil der Test-Freigabe-Anker als git-Blob außerhalb des Agentenkontexts persistiert war und der Refactor-Diff sich nachträglich dagegen auditieren ließ. Risiko: Ohne beschriebenen Weg improvisiert jeder Orchestrator anders – im schlechteren Fall wird der Subagenten-Stand ungeprüft übernommen oder der ganze Lauf verworfen und neu begonnen. **Zweiter Vorfall (S111), andere Ursache, neuer Schadenstyp:** Diesmal kein Absturz, sondern das Session-Limit – es beendete Orchestrator und **beide** Nachbesserungs-Subagenten innerhalb weniger Minuten. Der Backend-Agent hatte seine Arbeit vollständig abgeschlossen und alle Checks grün, kam aber nicht mehr zum Absenden; der Frontend-Agent stand im laufenden `qa-check`. Neu gegenüber S110 ist die Art des Schadens: Beide Aufträge trugen die Auflage „keine neue ADR anlegen – melde mir im Return, was dokumentiert gehört". Mit dem Return ging diese Meldung verloren, und im Produktionscode blieb ein Kommentar zurück, der auf ein ADR-Addendum verwies, das nie geschrieben wurde. Dieser tote Verweis wäre in den Commit gegangen; der Verifikations-Hash hätte ihn nicht aufgedeckt, weil Code, Tests und Stryker grün waren, und auch `qa-check` Check 6 nicht, weil die referenzierte ADR-ID existiert – nur der Abschnitt darin nicht. Die Rekonstruktion gelang, weil die Subagenten-Logs vollständig persistiert sind, kostete aber rund 15 Aufrufe, bevor überhaupt feststand, welche Arbeit noch offen war. Bemerkenswert: Die Auflage „keine ADR selbst anlegen, stattdessen im Return melden" macht den Return zur einzigen Brücke für eine Doku-Pflicht – fällt er aus, verschwindet die Pflicht spurlos, während der Code den Verweis darauf behält.
- Entscheidung/Maßnahme: User-Entscheidung Q1. Der erste Teil des Eintrags ist geloest: implementing-scenario beschreibt inzwischen den Fall 'gar kein Signal' – mechanisch am Arbeitsbaum pruefen (git status/diff, gezieltes grep) statt passiv warten, und den Verifikationslauf notfalls selbst fahren. Der zweite Teil (der Return ist der einzige Traeger einer Doku-Pflicht, faellt er aus, verschwindet die Pflicht spurlos) bleibt formal offen. Q2 – die Pflicht sofort als Datei ablegen statt im Return zu melden – wurde vom User verworfen, und der Einwand traegt: Ob ein sterbender Prozess eine Antwort nicht mehr senden oder eine Datei nicht mehr schreiben kann, ist derselbe Fehlerfall; das verkleinert nur das Zeitfenster und behebt nichts. Q3 (Gegenprobe vor dem Commit auf Verweise ins Leere) ist NICHT durch vorhandene Checks abgedeckt – decisions.py und qa-check Check 6 arbeiten beide auf ID-Ebene (ADR_ID_RE), der S111-Schaden war ein Verweis auf einen nie geschriebenen ABSCHNITT innerhalb einer existierenden ADR; check-dangling-refs triggert nur auf TD-/OQ-Loeschungen. Verworfen trotzdem: Ein Abschnitts-Check muesste aus Prosa-Kommentaren erraten, welcher Abschnitt gemeint ist, und produzierte vor allem Fehlalarme – ein Mechanismus mit eigener Reibung gegen einen einmaligen Vorfall. Wiederholt sich der Schadenstyp, wird neu entschieden.

---

## OBS-S105-2 – C#-String-Ops triggern unter `TreatWarningsAsErrors` kulturbezogene Analyzer
- Quelle: Subagent + Orchestrator
- Status: VERWORFEN (umgezogen in coding-guideline-csharp.md)
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: TOOLING    Kontext: C#-Code
- Beobachtung: Naive String-Operationen brechen unter `TreatWarningsAsErrors` den Build über kulturbezogene Analyzer – in S105 zweifach getroffen: (1) `.ToLower()` in einem EF-Core-LINQ-Prädikat → CA1304/CA1311/CA1862/MA0011 (Analyzer nehmen Laufzeit-`CurrentCulture` an, obwohl der Ausdruck zu SQL `LOWER()` übersetzt wird → braucht ein gezieltes `#pragma`); (2) `IndexOf(char)` / `==` / im `.env`-Parser → CA1307/MA0006 (hier ist der Nudge berechtigt → `Split`/`StringComparison.Ordinal`/`string.Equals`). Beide Male kostete es einen Trial-and-Error-Zyklus.
- Entscheidung/Maßnahme: Wissen ueber eine Werkzeug-Falle, kein Vorhaben und kein Prozess-Thema: Als OBS wartete es auf eine Behandlung, die es nie gebraucht haette. Steht jetzt als eigene Sektion in coding-guideline-csharp.md neben dem JIT-Fallstrick, mit der Unterscheidung 'Analyzer hat recht / Analyzer irrt' – dort wird es beim Schreiben von C#-Code gelesen.
- Bezug: LL-S105-1

## OBS-S103-2 – Stryker 100 % pinnt nicht die Reihenfolge von „erstes-von-N"-Prioritätslogik
- Quelle: Orchestrator
- Status: VERWORFEN (umgezogen in tdd-process.md)
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: QUALITÄT    Kontext: Mutation-Testing
- Beobachtung: Bei der Fokus-aufs-erste-Fehlerfeld-Logik (`nameError ? nameRef : unitError ? unitRef : undefined`) töteten die zwei Einzelfeld-Tests alle Stryker-Mutanten (100 %), aber der Mehrfeld-Fall (beide fehlerhaft → Priorität Name) war **nicht** gepinnt: ein menschlicher Prioritäts-Swap (Einheit vor Name) mutiert identisch und bliebe bei 100 % unentdeckt (im Review als FC-F1 gefunden, mit explizitem Mehrfeld-Assert geschlossen). Verallgemeinert: „erstes-von-N"-/Prioritäts-Auswahllogik braucht einen expliziten Mehrfach-Fall-Test; Stryker-100 % über Einzelfälle genügt nicht.
- Entscheidung/Maßnahme: Der konkrete Fall war schon in S105 mit einem Mehrfeld-Assert geschlossen; wertvoll blieb allein die verallgemeinerte Regel. Die ist Wissen, kein Vorhaben – sie steht jetzt in docs/process/tdd-process.md (Sektion Mutation Testing, Absatz '100 % Mutation Score pinnt keine Reihenfolge') und wirkt dort bei jedem Test statt auf eine Behandlung zu warten.
- Bezug: –

## OBS-S101-3 – useResultMutation: 4er-Positions-Tupel → Objekt-Rückgabe
- Quelle: Subagent
- Status: VERWORFEN (umgezogen nach TD-S122-1)
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: QUALITÄT    Kontext: TS-Code
- Beobachtung: `useResultMutation` gibt jetzt ein 4-Tupel `[mutate, error, isPending, reset]` zurück – zwei davon Funktionen. Positions-Tupel werden mit wachsender Länge fehleranfällig (Call-Sites müssen exakt in Reihenfolge destrukturieren, `error`/`isPending` leicht verwechselbar). Ein Objekt `{ save, error, isPending, reset }` wäre selbstdokumentierend und reihenfolgeunabhängig.
- Entscheidung/Maßnahme: Kein Prozess-Thema, sondern Produkt-Refactoring am Client-Code – nach der Taxonomie (CLAUDE.md, Schnitt 1) gehoert es in die technische Schuld. Inhalt unveraendert nach TD-S122-1 uebernommen; dort altert es ohne Drain-Kapazitaet zu binden, bis der Faellig-Anker Phase:MVP eintritt.
- Bezug: TD-S101-1

## OBS-S108-5 – Restore-Endpoint ist als CORS-„Simple Request" ohne Preflight erreichbar
- Quelle: Subagent (security-auditor, Review run-8)
- Status: VERWORFEN (umgezogen nach TD-S122-2)
- Impact: GERING    Häufigkeit: gelegentlich
- Kategorie: QUALITÄT    Kontext: Security
- Beobachtung: `POST /api/ingredients/{id}/restore` verlangt weder Custom-Header noch Request-Body und ist damit ein CORS-„Simple Request": Ein Browser sendet ihn cross-origin **ohne** Preflight, CORS verhindert nur das Auslesen der Antwort, nicht die serverseitige Ausführung. Alle übrigen mutierenden Endpoints sind hier zufällig geschützt – `DELETE` durch den verpflichtenden `If-Match`-Header, `POST /api/ingredients` durch `Content-Type: application/json`; beide erzwingen dadurch eine Preflight, die mangels CORS-Policy scheitert. Der Verzicht auf If-Match beim Restore ist in ADR-S108-2 bewusst und mit Concurrency-Argumenten begründet – dass If-Match nebenbei auch die Preflight erzwungen hätte, ist ein Nebeneffekt, den die ADR nicht betrachtet. Praktische Tragweite im aktuellen Stand begrenzt: Der Angreifer braucht die Ziel-UUIDv7 (~74 nicht erratbare Zufallsbits), wer sie kennt hat über das ungeschützte GET ohnehin direkten API-Zugriff, und der Schaden beschränkt sich auf das Rückgängigmachen eines Soft-Deletes. Relevant wird es, sobald Auth existiert – dann ist es die einzige Stelle, an der ein fremder Browser eine Zustandsänderung auslösen kann. Kein User-Entscheid nötig (kein Business-Impact, technische Härtungsfrage im Sinne der `CLAUDE.md`-Faustregel) – die Abwägung „Preflight erzwingen vs. bewusst tragen" gehört in den Drain, das Ergebnis in eine ADR.
- Entscheidung/Maßnahme: Kein Prozess-Thema, sondern ein Security-Befund am Produkt – nach Schnitt 1 der Taxonomie gehoert er in die technische Schuld. Inhalt nach TD-S122-2 uebernommen, Faellig Phase:MVP.
- Bezug: –

---

## OBS-S121-2 – Drain-Rate und Backlog-Ziel widersprechen sich - fester Satz gegen variablen Zielwert
- Quelle: User
- Status: UMGESETZT (S122)
- Impact: HOCH    Häufigkeit: dauerhaft
- Kategorie: PROZESS    Kontext: Skill-Nutzung
- Beobachtung: Der OBS-Drain arbeitet je Session einen Satz fester Groesse ab (aktuell 7 Eintraege: Wert-Lane, Alters-Lane, faellige Wiedervorlagen). Der Backlog liegt seit Laengerem weit ueber dem als gesund definierten Wert (Session-Start S121: 29 drainbar bei Ziel <=8) und sinkt langsamer, als neue Eintraege dazukommen - in S121 wurden fuenf aufgeloest und einer neu erfasst, netto minus vier bei 29 Ausgangslage. Der User weist auf einen zweiten, strukturellen Widerspruch hin: Mit dem neuen Startup soll gedraint werden, bis das Backlog unter einem Schwellwert steht (Groessenordnung 12). Ein Skill, der pro Durchlauf eine feste Anzahl Eintraege vorlegt, passt dazu nicht - er endet, waehrend das Backlog noch ueberfuellt ist, und die Rate ist von dem Ziel entkoppelt, das sie erreichen soll. Zu klaeren ist damit nicht nur die Hoehe der Rate, sondern ihre Form: fester Satz je Session, Abarbeiten bis zum Schwellwert, oder eine Rate, die sich aus dem Abstand zum Ziel ergibt. Mitzudenken ist die Gegenkraft - ein Drain-Durchlauf kostet real Kontext und User-Aufmerksamkeit (in S121 fuellte er eine ganze Session fuer fuenf Eintraege), ein reines Hochdrehen der Zahl verlagert das Problem also nur. KORREKTUR S122 (vom User): Die Erfassung gab den Kern unvollstaendig wieder. Vergessen und nachgetragen: Eine Drain-Session enthaelt bisher nie etwas anderes als den Drain, weil er allein schon die Session fuellt; so folgt eine Drain-Session auf die naechste, nur von Retros unterbrochen. Waehrend des Drains entstehen zudem fast immer neue OBS, sodass das Backlog langsamer schrumpft als vorgesehen. Die Folge ist der eigentliche Schaden: Es wird nicht mehr entwickelt. Gemessen in S122 ueber die Commit-Historie: Zwischen S112 und S121 wurde kein einziger Gherkin-Lauf implementiert - S113 bis S119 und S121 beruehrten null Produktdateien, S120 nur ueber die Umsetzung eines Prozess-Ergebnisses.
- Entscheidung/Maßnahme: Die Rate war das falsche Stellrad: Der Deckel 7 wurde nie erreicht (real ~4-5 Eintraege je Drain-Session), und 17 der 26 Eintraege lagen so tief, dass die Wert-Lane sie nie aufgriff. Umgesetzt wurde stattdessen ein Modell aus vier Teilen (kanonisch in process.md, Abschnitte 'Score und Behandlungswuerdigkeit' + 'Lanes und Trigger'): (1) Score = Impact x Haeufigkeit mit GERING=0 - die Rubrik definiert GERING als folgenlos, folglich traegt es auch gehaeuft und im Cluster nichts bei; behandlungswuerdig ab 2. (2) Pflichtfeld 'Verwandt' bei der Erfassung: gemeinsam loesbare Eintraege bilden eine Einheit, deren Scores summiert werden - so kommen kleine Eintraege mit dran, wenn man am Thema ohnehin arbeitet. (3) Trigger statt Backlog-Zahl: Top-5-Summe >= 9 ODER >= 4 Eintraege aelter als 15 Sessions. Die Backlog-Zahl mass Menge statt Wert und hielt sich selbst ueber der Schwelle, weil jeder Drain neue Eintraege erzeugt. (4) Alters-Lane nimmt alle ueber 15 Sessions statt nur des aeltesten - ein Slot fuehrte den Zufluss nicht ab. Verworfen: Rate erhoehen (der Deckel war nie bindend), Zielwert aufgeben (Alt-Eintraege veralten dann und tragen falsche Fakten), Log-gewichtete Alterssumme (der Logarithmus daempft das Alter so stark, dass daraus ein Anzahl-Trigger wird - die Alters-Lane existiert aber gerade fuer die uralten). Vorhersage zum Nachpruefen: Bei 1,32 behandlungswuerdigen Eintraegen je Session feuert der Wert-Trigger etwa jede dritte Session.

## OBS-S116-5 – Kein Mechanismus stellt sicher, dass ein HOCH-Finding einen CM-Anschluss bekommt
- Quelle: Orchestrator
- Status: UMGESETZT (S123)
- Impact: MITTEL    Häufigkeit: gelegentlich
- Kategorie: PROZESS    Kontext: Skill-Nutzung
- Beobachtung: process.md verlangt fuer jedes KRITISCH- oder HOCH-Finding sofort einen countermeasures-Eintrag. Geprueft wird das nur weich beim closing-session. In der Periode S107-115 entstanden 8 HOCH-Findings bei 2 neuen CMs. Ein Finding blieb ganz ohne Anschluss (LL-S113-3); bei vier weiteren existierte die inhaltlich passende Maßnahme, aber der Nachtrag an ihr fehlte. Die zweite Form ist die unauffaelligere und zugleich schaedlichere: Ohne Nachtrag zaehlt retro_report.py den Rueckfall nicht, die Maßnahme erscheint wirksamer als sie ist, und die naechste Retro bewertet sie auf zu guenstiger Datenlage - genau der Fehler, den LL-S107-2 fuer die BEWAEHRT-Hochstufung beschreibt. Der Punkt war als CM-S078-2 schon einmal offen und wurde in S095 verworfen, weil zwei Perioden ohne Fehlausgang vergingen; die Verwerf-Begruendung nannte ausdruecklich den Fall, der jetzt eingetreten ist. Erschwerend: Der Anschluss ist keine rein syntaktische Eigenschaft - ob eine bestehende CM inhaltlich passt, ist ein Urteil, weshalb ein rein mechanischer Abgleich Impact gegen CM-Existenz Fehlalarme erzeugen wuerde.
- Zusammen-erledigen: keiner
- Entscheidung/Maßnahme: Der CM-Anschluss entsteht ab jetzt bei der ERFASSUNG statt in der Retro: Pflichtfeld 'CM-Bezug:' im LL-Eintrag, erzwungen von 'lessons.py add --cm-bezug' fuer KRITISCH/HOCH (zulaessig: existierende CM-ID oder 'neu'; Freitext und tote IDs brechen mit Exit 1 ab). Rueckweg im kaizen-Skill Schritt 3 verankert, der die Bezuege der Periode vor der Archivierung einloest. Gewaehlt, weil der in S116 vorgesehene Weg ueber den Drain zu langsam gewesen waere: Der Eintrag traegt Score 1 und liegt unter der Schwelle der Wert-Lane (>= 2); aufgegriffen haette ihn die Alters-Lane mit erzwungener Entscheidung, aber erst ab 15 Sessions, also ab S131. Fuer ein Problem, das in jeder Session neue Instanzen erzeugt, ist das zu spaet - der Drain arbeitet hier wie gebaut, er ist nur nicht das passende Werkzeug. Verworfen: (a) PreToolUse-Hook auf lessons_learned.md - er saehe nur den einzelnen Edit und blockte faelschlich, wenn erst das LL und dann die CM geschrieben wird; (b) reiner Retro-Schritt - das ist der Status quo, der in S116-122 acht von neun HOCH-Findings ohne Anschluss liess; (c) Spalte in retro_report.py - erst zur Retro sichtbar, also zu spaet. Bekannte Grenze: Der Zwang sitzt im Script, ein direkter Datei-Edit umgeht ihn; ein Edit-Hook analog check-obs-capture.py bleibt der naechste Kandidat, falls die Luecke praktisch auftritt. Bezug: CM-S078-2.
- Bezug: CM-S078-2

