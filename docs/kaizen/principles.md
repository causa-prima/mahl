# Principles

<!--
wann-lesen: Wird automatisch am Session-Start geladen (Startup-Hook).
wann-schreiben: Nach einer Retro oder wenn ein KRITISCH/HOCH-Finding offensichtlich hierher gehört.
Kriterium: Verhaltensregel die in jeder Session gilt – zu querschnittlich für eine einzelne Guideline/Skill.
Einträge wandern hierher aus lessons_learned.md oder countermeasures.md (wenn BEWÄHRT + dauerhaft relevant).
-->

## Review-Prozess

- **Reviewer-Agenten stets ohne Iterations-Vorwissen beauftragen.**
  Jeder Review-Agent erhält ausschließlich den aktuellen Code – keinen Kontext über frühere Review-Runden. Vorwissen dämpft die
  Kritikbereitschaft strukturell – der Reviewer denkt "wurde ja schon reviewt".

- **Review-Agent-Outputs auf semantische Korrektheit prüfen, nicht blind übernehmen.**
  Vor jeder Übernahme eines Agent-Vorschlags prüfen: Ist die Begründung stichhaltig, oder klingt
  sie nur plausibel? Umsetzbar ≠ inhaltlich korrekt.

- **Findings ohne Zwischen-Nachfrage abarbeiten.**
  Beim Abarbeiten einer Finding-Liste (z.B. review-code/review-docs, implementing-scenario Schritt 5)
  nach jedem umgesetzten Finding kurz bestätigen und **sofort** zum nächsten übergehen – kein
  Pause-und-Fragen (User hat das explizit so gewünscht). **Ausnahme – invalide Findings** (nach
  Verifikation nicht haltbar): kurz erklären, warum der Reviewer darauf gekommen sein könnte und was
  ich evtl. übersehen habe, **dann** beim User nachfragen, bevor weitergearbeitet wird.

## Prozess-Disziplin

- **Guidelines aktiv auf den konkreten Fall anwenden.**
  Der häufigste Fehlerursprung ist nicht fehlendes Wissen, sondern fehlendes Anwenden.
  Hooks und Pflicht-Schritte in Skills sind zuverlässiger als Lese-Disziplin.

- **Deterministische Skill-Schritte mechanisieren.** Beim Schreiben/Ändern eines Skills prüfen, ob
  ein deterministischer Schritt (Session-Nummer bestimmen, Status setzen, archivieren …) statt
  freihändig besser als Script liefe (Token↓, Varianz↓). Details: `workflow-auditor.md` Dim. 5.

## Doku & Referenzen

- **Single Source of Truth: Information am passendsten Ort, sonst referenzieren.**
  Jede Information lebt an *einer* Stelle – dem dafür passendsten Dokument – und dort so
  ausführlich, dass sie **ohne Vorwissen/Session-Kontext** verständlich ist. Andere Stellen
  **referenzieren** diese Quelle (eine Kurzzusammenfassung ist erlaubt, eine Kopie nicht –
  Kopien driften). Jede referenzierte Stelle braucht einen **leicht auffindbaren Anchor**
  (grep-barer Marker / Heading-Text / ID – **keine** „Sektion N"-/Zeilen-Position, die stale wird;
  Zeilennummern nur für read-only-Dateien wie Session-Logs). Ändert man eine referenzierte Stelle,
  **prüfen, ob die referenzierenden Stellen mitgepflegt werden müssen.**

- **Referenzen laufen von volatil → stabil, nie umgekehrt.**
  Eine stabile Quelle (z.B. ADR) darf **keine** volatile Stelle referenzieren (z.B. `open-questions.md`,
  die bei Lösung gelöscht wird) – sonst dangelt die Referenz, sobald die volatile Stelle verschwindet.
  Die volatile Stelle referenziert die stabile; relevante Informationen leben (auch) in der stabilen Quelle.
  Mechanisch abgesichert in beide Richtungen: `check-ref-direction.py` blockt volatile IDs in stabilen
  Dokumenten (Einzelfall-Escape: `ref-ok`), `check-dangling-refs.py` blockt das Löschen eines TD-/OQ-Eintrags,
  auf den noch verwiesen wird (Escape: `dangling-ok`). Der zweite schließt die Lücke, dass `ref-ok` sonst
  ein stummes Opt-out bliebe – einmal gesetzt, nie wieder geprüft.

- **Zustandsdokumente tragen nur den offenen/aktuellen Zustand – kein Erledigtes.**
  Ein Zustandsdokument (z.B. `AGENT_MEMORY.md` „Nächste Prioritäten", `tech-debt.md`, `open-questions.md`,
  der `NEU`-Pool in `observations.md`) beschreibt, was **offen** ist – kein Changelog. Zwei Richtungen, beide Pflicht:
  **(a) präventiv** – nichts Erledigtes hineinschreiben (Einträge vorwärtsgerichtet formulieren, nicht „erledigt in run-X");
  **(b) kurativ** – ist ein Eintrag erledigt, wird er **aus dem Dokument entfernt** (er lebt in git-Historie / Session-Log /
  Archiv weiter), nicht als „erledigt"-Notiz stehengelassen. Weil solche Dokumente laufend geräumt werden, sind ihre
  Einträge/IDs volatil → an Verweisstellen die nötige Info **inlinen** oder nur auf **stabile** Artefakte (ADR, Guideline)
  verweisen (siehe Prinzip „volatil → stabil" oben; die syntaktischen Guards dafür stehen dort).

## Kommunikation & Argumentation

- **"Unterstützt" ≠ "beweist" – Empirie vor Behauptung, Empfehlung und Fertig-Erklärung.**
  Vor jeder Aussage oder Handlung, die auf angenommenem Tool-/Prozess-Verhalten beruht – eine
  Behauptung, eine Empfehlung, ein „fertig", oder das Verlassen auf einen dokumentierten
  Befehl/Snippet – prüfen: Garantiert der Mechanismus das, oder erleichtert er es nur? Ist ein
  empirischer Check machbar (Befehl real ausführen, am echten Datensatz, am frischen Agenten),
  erst verifizieren. Gesichert ist eine Aussage über externes Tool-Verhalten nur, wenn sie auf
  einem konkreten Tool-Call dieser Session basiert – alles andere proaktiv als unverified
  kennzeichnen und Verifizierung anbieten, nicht warten bis der User nachfragt.
  Zwei Tarnungen, die den Selbst-Check aushebeln:
  **(a) Rechnen ist keine Messung.** Werden zitierte Zahlen addiert, geteilt oder ins Verhältnis
  gesetzt, war der Tool-Call das Rechnen – nicht die Erhebung. Das Ergebnis ist abgeleitet und
  erbt jeden Fehler der Quelle; es so zu nennen ist Pflicht, sonst entfällt die Gegenprobe.
  **(b) Eine Vorschrift beschreibt nicht die Praxis.** Was ein Skill, eine Guideline oder ein
  Prozessdoc anordnet, sagt nichts darüber, ob es befolgt wird. Bevor Kosten oder Nutzen einer
  Regel beziffert werden: am Bestand prüfen, ob sie greift.
  **(c) Redaktionsarbeit fühlt sich nicht wie eine Behauptung an.** Doku schreiben, Zustand
  ablegen, Information platzieren – dort springt der Selbst-Check nicht an, obwohl jeder
  dokumentierte Befehl eine Behauptung ist und jede Ablage eine über ihre Wiedervorlage. Drei
  Fragen: Befehl in dieser Session ausgeführt (sonst als ungeprüft kennzeichnen)? Bezeugt die
  Quelle einen *Versuch* oder eine *Ausführung*? Welcher Mechanismus legt das Abgelegte wieder
  vor – verträgt der Zielstatus ihn?
  Gegenprobe für alle drei: Widerspricht die eigene Rechnung einer vorliegenden Messung um
  Größenordnungen, ist zuerst die Rechnung verdächtig.

- **Die Gegenprobe: das Gegenteil herstellen und prüfen, ob es auffällt.**
  Ein grünes Ergebnis belegt nur, dass der Aufbau lief – nicht, dass er das Fragliche geprüft hat.
  **Vor dem Messen/Testen:** Wie sähe es aus, wenn das Gegenteil wahr wäre? Zeigt der Aufbau
  Erfolg und Misserfolg nicht **unterscheidbar**, trägt das Ergebnis nichts – Testdaten, Mutant
  und Fixture danach wählen, nicht nach Verfügbarkeit.
  **Nach dem Bauen oder Ändern eines Prüfmechanismus** (Hook, Gate, Wrapper, Audit, Guard-Test):
  ihn einmal absichtlich brechen und bestätigen, dass er anspringt – und fragen, wodurch er selbst
  abgesichert ist. Ein Mechanismus, der nichts prüft, fällt lautlos aus: Sein Ausfall löst per
  Definition nichts aus.

- **Vollständige Zerlegung vor Schluss/Empfehlung.**
  Bevor ein Schluss, eine Empfehlung oder eine abgeleitete Anforderung steht, den relevanten
  Raum **explizit zerlegen** und jede Dimension prüfen – nicht den auffälligsten Teil für das
  Ganze nehmen. Konkrete Auslöser: Quantoren in Akzeptanzkriterien („alle", „jeder") sind eine
  **eigene** Prüfdimension; bei Kosten-/Trade-off-Vergleichen **alle** Pfade aufzählen
  (z.B. Injektion + Lesen + Schreiben), bevor eine Empfehlung steht.
