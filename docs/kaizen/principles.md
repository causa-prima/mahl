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

## Doku & Referenzen

- **Single Source of Truth: Information am passendsten Ort, sonst referenzieren.**
  Jede Information lebt an *einer* Stelle – dem dafür passendsten Dokument – und dort so
  ausführlich, dass sie **ohne Vorwissen/Session-Kontext** verständlich ist. Andere Stellen
  **referenzieren** diese Quelle (eine Kurzzusammenfassung ist erlaubt, eine Kopie nicht –
  Kopien driften). Jede referenzierte Stelle braucht einen **leicht auffindbaren Anchor**
  (grep-barer Marker / Heading-Text / ID – **keine** „Sektion N"-/Zeilen-Position, die stale wird;
  Zeilennummern nur für read-only-Dateien wie Session-Logs). Ändert man eine referenzierte Stelle,
  **prüfen, ob die referenzierenden Stellen mitgepflegt werden müssen.**

## Kommunikation & Argumentation

- **"Unterstützt" ≠ "beweist" – Empirie vor Behauptung, Empfehlung und Fertig-Erklärung.**
  Vor jeder Aussage oder Handlung, die auf angenommenem Tool-/Prozess-Verhalten beruht – eine
  Behauptung, eine Empfehlung, ein „fertig", oder das Verlassen auf einen dokumentierten
  Befehl/Snippet – prüfen: Garantiert der Mechanismus das, oder erleichtert er es nur? Ist ein
  empirischer Check machbar (Befehl real ausführen, am echten Datensatz, am frischen Agenten),
  erst verifizieren. Gesichert ist eine Aussage über externes Tool-Verhalten nur, wenn sie auf
  einem konkreten Tool-Call dieser Session basiert – alles andere proaktiv als unverified
  kennzeichnen und Verifizierung anbieten, nicht warten bis der User nachfragt.
