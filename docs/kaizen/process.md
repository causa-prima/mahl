# Kaizen-Prozess

<!--
wann-lesen: Beim Schreiben eines lessons_learned-Eintrags (Schwere/Kategorie/Kontext bestimmen),
            beim Starten einer Retro, beim Bewerten einer Maßnahme.
-->

## Was gehört in lessons_learned?

Ein Eintrag ist sinnvoll wenn er ein **Agenten-Verhalten** beschreibt das wieder auftreten könnte.

**Nicht dokumentieren:**
- Infrastruktur- oder Setup-Fehler die durch eine Konfigurationsänderung dauerhaft behoben sind
  → Dieses Wissen gehört in `docs/process/dev-workflow.md`, eine Config-Datei oder einen Code-Kommentar
- Reine Fakten über Tool-Verhalten ohne Konsequenz für künftiges Agenten-Verhalten
- Fehler aus einer **einmaligen Situation, die grundsätzlich nicht wiederkehren kann** und unter der **keine wiederkehrende Tätigkeits-Klasse** liegt (z.B. ein Fehler, der nur an eine einmalige Repo-Umstellung gebunden war)
  → Achtung Abstraktionsebene: Liegt unter der einmaligen konkreten Auslösung eine wiederkehrende Klasse (z.B. „programmatische String-Transforms", „Datei-Renames"), ist der Eintrag sinnvoll – aber auf der **Klassen-Ebene** formuliert, nicht auf der Einmal-Situation.

**Test vor jedem Eintrag (alle drei Fragen müssen mit Ja beantwortet werden, sonst kein Eintrag):**
1. „Könnte ein Agent diesen Fehler wieder machen – auch wenn die Konfigurationsänderung schon vorhanden ist?" (Nein → Infra-/Config-Noise)
2. „Kann die auslösende Situation grundsätzlich wiederkehren – bzw. liegt eine wiederkehrende Tätigkeits-Klasse darunter?" (Nein → einmalige Situation, kein Eintrag)
3. „Beschreibt die *Regel* ein **Agenten-Verhalten oder -Urteil**, das schiefgehen kann – oder ist sie eine **statische Tatsache**, die man einmal nachschlägt und danach kennt?" (statische Tatsache → Noise, gehört nach `docs/process/dev-workflow.md` oder in einen Code-Kommentar)

> Warum Frage 3 nötig ist: Frage 1 allein trennt Tool-Fakten nicht sauber ab – ein Agent „könnte" fast jeden Tool-Fakt wiederholen, weil er Tool-Verhalten nicht auswendig kennt, womit Frage 1 fast nie Nein ergibt. Erst Frage 3 zieht die Linie: wiederkehrendes Verhaltensmuster bleibt, nachschlagbare Tatsache ist Noise.

Alle drei Ja → dokumentieren (Frage 2: auf Klassen-Ebene formulieren, nicht auf der einmaligen Auslösung).

---

## Eintrag-Format (lessons_learned.md)

Einträge werden pro Session gruppiert:

```markdown
## Session NNN – YYYY-MM-DD

- **[SCHWERE] [KATEGORIE] [KONTEXT] Kurztitel**
  Was: Ein Satz – was ist passiert?
  Warum: Ein Satz – Ursache.
  Regel: Die destillierte Erkenntnis (imperative Form).
```

Alle drei Tags sind Pflicht. Definitionen: Abschnitte unten.

---

## Schwere-Kategorien

| Schwere | Definition | Sofortreaktion | Maßnahmen-Anspruch |
|---------|-----------|----------------|-------------------|
| **KRITISCH** | Verursacht signifikanten Rework oder Qualitätsverlust; darf unter keinen Umständen wiederholt werden | **Andon-Cord:** Arbeit sofort stoppen, Ursache analysieren, Gegenmaßnahme definieren – erst dann weitermachen | Poka-yoke **Pflicht** – schwächere Maßnahmen reichen nicht |
| **HOCH** | Verzögert die Arbeit spürbar oder gefährdet Qualität | In derselben Session: Eintrag in `lessons_learned.md` + `countermeasures.md` | Poka-yoke anstreben wenn verhältnismäßig; sonst expliziter Schritt in Guideline oder Skill |
| **MITTEL** | Kleine Prozessabweichung, schnell bemerkt | Eintrag in `lessons_learned.md` | Poka-yoke anstreben wenn einfach umsetzbar; sonst Eintrag in `principles.md` wenn wiederholt |
| **GERING** | Stilistisch oder präferenzbedingt | Eintrag in `lessons_learned.md` | Keine Maßnahme nötig |

---

## Bereichs-Kategorien

Entscheidungskriterium: **Wo liegt der Fix?**

| Kategorie | Beschreibung | Beispiele |
|-----------|-------------|---------|
| **PROZESS** | Fix liegt im Workflow, in einem Skill-Schritt oder in der Session-Struktur | TDD-Verstoß, Skill-Schritt übersprungen, Evaluation+Implementierung kombiniert |
| **AGENT** | Fix liegt in der Art wie Sub-Agenten instruiert werden | Reviewer mit Iterations-Vorwissen, unklarer Prompt, falscher Kontext an Agent |
| **QUALITÄT** | Fix liegt im Code oder in der Test-Qualität (kein Prozess-Muster) | Primitive Typen statt Domain-Typen (isolierter Fall), fehlender Test |
| **TOOLING** | Fix liegt in Build, Infrastruktur, IDE oder Konfiguration | WSL/npm-Problem, CI-Konfiguration, Build-Pipeline |

> Wenn ein QUALITÄT-Problem wiederholt auftritt → Ursache ist meist PROZESS (Skill/Hook fehlt).

---

## Kontext-Tags

Beschreibt *was* konkret betroffen war – feiner als die Kategorie.

| Tag | Bedeutung |
|-----|-----------|
| `TDD` | Test-first-Disziplin, Red-Green-Refactor-Loop |
| `C#-Code` | C#-Implementierung, .NET-Guidelines |
| `TS-Code` | TypeScript/React-Implementierung, Frontend-Guidelines |
| `Bash/Permission` | Befehlsausführung & Permission-Hook (Allow-Liste, `--allow-once`, ad-hoc-Befehle) |
| `Mutation-Testing` | Stryker / QA-Gate (Score, Hashes, Coverage-Gate, Build-Lock für Mutation-Läufe) |
| `Hook/Script` | Selbstgebaute Projekt-Automatisierung (.claude-Hooks & -Scripts, Pfad-Matcher, Migrations-Scripts) |
| `Review` | Code- oder Dokument-Review-Prozess |
| `Agent-Prompt` | Formulierung & Mechanik von Sub-Agenten-Instruktionen |
| `Skill-Nutzung` | Anwendung oder Aufrufen von Skills (inkl. Kaizen-Prozess-Bookkeeping) |
| `Gherkin` | Feature-Files, Szenario-Formulierung |
| `Doku` | Guidelines, Docs, Entscheidungen pflegen |
| `Kommunikation` | Aussagen ggü. dem User – Verifikation vor Behauptung, Mechanismus-Präzision, Hypothesen-Framing |
| `Sonstiges` | Passt in keinen anderen Tag. **Staging-Area:** dünne/unklare Cluster (z.B. Build/Deps, Harness-Tool-Bedienung wie Edit/replace_all) hier parken – graduieren zu eigenem Tag, sobald ein Muster wächst |

**Pflege der Kontext-Tags:**
- Alle `Sonstiges`-Einträge werden in jeder Retro explizit gesichtet – Ziel: fehlende Tags ableiten
- Sehr häufige Tags (>30% aller Einträge) werden auf sinnvolle Aufteilung untersucht
- Neue oder geänderte Tags werden in dieser Datei dokumentiert

---

## Wann gehört etwas wohin?

| Ziel | Kriterium |
|------|-----------|
| `lessons_learned.md` | Jedes Finding, immer |
| `principles.md` | Verhaltensregel die in jeder Session gilt; zu querschnittlich für eine Guideline/Skill |
| `countermeasures.md` | Jedes KRITISCH- oder HOCH-Finding sofort; MITTEL/GERING wenn Retro ein Muster aufdeckt |
| Guideline / Skill | Das Problem liegt an einem fehlenden oder falschen Schritt in einem konkreten Arbeitsablauf. Die Änderung ist direkt als Regel/Schritt in einem bestehenden Dokument formulierbar. (Meist wird zusätzlich ein `countermeasures.md`-Eintrag angelegt, der auf diese Änderung verweist.) |

**principles.md ⇄ countermeasures.md:** Ein Prinzip in `principles.md` ist die **Fließtext-Leitplanke** (wird jede Session geladen, keine Tags). Jedes Prinzip hat **zusätzlich** einen Tracking-Eintrag in `countermeasures.md` (Tupel Schwere/Kategorie/Kontext + Status) – nur so bleibt es **evaluierbar** (BEWÄHRT/Rückfall) und wird von `retro_report.py` als „abgedeckt" erkannt. Die CM-Maßnahme verweist aufs Prinzip („Regel in principles.md dokumentiert"). BEWÄHRT-CMs bleiben in der Tabelle (Regressionserkennung). Konsequenz: Ein neu angelegtes Prinzip **immer** mit einem CM-Eintrag spiegeln – sonst ist es unsichtbar fürs Script und nicht bewertbar.

**CM-Eingangs-Gate (vor dem Anlegen einer Countermeasure):** Dieselbe Recurrence-Frage wie beim lessons-Eintrag, aber auf Maßnahmen-Ebene und vorgelagert (damit nicht Aufwand in eine Maßnahme fließt, die sofort obsolet wäre):

> „Liegt unter dem Finding eine **wiederkehrende Tätigkeits-Klasse**, die zwangsläufig Teil des normalen Arbeitsablaufs ist – oder war die Auslösung an eine **einmalige Umstellung gebunden, die grundsätzlich nicht wiederkehrt**?"

Keine verallgemeinerbare Klasse darunter → **keine CM** (sie wäre sofort obsolet, siehe Obsolet-Kriterien unten). Klasse vorhanden → CM auf **dieser** Klassen-Ebene formulieren, nicht auf der einmaligen konkreten Auslösung. Filtere nach Häufigkeit *nicht* (fast alles „kann schon wiederkehren") – entscheidend ist die strukturelle Wiederkehrbarkeit der Situation.

**Messwerkzeug bei CM-Definition (gilt für alle Maßnahmen):** Beim Festlegen einer Maßnahme zugleich bestimmen, **woran** ihre Wirksamkeit später beurteilt wird (sonst lässt sich BEWÄHRT/Rückfall nie belegen). Default-Kanal: lessons_learned + Session-Dateien – reicht für **selbst-berichtbare** Probleme. Adressiert die Maßnahme ein Verhalten, das der Agent **nicht** selbst als Problem loggt (z.B. Bash-Permission), muss schon jetzt eine **harte Datenquelle** benannt oder geschaffen werden (z.B. ein Log). Der Check ist leichtgewichtig: Default genügt meistens; nur die Lücke „nicht selbst-berichtet" erzwingt eine explizite Datenquelle.

---

## Retro-Trigger: Jenga-Score

Der Jenga-Score misst akkumulierten Problemdruck seit der letzten Retro.
Script `jenga_score.py` berechnet ihn aus der aktuellen `lessons_learned.md`.

**Start-Wert:** 100 Punkte

| Ereignis | Abzug |
|---------|-------|
| Session (immer) | -5 |
| KRITISCH-Finding | -25 |
| HOCH-Finding | -10 |
| MITTEL-Finding | -3 |
| GERING-Finding | -1 |

**Bei Jenga-Score ≤ 0:** Nächste Session beginnt mit einer Retro (Skill `kaizen`).

Scripts: `.claude/scripts/jenga_score.py` (nach jeder Session) und `.claude/scripts/retro_report.py` (zur Retro).
Nach einer Retro wird `lessons_learned.md` archiviert → Jenga-Score startet neu bei 100.

---

## Scripts

### jenga_score.py
Läuft nach jeder Session (im `closing-session`-Skill).
Input: `docs/kaizen/lessons_learned.md`
Output: Jenga-Score + Zähltabelle (Schwere × Kategorie × Kontext)

### retro_report.py
Läuft zu Beginn jeder Retro (im `kaizen`-Skill).
Input: aktuelle `lessons_learned.md` + alle Archiv-Dateien in `docs/kaizen/archive/`
Output: Aggregation, Zeitreihen-Charts, Pattern-Kandidaten (Muster ≥2× im Fenster, gefiltert gegen `countermeasures.md`),
semantisches Clustering (ab 50 Einträgen), Trendanalyse je Kategorie.
Details: Kommentar-Header in `.claude/scripts/retro_report.py`.

---

## Archivierung (nach Retro)

Die aktuelle `lessons_learned.md` wird nach `docs/kaizen/archive/` verschoben.
Ablauf: Skill `kaizen`, Schritt 5.
Der Jenga-Score startet automatisch neu – `jenga_score.py` liest immer nur die aktuelle Datei.

---

## Umsetzung offener Maßnahmen

**Regel 1 – Sichtbarkeit:** Jede neue OFFEN-Maßnahme wird in derselben Retro-Session unter „Nächste Prioritäten" in `docs/AGENT_MEMORY.md` eingetragen. Falls inhaltlich zutreffend auch als Technische Schuld oder Offene Frage. Ablauf: Schritt 4 des `kaizen`-Skills.

**Regel 2 – Eskalation:** Eine Maßnahme die nach 2 Retros noch OFFEN ist, wird in der nächsten Retro (Schritt 3, Abschnitt F) als ESKALIERT präsentiert. Der User entscheidet dann: Umsetzung priorisieren oder bewusst verwerfen (Begründung in der Maßnahme notieren).

---

## BEWÄHRT-Kriterium für Countermeasures

Eine Maßnahme gilt als BEWÄHRT wenn:
- Die relevante Situation nach Einführung der Maßnahme mindestens 3× aufgetreten ist
- Kein Rückfall beobachtet wurde
- "Aufgetreten" = die Art der Arbeit, bei der das Problem hätte entstehen können, hat stattgefunden

Nachweis: Session-Dateien in `docs/history/sessions/` lesen und beurteilen, ob die relevante Arbeit stattfand.

> **Harte Daten bei nicht-selbstberichteten Verhaltensweisen:** Adressiert die Maßnahme ein Agenten-Verhalten, das der Agent **nicht selbst** als Problem in lessons_learned einträgt (z.B. Bash-Permission-Verstöße, abgelehnte Befehle), ist „keine neuen lessons_learned dazu" **kein** Beleg für BEWÄHRT (der Agent sieht es nicht als Problem). Stattdessen die primäre Datenquelle auswerten (z.B. `.claude/tmp/denied-commands.log`). Fehlt diese, ist **keine verlässliche/belastbare Aussage** möglich – dann den User fragen, ob ihm das Verhalten aufgefallen ist und wie mit dem Punkt weiter verfahren werden soll.

## Obsolet-Kriterien für Countermeasures

Ein Eintrag ist obsolet wenn:
- Das betroffene Tool oder die Technologie nicht mehr genutzt wird
- Der zugrundeliegende Prozess so fundamental umgebaut wurde, dass das Problem strukturell nicht mehr entstehen kann
- Es sich um eine einmalige Situation handelte, die grundsätzlich nicht wiederkehren kann
