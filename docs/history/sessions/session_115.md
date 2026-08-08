# Session 115 – 2026-08-08/09

**Phase:** SKELETON · **Story:** US-904 (alle Läufe implementiert)

Kein Produktionscode. Dritter OBS-Drain in Folge, weiter vor der fälligen Retro. Backlog 22 → 16 drainbar: fünf Einträge aufgelöst, vier auf Wiedervorlage mit belastbarem Re-Trigger, einer um eine Ausprägung erweitert. Sechs Fixes entstanden außerhalb des Drain-Satzes, weil sie bei der Arbeit auffielen – darunter eine Gate-Lücke an der sicherheitsrelevantesten Datei und ein stiller Korruptionspfad im Tracker-Tooling. Tests 433 → 494. Prägend für den Verlauf: fünf User-Korrekturen nach einem einzigen Muster (→ LL-S115-1).

---

## Block A – fällige Wiedervorlagen (OBS-S085-3, OBS-S085-4, OBS-S091-2)

Alle drei trugen vorab definierte Bewertungskriterien, die jetzt messbar wurden.

**OBS-S085-3** – Filter-Quote erstmals **gemessen statt gerechnet**. `tool-usage.py` bekam `--since`: Der volle Zeitstempel stand längst im Log, die Auswertung gruppierte ihn nur auf den Monat und verwarf den Tag, weshalb ein Stichtag mitten im Monat (der S109-Umbau fiel auf den 29.07.) nicht schneidbar war. Ergebnis ab Umbau-Commit: **110 Läufe, 105 gefiltert = 95 %** gegen Basislinie 83 %. Damit ist das Kriterium erfüllt und die Gewohnheits-These bestätigt. Gebaut wurde der **Rewrite statt des Deny** (User-Entscheid): `strip_wrapper_filter()` entfernt Filter-Pipes hinter Wrapper-Aufrufen via `updatedInput`, mit Hinweis auf `--verbose`. Begründung gegen das Deny: Subagenten starten immer frisch und können über Sessions nicht umlernen – ein Deny kostet sie jede Session erneut eine Runde. Deny bleibt Eskalationsstufe.

**OBS-S085-4** – vierte Pilot-Runde. Die S109-Sichtbarkeitsmaßnahme wurde im Bestand **verifiziert** (LSP-Block steht prominent in `frontend-layer-implementer.md`), doch danach liefen nur zwei TS-Sessions – die vorab definierte Mindest-Evidenz von drei ist nicht erreicht, ein Urteil wäre das ausdrücklich ausgeschlossene Urteil auf Null-Daten. Post-S109 null Calls in Implementierung.

**OBS-S091-2** – Re-Trigger eingetreten (vier Wrapper-Fehlschläge in S111 nach der `--prefix`-Freigabe), der S109-Schluss aber nur unvollständig, nicht falsch: Drei der vier cd-Gründe blockt der Hook längst, belegt im Deny-Log. Offen war allein das typecheck-npm-Script, dessen historische Ursache im OBS-Archiv steht (`--prefix` war damals gesperrt). Gebaut wurde `cd_npm_conflict()` – kein Wrapper (User-Einwand, deckungsgleich mit dem S099-Entscheid: der Erfolgsfall sind drei Zeilen, es gibt nichts zu kuratieren) und kein Hook-Rewrite.

**Terminierung neu gedacht:** Beide Wiedervorlagen hängen nicht mehr an einer Session-Nummer, sondern an Ereignissen (≥ 100 Wrapper-Läufe; drei Sessions mit real auf TS-Code laufendem Implementer/Auditor), weil zwischen dem 30.07. und heute in drei Sessions nur **6** Wrapper-Läufe anfielen – ein Kalendertermin hätte erneut auf Null-Daten geurteilt.

## Block B – Wert-Lane (OBS-S108-6, OBS-S112-8, OBS-S111-3, OBS-S108-1, OBS-S112-7, OBS-S114-2)

**OBS-S108-6** – `open-questions.md` hatte als einziger Tracker keinen Lese-Trigger; alle fünf Verweise darauf sind Schreib-Verweise, vier Fragen lagen 14–32 Sessions. Angehängt an den bestehenden Vorschlag (`obs-drain.py`, Sektion „Offene Fragen") statt als eigenes Script mit eigener Injektion – die Alters-Logik existierte dort schon. Neues optionales `Fällig: S<NNN>` im OQ-Format; ein gesetzter Termin unterdrückt die Alters-Regel, sonst wäre er wirkungslos. Liegende Fragen verhindern zudem das Verdikt „Backlog leer". Abgrenzung dokumentiert: Offene Fragen werden dem **User** vorgelegt, nicht im Drain entschieden.

**OBS-S112-8** – neues Feld `Vorprägung` für schon genanntes Lösungswissen. Die Session lieferte eine Doppel-Evidenz: Die konservierte Zielvorstellung machte den Drain von OBS-S112-7 erst handlungsfähig **und** hatte, agentenformuliert, das Ziel verschoben und wurde als Auftrag gelesen. Der Zwischenvorschlag „Feld + Verifikationspflicht" fiel am User-Einwand, dass `get` den Volltext ausgibt – eine Pflicht *nach* dem Lesen kommt zu spät. Gewählt: ein generelles Feld, beim Standardzugriff **verborgen**, Abruf per `--vorprägung` erst nach eigener Kandidatenbildung. Drei Absicherungen end-to-end verifiziert (Verbergen mit Hinweis, Abruf, `+Vorprägung`-Marker im Drain-Satz) – ohne Marker wäre ein verborgenes Feld so verloren wie ein getilgtes.

**OBS-S111-3** – im Kern-Argument widerlegt: Die Unterscheidung Survived/NoCoverage ging nie verloren, `collect_undetected` trennt sie über `status`. Valide blieb der Rest; die Survivor-Ausgabe zeigt jetzt Zeilenspanne (behebt die Block-removal-Mehrdeutigkeit), Anzahl deckender Tests und `statusReason`. Ein Probelauf gegen echte Report-Objekte deckte auf, dass `statusReason` einen Assertion-Diff mit komplettem DOM-Dump tragen kann – die Fixtures zeigten das nicht; ungekürzt wäre eine Output-Explosion in genau das Script gegangen, dessen Ausgabe S109 gekürzt hat.

**OBS-S108-1** – ADR-Referenzen werden jetzt auch mid-line erkannt (`adr_refs_in_line()`). Am Bestand belegt: drei Zeilen liefern seither zwei Referenzen, die vorher sämtlich unerfasst blieben.

**OBS-S112-7 / OBS-S114-2** – Ziel geschärft und Umfang erhoben, Umsetzung als eigene Session geplant (User-Entscheid: vollständig migrieren). Die Zwischenannahme „bei Skill-Ablaufschritten ist die Nummer echte Semantik" wurde vom User entkräftet; Auflösung ist die Trennung von Nummer und Identität. Kritischer Befund: `implementing-scenario/SKILL.md` (356 Zeilen) und `closing-session/SKILL.md` haben **keine Schritt-Überschriften**, die 30+ Verweise zeigen auf Ziele, die als Struktur nicht existieren. OBS-S114-2 wartet bewusst auf die Anker; die naheliegende Baseline `doc-outline.py` wurde deshalb nicht gebaut.

## Fixes außerhalb des Drain-Satzes

- **Gate-Lücke:** `test-bash-permission.py` lag mit eigenem Runner neben `tests/` und lief in **keinem** Gate – die Datei, die jeden anderen Bypass verhindert, war ungegatet. Über einen pytest-Wrapper eingebunden; Wirksamkeit durch temporäres Brechen nachgewiesen.
- **Stiller Korruptionspfad:** `obs_entry.set_fields` übergab Werte als Regex-Ersetzungstemplate an `re.sub` – ein `\1` in einem Entscheidungstext wäre klanglos durch eine Regex-Gruppe ersetzt worden. Trat real als Abbruch auf.
- **`obs.py --beobachtung-anhängen`:** Der Drain-Skill verlangt Konsolidierung („tragenden Eintrag erweitern"), das Script konnte es nicht – jede Konsolidierung landete zwangsläufig im Hand-Edit.
- **`decisions.py` hatte keine Tests**, obwohl es als qa-check-Schritt 6 läuft; 11 angelegt.
- **`tool-usage.py --since`** und sechs Befehle in `dev-workflow.md` auf `--prefix` (alle real ausgeführt außer `ci`/`update`/`audit fix`).

## Learnings

- **LL-S115-1** (HOCH) – Das Prinzip „Empirie vor Behauptung" wurde bei Messungen penibel befolgt, bei Doku-Änderungen und Ablage-Entscheidungen dagegen nicht angewandt; fünf User-Korrekturen nach diesem Muster. Volltext: `docs/kaizen/lessons_learned.md`.
