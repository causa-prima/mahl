# Principles

<!--
wann-lesen: Wird automatisch am Session-Start geladen (Startup-Hook).
wann-schreiben: Nach einer Retro oder wenn ein KRITISCH/HOCH-Finding offensichtlich hierher gehört.
Kriterium: Verhaltensregel die in jeder Session gilt – zu querschnittlich für eine einzelne Guideline/Skill.
Einträge wandern hierher aus lessons_learned.md oder countermeasures.md (wenn BEWÄHRT + dauerhaft relevant).
-->

<a id="KPI-review-prozess"></a>
## Review-Prozess

- **Reviewer-Agenten stets ohne Iterations-Vorwissen beauftragen.**
  Jeder Review-Agent erhält ausschließlich den aktuellen Code – keinen Kontext über frühere Review-Runden. Vorwissen dämpft die
  Kritikbereitschaft strukturell – der Reviewer denkt "wurde ja schon reviewt".

- **Review-Agent-Outputs auf semantische Korrektheit prüfen, nicht blind übernehmen.**
  Vor jeder Übernahme eines Agent-Vorschlags prüfen: Ist die Begründung stichhaltig, oder klingt
  sie nur plausibel? Umsetzbar ≠ inhaltlich korrekt.

- **Findings ohne Zwischen-Nachfrage abarbeiten.**
  Beim Abarbeiten einer Finding-Liste (z.B. review-code/review-docs, implementing-scenario Review-Loop)
  nach jedem umgesetzten Finding kurz bestätigen und **sofort** zum nächsten übergehen – kein
  Pause-und-Fragen (User hat das explizit so gewünscht). **Ausnahme – invalide Findings** (nach
  Verifikation nicht haltbar): kurz erklären, warum der Reviewer darauf gekommen sein könnte und was
  ich evtl. übersehen habe, **dann** beim User nachfragen, bevor weitergearbeitet wird.

<a id="KPI-prozess-disziplin"></a>
## Prozess-Disziplin

- **Guidelines aktiv auf den konkreten Fall anwenden.**
  Der häufigste Fehlerursprung ist nicht fehlendes Wissen, sondern fehlendes Anwenden.
  Hooks und Pflicht-Schritte in Skills sind zuverlässiger als Lese-Disziplin.

- **Deterministische Skill-Schritte mechanisieren.** Beim Schreiben/Ändern eines Skills prüfen, ob
  ein deterministischer Schritt (Session-Nummer bestimmen, Status setzen, archivieren …) statt
  freihändig besser als Script liefe (Token↓, Varianz↓). Details: [`workflow-auditor.md`, Ressourceneffizienz](../../.claude/agents/workflow-auditor.md#WFA-ressourceneffizienz).

<a id="KPI-doku-referenzen"></a>
## Doku & Referenzen

- **Single Source of Truth: Information am passendsten Ort, sonst referenzieren.**
  Jede Information lebt an *einer* Stelle – dem dafür passendsten Dokument – und dort so
  ausführlich, dass sie **ohne Vorwissen/Session-Kontext** verständlich ist. Andere Stellen
  **referenzieren** diese Quelle (eine Kurzzusammenfassung ist erlaubt, eine Kopie nicht –
  Kopien driften). Jede referenzierte Stelle braucht einen **leicht auffindbaren Anchor**
  (grep-barer Marker / Heading-Text / ID – **keine** „Sektion N"-/Zeilen-Position, die stale wird;
  Zeilennummern nur für read-only-Dateien wie Session-Logs). Ändert man eine referenzierte Stelle,
  **prüfen, ob die referenzierenden Stellen mitgepflegt werden müssen.**

- **Abschnitte tragen Anker, Verweise zeigen auf den Anker – nie auf eine Nummer.**
  Definition per HTML-Anchor über der Überschrift, Verweis als echter Markdown-Link:

      <a id="CGT-result"></a>
      ## Result-Typen
      … siehe [CGT-result](../guidelines/coding-guideline-typescript.md#CGT-result) …

  Präfix = Dokument, Rest ein Slug in Kleinbuchstaben. So bleibt der Verweis **klickbar**
  (GitHub, IDE) und zugleich stabil: Weil der Anker die Identität trägt, dürfen Titel geändert
  und Abschnitte umsortiert werden, ohne dass etwas bricht – der Zwang zu Einschüben wie
  „4b/4c" entfällt. GitHubs Auto-Anchors leisten das nicht, sie hängen am Titeltext.
  Drei Richtungen sind mechanisch abgesichert (`check-anchors.py`): Verweis ohne Ziel, Link
  auf die falsche Datei, und ein gelöschter Anker, auf den noch verwiesen wird. Bestand und
  Vollprüfung: `python3 .claude/scripts/anchors.py list|check`. Einzelfall-Escape:
  `anchor-ok` in der Zeile. Tracker-IDs (TD-/OBS-/ADR-) sind keine Anker.

- **Ein Anker ist eine Abrufeinheit – was zu ihm gehört, muss aus der Gliederung folgen.**
  Seit `doc.py get <ANKER>` existiert, liest ein Agent nicht mehr die Volldatei, sondern genau
  den Abschnitt: bei einem Überschriften-Anker bis zur nächsten gleichrangigen oder
  höherrangigen Überschrift (Unterabschnitte gehören dazu), bei einem Absatz-Anker nur dessen
  Block. Damit wird die Gliederung **maschinell wirksam** – ein Nachsatz hinter dem Block, der
  inhaltlich dazugehört, fehlt beim Abruf, und zwar unbemerkt. Beim Schreiben gilt deshalb:
  Braucht ein Gedanke mehr als seinen Absatz, bekommt er eine Überschrift, keinen zweiten
  Absatz. Bestand sichten: `python3 .claude/scripts/doc.py audit` (Teil von `review-docs`).
  Nicht behoben wird das je durch eine großzügigere Abrufregel – eine Heuristik, die schlechte
  Gliederung glattbügelt, verbirgt sie auch vor dem menschlichen Leser.

- **Abschnitte, Regeln und Schritte bekommen Namen, keine Nummern.**
  Eine selbstvergebene Nummer ist eine *zweite Adresse* neben dem Anker – und nur der Anker
  wird geprüft. Sie wird bei jeder Umsortierung still falsch; in S124 lagen zwei solche
  Verweise bereits tot im Bestand („kaizen Schritt 5" für einen Schritt 7, „Script-Output
  Abschnitt 9" ohne Entsprechung). Der Name leistet zudem mehr: „REFACTOR" sagt, wohin man
  springt, „Phase 3" nur, wie weit. Gilt für Überschriften (`## Findings präsentieren`),
  Verweistexte (`[Findings präsentieren](#KZN-…)`) und fette Absatz-Leads (`**Rolle ≠ Typ**`).
  **Legitim bleibt allein fremdbestimmte Nummerierung** – von einer externen Autorität
  vergeben (RFC-Abschnitt, Gesetzesparagraph, fremde Spec). *Nicht* legitim ist „steht in
  einer anderen Datei": Eine ADR-Punktnummer schreiben dieselben Autoren wie eine
  Abschnittsnummer. Ausgenommen sind Markdown-Ordered-Lists – dort zählt Markdown selbst
  weiter, solange kein Verweis von außen auf eine Position zeigt. Mechanisch abgesichert
  (`check-ordinale.py`, Bestand: `python3 .claude/scripts/ordinale.py`); Einzelfall-Escape:
  `ordinal-ok` in der Zeile.

- **Ein Filter findet nur, woran beim Bauen gedacht wurde – Bestände werden gesichtet, nicht gefiltert.**
  In S124 versagten vier aufeinander aufbauende Suchnetze am selben Punkt: Jedes kodierte die
  Wortliste, die gerade im Kopf war („Gate" fehlte, dann „Dimension", dann „Agent", zuletzt
  „Migrationsschritt"). Jede Runde meldete sauber, und jede folgende Sichtung fand neue Fälle
  – zuletzt im Prüfwerkzeug selbst. Konsequenz, zweigeteilt: Für den **Neuzugang** ist ein
  Filter richtig (er läuft bei jedem Edit, Lücken fallen mit der Zeit auf). Für einen
  **bestehenden Bestand** ist er es nicht – dort trägt nur vollständiges Sichten, notfalls
  klassenweise: alles aufnehmen, Klassen mit Stichprobenbeleg abziehen, den Rest ansehen.
  Wer eine Klasse ohne Beleg abzieht, hat wieder gefiltert.

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

<a id="KPI-kommunikation"></a>
## Kommunikation & Argumentation

**Vier der folgenden Regeln sichern dieselbe Kette – von der Frage über die Erhebung zur
Aussage – an je einer Bruchstelle, und stehen unten in dieser Reihenfolge:** gar nichts erhoben
(„Unterstützt ≠ beweist"), am untauglichen Aufbau erhoben („Die Gegenprobe"), nur über einen Teil
des Raums erhoben („Vollständige Zerlegung"), korrekt erhoben und in einer anderen Größe berichtet
(„Die berichtete Größe ist die gemessene"). Wer einen Fall einordnet, bestimmt **zuerst die
Bruchstelle** – die vier überschneiden sich inhaltlich stark, und ohne diesen Schritt landet ein
Fall beliebig bei einer von ihnen. Jede trägt im Tracker eine eigene Maßnahme, deren
Rückfallzählung nur bei eindeutiger Zuordnung etwas wert ist.

- **Eine Tracker-ID nie nackt nennen.**
  Wer den Volltext hat, ist der Agent – der User müsste ihn heraussuchen. Erstnennung eines
  Eintrags (OBS/LL/TD/OQ/ADR): ID + Kurztitel + zwei, drei Sätze, die den Punkt verständlich
  machen und eine qualifizierte Nachfrage erlauben. Jede weitere Nennung: ID + **derselbe**
  Kurztitel, auch wenn der User selbst nur die ID schreibt – der Name hält im Gespräch fest,
  wofür die Ziffer steht. Der Kurztitel ist der **Titel** des Eintrags; trägt der den Punkt
  nicht, Alternativen vorschlagen und die Wahl per `--titel` zurückschreiben, statt einen
  zweiten Namen danebenzustellen (der veraltete still und behauptete dann Falsches).

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

- **Vor dem Ausgeben eines Prüfergebnisses fragen, ob die Prüfung hätte anschlagen können.**
  Dieselbe Bruchstelle wie die Gegenprobe, eine Ebene höher: Dort fällt das Werkzeug aus, hier
  war schon die **Wahl** des Werkzeugs untauglich. Ein grünes Ergebnis fühlt sich wie ein Beleg
  an, auch wenn der Test seinen Gegenstand nie berührt hat (S124: ein Diff nach `TODO|FIXME`
  durchsucht, um Vollständigkeit zu belegen – bei Arbeit, die solche Marker nie setzt).
  Gegenfrage vor jeder Aussage: *Hätte dieses Ergebnis anders ausgesehen, wenn der Fehler
  vorläge?*

- **Vollständige Zerlegung vor Schluss/Empfehlung.**
  Bevor ein Schluss, eine Empfehlung oder eine abgeleitete Anforderung steht, den relevanten
  Raum **explizit zerlegen** und jede Dimension prüfen – nicht den auffälligsten Teil für das
  Ganze nehmen. Konkrete Auslöser: Quantoren in Akzeptanzkriterien („alle", „jeder") sind eine
  **eigene** Prüfdimension; bei Kosten-/Trade-off-Vergleichen **alle** Pfade aufzählen
  (z.B. Injektion + Lesen + Schreiben), bevor eine Empfehlung steht.

- **Die berichtete Größe ist die gemessene – sonst ist es keine Messung mehr.**
  Letzte Bruchstelle der Kette, und die unauffälligste: Erhoben wurde korrekt, berichtet wird
  eine andere Größe. Der Fehler fällt nicht auf, weil beide Zahlen plausibel klingen und in
  dieselbe Richtung zeigen. Drei Fragen vor jeder Zahl, die in eine Aussage eingeht:
  **(1) Zähleinheit** – was genau ist *ein* Treffer, und kann *ein* Ereignis mehrere erzeugen?
  (S125: 31 Vorkommen der Agenda-Injektion, verteilt auf 11 Session-Logs, wurden als „30
  Session-Starts" berichtet – Resume, `/clear` und manuelle Aufrufe erzeugen je einen Treffer.
  Damit fiel das tragende Argument weg.)
  **(2) Grundgesamtheit und Zeitpunkt** – worauf bezieht sich die Quote, und wurde zwischen
  Erhebung und Bericht daran etwas verändert? Wer eine Menge erst bearbeitet und dann misst,
  misst die Überlebenden (S124: Fehlalarmquote auf dem bereits bereinigten Bestand – 91 % statt
  realer 65–75 %).
  **(3) Zielgröße** – rechnet der Mechanismus, über den geredet wird, in genau dieser Größe?
  Eine Ersatzgröße ist erst zulässig, wenn ihr Zusammenhang mit der Zielgröße selbst belegt ist
  (S126: der Drain rechnet in Score, gemessen wurde Anzahl).
  Ein Muster trifft zudem Zeichenketten, keine Objekte der gemeinten Art: Zählt es in Dokumenten,
  die über den gesuchten Gegenstand *schreiben* (Logs, Retros, Archive), sind diese vor dem Zählen
  auszuschließen – und die Treffer sind anzusehen, nicht nur ihre Anzahl.
