---
name: review-code
description: >
  Code-Review nach einer Implementierung: Selbstcheck via docs/process/review-checklist.md,
  dann spezialisierte Review-Agenten spawnen und Findings als strukturierte Liste
  zurückgeben. Wird vom Review-Loop in implementing-scenario direkt ausgeführt (kein
  Subagent-Wrapper). Kann auch standalone auf beliebigem Code angewendet werden.
user-invocable: true
---

# Skill: review-code

<a id="RVC-eingabe"></a>
## Eingabe

- Scope + Szenario-Tag (oder freier Scope bei standalone-Aufruf)
- Geänderte Dateien (Pfade oder git-diff-Auszug)
- **Stryker-Suppression-Report:** neue Suppressionen aus dem REFACTOR-Schritt
  (Format: Datei:Zeile – Begründung), oder leer wenn keine neuen Suppressionen

Fehlende Eingaben bei standalone-Aufruf: Scope → User nach Beschreibung der Änderung fragen.
Geänderte Dateien → `git diff` (staged + unstaged) als Standard verwenden.

---

<a id="RVC-ablauf"></a>
## Ablauf

<a id="RVC-selbstcheck"></a>
### Selbstcheck (docs/process/review-checklist.md)

Gehe in `docs/process/review-checklist.md` jeden Abschnitt Punkt für Punkt durch, dessen „Wann lesen"
in der [Inhaltstabelle](../../../docs/process/review-checklist.md#RCL-inhalt) auf die Änderung zutrifft.

Für jedes Finding: Schweregrad ❌/⚠️/✅ + Guideline-Referenz (Datei + Sektion) notieren.
Findings werden gesammelt – nicht sofort selbst behoben.

<a id="RVC-suppression-report"></a>
### Suppression-Report bewerten

Jeden Eintrag im übergebenen Stryker-Suppression-Report einzeln prüfen. Maßstab:
[Welcher Survivor bekommt welche Reaktion?](../../../docs/process/tdd-process.md#TDD-survivor-entscheidung).

Für jeden Eintrag: Nennt die Begründung eine ADR, und deckt diese genau die Klasse des Falls – oder
eine Einzelfall-Freigabe des Users? Und trägt die Begründung inhaltlich, oder klingt sie nur
plausibel? ([Review-Prozess](../../../docs/kaizen/principles.md#KPI-review-prozess): semantische
Korrektheit prüfen, nicht blind übernehmen.) Fehlt beides oder trägt die Begründung nicht → ❌ Finding.

Kein Suppression-Report übergeben oder leer → Schritt überspringen.

<a id="RVC-agenten-spawnen"></a>
### Review-Agenten spawnen

⚠️ **Context-Freiheit:** Jeden Agenten ohne Iterations-Vorwissen spawnen – weder frühere
Findings noch als false positive bekannte Punkte im Prompt. Filtering geschieht im
Anschluss. Begründung: Vorwissen dämpft die Kritikbereitschaft strukturell – der Reviewer
denkt „wurde ja schon reviewt". Unabhängige Urteile, dann zentral filtern.

Scope bestimmt welche Agenten nötig sind:

| Was wurde geändert? | Agenten |
|--------------------|---------|
| Änderung ohne Verhaltensänderung (z. B. Rename, Refactoring ohne Logik-Änderung) | `code-quality-auditor` |
| Neue Funktionalität / Verhaltensänderung | `code-quality-auditor` + `functional-correctness-auditor` + `test-quality-auditor` |
| + API-Grenze, User-Input oder Auth berührt | + `security-auditor` |
| + Frontend-Komponenten geändert | + `ux-ui-auditor` |
| Nur Tests geändert (kein Produktionscode) | `test-quality-auditor` |
| Nur Suppressionen hinzugefügt | [Suppression-Report bewerten](#RVC-suppression-report) deckt das ab – kein Agent-Spawn nötig |
| Nur Dokumentation / Kommentare geändert | `code-quality-auditor` |
| Prozess-Code (Python unter `prozesscode/`) | [Eigene Stufen](#RVC-prozess-code) – meist **kein** Agent |

Jeden Agenten via Agent-Tool mit `subagent_type: "<name>"` spawnen (z.B. `subagent_type: "code-quality-auditor"`) – die Namen entsprechen der Tabelle (es sind registrierte Agenten in `.claude/agents/`, read-only).

**Modellwahl vor Spawn:** Auditoren laufen per Default auf `model: sonnet` (Frontmatter). Den `model`-Parameter des Agent-Tools nur dann setzen, wenn die Änderung erhöhte Tiefe verlangt (z.B. subtile Nebenläufigkeit, nicht-triviale Sicherheits-Edge-Cases) → gezielt `opus` für den betroffenen Auditor; Routine-Reviews bleiben auf `sonnet`. Vor jedem Spawn kurz prüfen: reicht der Default?

Alle zutreffenden Agenten parallel spawnen – sie reviewen denselben Diff und haben keine gegenseitigen Abhängigkeiten. Bei Unsicherheit über den Scope: `git diff` selbst auswerten; bei genuiner Ambiguität User fragen.

Agent-Prompts enthalten (je Agent):
- Geänderte Dateien / git diff
- Anforderung: jedes Finding nennt Schweregrad (❌/⚠️), Guideline-Referenz
  (konkrete Datei + Sektion) und Begründung (nicht nur Guideline zitieren)
- Hinweis: Projekt-Guidelines (`docs/guidelines/coding-guideline-*.md`) haben Vorrang vor
  agenten-eigenen Checklisten
- **ADR-Volltexte im Prompt, plus Auftrag zur eigenen Gegenprobe.** Die Auditoren haben **kein Bash**
  (Tools: Read, Grep, Glob, LSP – s. `.claude/agents/*.md`), und das bleibt so: Die Tool-Liste ist
  der Mechanismus, der „erzeugt ausschließlich Findings" garantiert – eine Allow-Liste wäre dafür
  nur Disziplin. Ein Prompt, der ihnen `python3 -m prozesscode.decisions get …` aufträgt, läuft
  deshalb ins Leere. Stattdessen zweigleisig:
  1. Die vom Orchestrator als relevant eingestuften ADRs **im Prompt ausschreiben**.
  2. Den Auditor ausdrücklich beauftragen, in `docs/history/adr.md` **per Grep selbst nachzusehen** –
     eine zweite Meinung, die nur die Auswahl des Orchestrators kennt, ist keine.

  Aus demselben Grund lesen Auditoren die **Guidelines vollständig** und nicht abschnittsweise über
  `doc.py get <ANKER>`, obwohl der gezielte Abruf für Implementierer der Regelweg ist: Ohne Bash
  könnten sie das Script ohnehin nicht ausführen – vor allem aber setzt gezieltes Abrufen voraus,
  dass man schon weiß, wonach man sucht. Ein Implementierer weiß das (er kennt seine Aufgabe), ein
  Reviewer nicht: Er sucht Verstöße, deren betroffene Guideline-Stelle vorher niemand kennt. Wer ihm
  nur die Abschnitte gibt, die der Orchestrator für einschlägig hielt, bekommt genau die Findings
  zurück, die der Orchestrator ohnehin erwartet hat.

  Die ADR-Mitgabe ist nicht optional: Fehlt eine ADR, die ein Finding entkräftet, meldet der Auditor ein
  False Positive, das erst beim Zusammenführen auffliegt. Real passiert: ADR-S106-3 (Querschnitts-/
  Infra-Tests tragen bewusst keinen US-Tag) stand nicht im Prompt, und ein Auditor meldete daraufhin
  zwölf legitime Tests als Namensformat-Verstoß.
- **Rückgabe:** Den vollständigen Findings-Endbericht in **einem Stück** am Ende des Laufs liefern,
  über den Rückgabeweg, den der Harness dem Agenten vorgibt (derzeit für unbenannte Hintergrund-Agenten
  ein eigener Rückgabe-Aufruf, für benannte Agenten die letzte Ausgabe). Text mitten im Lauf sieht der
  Orchestrator nicht; ein auf mehrere Zwischentexte verteilter Bericht ginge teilweise verloren.
  (Gemessen 2026-10-09 und 2026-10-12, Claude Code 2.1.295.)

<a id="RVC-prozess-code"></a>
### Prozess-Code: eigene Stufen

Python unter `prozesscode/` folgt nicht der Scope-Matrix oben. Es hat keinen externen Nutzer, kein
Szenario und keinen Stryker-Lauf – und sein Fehlerprofil ist ein anderes: Die Klasse, die hier
weh tut, ist der Mechanismus, der fehlerfrei läuft und trotzdem nichts prüft
([Fehlerprofil](../../../docs/guidelines/coding-guideline-python.md#CGP-fehlerprofil)). Ein
zweiter Leser findet die nicht; sie fällt nur auf, wenn jemand die Wirkung herstellt.

**Immer:** Selbstcheck gegen [`RCL-prozess-code`](../../../docs/process/review-checklist.md#RCL-prozess-code)
– **statt** der übrigen Abschnitte der Checkliste. Suppression-Report entfällt (kein Stryker).

**Zusätzlich ein Auditor**, wenn die Änderung eines von beidem betrifft:
- einen **Hook, ein Gate oder einen Guard** – also Code, dessen Ausfall stumm ist,
- ein **von mehreren Scripts genutztes Modul** (`_util.py`, `_hook_io.py`, `_wrapper_output.py`,
  `td_anchors.py`, `anchors.py` und ihresgleichen) – dort trägt ein Fehlgriff weit.

Welcher: `code-quality-auditor`; wurden überwiegend Tests geändert, stattdessen
`test-quality-auditor`. Nur einer, nicht beide – der Nutzen des zweiten deckt sich hier
weitgehend mit dem des ersten.

**Sonst kein Agent.** Ein einzelnes Script, ein Wrapper, eine Testdatei: Der Selbstcheck genügt,
`ruff` und die Werkzeug-Suite laufen ohnehin bei jeder Änderung. Das ist ein bewusster Verzicht,
kein Vergessen – bei einer Änderungsrate von nahezu jeder Session wäre der Regelfall sonst
teurer als der Ertrag, und geprüft würde überwiegend Lesbarkeit, also die bereits gedeckte
Fehlerklasse.

**Grenze des Auditors, im Prompt zu nennen:** Er hat kein Bash, kann also weder den Guard
auslösen noch einen Wrapper fahren. Er beurteilt Struktur, Testdesign und Meldungsqualität –
**nicht**, ob der Mechanismus wirkt. Dieser Beleg bleibt die Gegenprobe des Autors; ein
Auditor-Report ersetzt sie nie.

<a id="RVC-findings-zusammenfuehren"></a>
### Findings zusammenführen

Alle Findings aus Selbstcheck + Suppression-Bewertung + Agenten zusammenführen. Für jedes Finding prüfen:
ist die Begründung semantisch korrekt – „Es ist implementierbar" ≠ „Es ist das richtige
Verhalten"? Insbesondere Performance-Tradeoff-Argumente und stille Fallbacks kritisch hinterfragen.

Ein Finding gilt als false positive wenn die zitierte Guideline im konkreten Code-Kontext nicht
greift (z.B. agenten-eigene Checkliste widerspricht Projektguideline) oder wenn die Begründung
durch den Code-Kontext widerlegbar ist. False positives aus dem Report herausnehmen und kurz begründen.

**Scope-Prüfung (Pflicht für jedes verbleibende Finding, in dieser Reihenfolge):**

1. **Gehört das geforderte Verhalten in die aktuelle Phase?** Ist es erst in einer späteren
   Phase gefordert, wird es **nicht jetzt gebaut**, sondern als Schuld mit Phasen-Auslöser
   vorgeschlagen (in `implementing-scenario`: Punkt der [Abschluss-Triage](../implementing-scenario/SKILL.md#IMP-abschluss),
   der User entscheidet).
2. **Fordert ein Szenario das Verhalten?** Ändert der Fix beobachtbares Nutzerverhalten (neue
   Reaktion auf eine Eingabe, geändertes Timing, ein zusätzlicher Guard), braucht er ein Szenario –
   „kommt aus einem Review-Finding" ist kein Ausnahmegrund. Fehlt es, gehört es vor dem Fix ins
   Feature-File; ist das zu groß für jetzt, wird der Fix zurückgestellt (wie Schritt 1). Begründung
   und Ablage-Regel: [Review-Loop](../implementing-scenario/SKILL.md#IMP-review-loop), Szenario-Frage.
3. **Sonst sofort umsetzen** – gilt für ❌ und ⚠️ gleichermaßen; Aufschieben kostet mehr Verwaltung
   als der Fix. **Wer** umsetzt, hängt vom Aufruf ab:
   - **Im Review-Loop von `implementing-scenario`:**
     - **Trivial** (Namen, Kommentare, Formatierung, Extraktion ohne Verhaltensänderung) → der
       Orchestrator selbst. Hat er dabei Code angefasst, führt er `qa-check` erneut aus – als Beleg,
       dass Tests und Mutation-Score unverändert stehen.
     - **Alles andere** – insbesondere wenn der Fix Verhalten ändert oder ein Test angepasst werden
       müsste → ein Schicht-Subagent mit TDD. Neu starten oder den bisherigen wiederaufnehmen ist
       abzuwägen, mit Tendenz zu neu (Kosten; Kriterium:
       [Wiederaufnehmen oder neu starten](../implementing-scenario/SKILL.md#IMP-innerer-loop)).
   - **Prozess-Code** (`prozesscode/`): der Autor selbst; Beleg ist die Werkzeug-Suite, bei Guards
     zusätzlich die Mutations-Sperrklinke ([Prozess-Code](../write-code/SKILL.md#WRC-prozess-code)) –
     kein `qa-check`, kein Schicht-Subagent.
   - **Eigenständig vom User aufgerufen** (fremder Diff, kein laufender Auftrag): nichts ändern –
     die Liste geht an den User, er entscheidet über die Umsetzung.

Grund: Ein Finding umzusetzen, dessen Verhalten kein Szenario der aktuellen Phase fordert, erzeugt
Code ohne treibendes Szenario – und damit regelmäßig mehr Schuld, als es beseitigt. Real passiert:
Eine Pending-Sperre wurde aus einem Review-Finding gebaut, ohne dass ein Szenario sie forderte;
weil Fehler- und Mehrfach-Pfade dieser Sperre nun ungetestet mitliefen, entstanden daraus vier neue
Schuld-Punkte, darunter eine dauerhaft deaktivierbare Schaltfläche ohne Retry-Weg.

**Ausgabe (strukturierte Liste für den Orchestrator):**

```
❌ Must Fix:
- [Quelle: Selbstcheck|Agent] [Datei:Zeile] [Guideline: <Pfad>, <Sektion>] <Beschreibung>

⚠️ Improvements:
- [Quelle: Selbstcheck|Agent] [Datei:Zeile] [Guideline: <Pfad>, <Sektion>] <Beschreibung>

Suppression-Bewertung:
- [Datei:Zeile] → valide | ❌ Begründung unzureichend: <Warum>

✅ Keine weiteren Findings
```
