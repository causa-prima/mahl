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

## Prozess-Disziplin

- **Guidelines aktiv auf den konkreten Fall anwenden.**
  Der häufigste Fehlerursprung ist nicht fehlendes Wissen, sondern fehlendes Anwenden.
  Hooks und Pflicht-Schritte in Skills sind zuverlässiger als Lese-Disziplin.

## Kommunikation & Argumentation

- **"Unterstützt" ≠ "beweist" – Präzision bei Mechanismus-Behauptungen.**
  Vor einer Behauptung über das Verhalten eines Tools oder Prozesses prüfen: Garantiert der
  Mechanismus das, oder erleichtert er es nur? Starke Behauptungen erst nach Verifikation.
  Behauptungen über externes Tool-Verhalten sind nur dann gesichert wenn sie auf einem
  konkreten Tool-Call dieser Session basieren – alles andere proaktiv als unverified
  kennzeichnen und Verifizierung anbieten, nicht warten bis der User nachfragt.
