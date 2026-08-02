# Session 114 – 2026-08-02/03

**Phase:** SKELETON · **Story:** US-904 (alle Läufe implementiert)

Kein Produktionscode. Zweiter OBS-Drain in Folge, ausdrücklich vor der fälligen Retro. Backlog 26 → 20 (fünf aufgelöst, einer auf Wiedervorlage, zwei neu erfasst). Der zweite Block bestand fast vollständig darin, eigene Zahlen zu widerlegen: Drei der Empfehlungen ruhten auf Angaben, die einer Messung nicht standhielten – jedes Mal durch eine Rückfrage des Users ausgelöst (→ LL-S114-1 bis -3).

---

## Block A – tech-debt-Format (OBS-S112-1, -2, -6)

Drei Einträge, dieselbe Datei, dieselbe Ursache: Das Eintragsformat kodierte die Fälligkeit nicht verbindlich. Verifiziert statt übernommen – die in den Einträgen zitierten Beispiele waren durch den S112-Durchgang längst bereinigt, die Ursache stand unverändert.

- **OBS-S112-2** am Bestand geprüft: Das Prioritätsfeld hatte im **gesamten** Tooling keinen Leser (`implementing-scenario` sichtet TD area-basiert, kein Script parst die Datei). Ersatzlos gestrichen.
- **Neues Format:** `**Fällig:**` / `**Problem:**` / `**Behebung:**`, alle 20 Bestandseinträge migriert. Vier Regeln im Header, davon zwei mechanisch geprüft.
- **`check-td-capture.py`** (im Dispatcher registriert) fordert die Pflichtfelder, blockt die abgeschafften und koppelt `Fällig: jetzt` daran, dass die TD-ID in `AGENT_MEMORY.md` steht – die einzige Datei, die jeder Session-Start liest. Bewusst **ohne** `obs-ok`-Pendant: Für die denkbaren Fälle wäre die Klappe die Umgehung der Regel selbst (Argument aus OBS-S112-8).
- **Folge:** TD-S083-4 verletzt Guideline §2 verifizierbar und steht nach Regel 4 auf `jetzt` – neu in der Prioritätenliste.

Der Hook hat seinen eigenen Bau bewiesen: Er blockte den halb migrierten TD-S077-1-Edit.

## Block B – Read-Volumen, ADR-Übergabe, Access-Layer

**Messgrundlage wiederhergestellt.** Die S109-Zahlen stammten aus `.claude/tmp/read_breakdown.py`, das nach Gebrauch gelöscht wurde und aus dem Session-Log zurückgeholt werden musste (das Muster aus OBS-S111-3). Zwei Fehler der Vorgänger-Messung dabei aufgedeckt: Sie scannte nur Sessions mit `subagents/` – faktisch ein Filter auf implementing-scenario-Sessions – und zählte Tool-Ausgaben über ~60 KB nur als 2-KB-Vorschau, weil Claude Code sie auslagert.

**Neu als reguläre Werkzeuge:** `read-breakdown.py` (Read-Volumen nach Session-Art/Bereich/Datei, löst Auslagerungen auf), `tool-usage.py` (Filter-Quote und LSP-Nutzung, beide S115 fällig), Modul `_session_logs.py`, Mapping `.claude/session-types.json`. Session-Art primär über `attributionSkill` (38 von 48 Logs), sonst über eine Heuristik auf den editierten Dateien. Deren erste Fassung klassifizierte 18 Sessions als Drain – `closing-session` schreibt in jeder Session nach `observations.md`; erst der Abzug dieser Rausch-Dateien (User-Vorschlag) brachte 45 von 48 Sessions automatisch zu. Gegenprobe am Archiv bestätigte die Retro-Zahl und deckte auf, dass `gherkin-workshop` fälschlich als Implementierung galt.

- **OBS-S111-2** widerlegt: Die Vorschrift wurde über 24 Schicht-Aufträge **nie** befolgt (größter Prompt 11.099 Zeichen gegen 101.722 vorgeschriebene). Kernbefund stattdessen: `scope:cross-cutting` trägt 65 von 87 ADRs und trennt nichts, während jede ADR mindestens einen fachlichen Tag hat. `implementing-scenario` filtert jetzt darüber; in die Message geht der Volltext der bewerteten ADRs plus die Suchbefehle für die unabhängige Gegenprobe des Subagenten.
- **OBS-S109-1** auf Wiedervorlage (S120): Ursache gemessen – nur ein Drittel des Lesens auf Code/Tests ist Vor-Edit, zwei Drittel sind Orientierung. `test-inventory.py` liefert dafür Testnamen **mit Zeilenbereich** (C#/TS), verdrahtet in beide Layer-Implementer; im Frontend zusätzlich `documentSymbol` für Nicht-Test-Dateien. Verworfen: Testdateien aufteilen (das Wachstum ist erwartbar, das Voll-Lesen nicht) und ein reiner Prompt-Appell (OBS-S085-3 belegt, dass er die Quote nicht bewegt).
- **OBS-S096-3** umgesetzt, schmal zugeschnitten: `obs.py` (get/add/set) und `lessons.py` (get/add). Die S109-Reaktivierung hatte auf die ADR-Schreibseite gezeigt – gemessen ist `docs/history` mit 74 % gezielter Reads der **best**-bediente Bereich, während `docs/kaizen` zu 50 % erzwungener Vor-Edit-Read ist. Zweiter Nutzen: Form durch Konstruktion statt nachträglicher Prüfung.

## Werkzeug-Sichtbarkeit

`check-bash-permission.py` verlangt jetzt Freigabe für `obs.py add|set` und `lessons.py add` (neue `WRITE_ACCESS_PATTERNS`, vor dem Segment-Check). Grund: Die Scripte ersparen den Vor-Edit-Read und umgehen damit den Dialog, in dem der geschriebene Text sichtbar wäre. `obs-archive.py` bleibt ohne Freigabe – mechanisches Verschieben ohne neuen Text.

`obs_parse.running_session()` bestimmt die laufende Session über den Commit-Zustand der Session-Datei statt über „höchste + 1". Ohne das hätten alle in `closing-session` Schritt 5 geschriebenen Learnings die Nummer der Folge-Session getragen.

---

**Tests:** 433 (pytest) + Permission-Suite grün. **Neu:** OBS-S114-1 (Zugriffs-Scripte vs. fertige Systeme), OBS-S114-2 (Pflichtlektüre ungefiltert). **Learnings:** LL-S114-1 bis -3. **Countermeasures:** CM-S114-1, CM-S114-2.
