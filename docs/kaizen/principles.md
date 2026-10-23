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
  Jeder Review-Agent erhält nur den aktuellen Code, keinen Kontext früherer Review-Runden –
  Vorwissen dämpft die Kritikbereitschaft strukturell („wurde ja schon reviewt").

- **Review-Agent-Outputs auf semantische Korrektheit prüfen, nicht blind übernehmen.**
  Vor jeder Übernahme eines Agent-Vorschlags prüfen: Ist die Begründung stichhaltig, oder klingt
  sie nur plausibel? Umsetzbar ≠ inhaltlich korrekt.

- **Findings ohne Zwischen-Nachfrage abarbeiten.**
  Nach jedem umgesetzten Finding einer Liste (review-code, review-docs, Review-Loop) kurz
  bestätigen und **sofort** zum nächsten – kein Pause-und-Fragen. **Ausnahme – invalide Findings**
  (nach Verifikation nicht haltbar): erklären, wie der Reviewer darauf gekommen sein könnte und was
  ich evtl. übersehen habe, **dann** beim User nachfragen, bevor es weitergeht.

<a id="KPI-prozess-disziplin"></a>
## Prozess-Disziplin

- **Guidelines aktiv auf den konkreten Fall anwenden.**
  Der häufigste Fehlerursprung ist nicht fehlendes Wissen, sondern fehlendes Anwenden.
  Hooks und Pflicht-Schritte in Skills sind zuverlässiger als Lese-Disziplin.

<a id="KPI-doku-referenzen"></a>
## Doku & Referenzen

- **Single Source of Truth: Information am passendsten Ort, sonst referenzieren.**
  Jede Information lebt an *einer* Stelle – dem passendsten Dokument – und dort so ausführlich,
  dass sie **ohne Vorwissen/Session-Kontext** verständlich ist. Andere Stellen **referenzieren**
  sie über einen Anker oder eine ID (Kurzzusammenfassung erlaubt, Kopie nicht – Kopien driften);
  Zeilennummern nur in read-only-Dateien wie Session-Logs. Ändert man eine referenzierte Stelle,
  **prüfen, ob die referenzierenden Stellen mitgepflegt werden müssen.**

- **Abschnitte tragen Anker, Verweise zeigen auf den Anker – nie auf eine Nummer.**
  Definition per HTML-Anchor über der Überschrift, Verweis als echter Markdown-Link:

      <a id="CGT-result"></a>
      ## Result-Typen
      … siehe [CGT-result](../guidelines/coding-guideline-typescript.md#CGT-result) …

  Präfix = Dokument, Rest ein Slug in Kleinbuchstaben. So bleibt der Verweis **klickbar** und
  zugleich stabil: Titel dürfen sich ändern, Abschnitte umsortiert werden. Kaputte Verweise blockt
  `check-anchors.py`. Tracker-IDs (TD-/OBS-/ADR-) sind keine Anker.

- **Ein Anker ist eine Abrufeinheit – was zu ihm gehört, muss aus der Gliederung folgen.**
  `doc.py get <ANKER>` liefert bei einem Überschriften-Anker alles bis zur nächsten gleich- oder
  höherrangigen Überschrift, bei einem Absatz-Anker nur dessen Block. Ein Nachsatz hinter dem
  Block, der inhaltlich dazugehört, fehlt beim Abruf unbemerkt. Deshalb: Braucht ein Gedanke mehr
  als seinen Absatz, bekommt er eine Überschrift, keinen zweiten Absatz.

- **Abschnitte, Regeln und Schritte bekommen Namen, keine Nummern.**
  Eine selbstvergebene Nummer ist eine *zweite*, ungeprüfte Adresse neben dem Anker und wird bei
  jeder Umsortierung still falsch; der Name sagt zudem, wohin man springt, nicht nur, wie weit.
  Gilt für Überschriften, Verweistexte und fette Absatz-Leads. **Legitim ist allein
  fremdbestimmte Nummerierung** (RFC-Abschnitt, Gesetzesparagraph, fremde Spec) – nicht die
  eigene, auch wenn sie in einer anderen Datei steht (ADR-Punktnummern). Markdown-Ordered-Lists
  sind erlaubt, solange kein Verweis von außen auf eine Position zeigt. Abgesichert durch
  `check-ordinale.py`.

- **Ein Filter findet nur, woran beim Bauen gedacht wurde – Bestände werden gesichtet, nicht gefiltert.**
  Ein Suchnetz kodiert die Wortliste, die beim Bauen im Kopf war, meldet sauber und übersieht
  alles andere. Für den **Neuzugang** ist ein Filter richtig (er läuft bei jedem Edit, Lücken
  fallen mit der Zeit auf), für einen **bestehenden Bestand** nicht – dort trägt nur vollständiges
  Sichten, notfalls klassenweise: alles aufnehmen, Klassen mit Stichprobenbeleg abziehen, den Rest
  ansehen. Wer eine Klasse ohne Beleg abzieht, hat wieder gefiltert.

- **Referenzen laufen von volatil → stabil, nie umgekehrt.**
  Eine stabile Quelle (z.B. ADR) darf **keine** volatile Stelle referenzieren (z.B. `open-questions.md`,
  die bei Lösung gelöscht wird) – sonst dangelt die Referenz, sobald die volatile Stelle verschwindet.
  Die volatile referenziert die stabile; Relevantes lebt (auch) in der stabilen Quelle. Abgesichert
  durch `check-ref-direction.py` (volatile IDs in stabilen Dokumenten) und `check-dangling-refs.py`
  (Löschen eines TD-/OQ-Eintrags, auf den noch verwiesen wird).

- **Zustandsdokumente tragen nur den offenen/aktuellen Zustand – kein Erledigtes.**
  Ein Zustandsdokument (z.B. `AGENT_MEMORY.md` „Nächste Prioritäten", `tech-debt.md`, `open-questions.md`,
  der `NEU`-Pool in `observations.md`) beschreibt, was **offen** ist – kein Changelog. Also nichts
  Erledigtes hineinschreiben (vorwärtsgerichtet formulieren, nicht „erledigt in run-X"), und ist ein
  Eintrag erledigt, wird er **entfernt** statt als „erledigt" stehengelassen (er lebt in
  git-Historie, Session-Log, Archiv weiter). Weil solche Dokumente laufend geräumt werden, sind ihre
  IDs volatil: an Verweisstellen die nötige Info **inlinen** oder nur auf **stabile** Artefakte
  (ADR, Guideline) verweisen.

<a id="KPI-kommunikation"></a>
## Kommunikation & Argumentation

Vier der folgenden Regeln sichern je eine Bruchstelle der Kette Frage → Erhebung → Aussage: gar
nichts erhoben („Unterstützt ≠ beweist"), am untauglichen Aufbau erhoben („Die Gegenprobe"), nur
über einen Teil des Raums erhoben („Vollständige Zerlegung"), korrekt erhoben und in einer anderen
Größe berichtet („Die berichtete Größe ist die gemessene").

- **Eine Tracker-ID nie nackt nennen.**
  Den Volltext hat der Agent, nicht der User. Erstnennung eines Eintrags (OBS/LL/TD/OQ/ADR):
  ID + Kurztitel + zwei, drei Sätze, die den Punkt verständlich machen und eine qualifizierte
  Nachfrage erlauben. Jede weitere Nennung: ID + **derselbe** Kurztitel, auch wenn der User nur
  die ID schreibt. Der Kurztitel ist der **Titel** des Eintrags – trägt er den Punkt nicht, einen
  besseren vorschlagen und per `--titel` zurückschreiben, keinen zweiten Namen danebenstellen (der
  veraltete still). Dasselbe gilt für jedes Kürzel, das nur der Agent kennt – Review-Findings
  („A1", „FC-6"), selbst vergebene Befund-Labels, Werkzeug- und Prüfnamen: Eine Frage an den User
  nennt Gegenstand, Problem und Vorschlag ausgeschrieben, das Kürzel höchstens als Zusatz.

- **"Unterstützt" ≠ "beweist" – Empirie vor Behauptung, Empfehlung und Fertig-Erklärung.**
  Beruht eine Behauptung, eine Empfehlung, ein „fertig" oder das Verlassen auf einen dokumentierten
  Befehl auf angenommenem Tool-/Prozess-Verhalten, prüfen: Garantiert der Mechanismus das, oder
  erleichtert er es nur? Ist ein empirischer Check machbar (Befehl real ausführen, am echten
  Datensatz, am frischen Agenten), erst verifizieren. Gesichert ist eine Aussage über externes
  Tool-Verhalten nur durch einen konkreten Tool-Call dieser Session – alles andere proaktiv als
  ungeprüft kennzeichnen und Verifizierung anbieten, nicht warten, bis der User nachfragt.
  Drei Tarnungen, die den Selbst-Check aushebeln:
  **Rechnen ist keine Messung.** Wer zitierte Zahlen addiert, teilt oder ins Verhältnis setzt, hat
  gerechnet, nicht erhoben: Das Ergebnis ist abgeleitet, erbt jeden Fehler der Quelle und muss so
  genannt werden.
  **Eine Vorschrift beschreibt nicht die Praxis.** Was ein Skill, eine Guideline oder ein
  Prozessdoc anordnet, sagt nichts darüber, ob es befolgt wird. Bevor Kosten oder Nutzen einer
  Regel beziffert werden: am Bestand prüfen, ob sie greift.
  **Redaktionsarbeit fühlt sich nicht wie eine Behauptung an.** Beim Doku-Schreiben, Zustand-Ablegen
  und Platzieren springt der Selbst-Check nicht an, obwohl jeder dokumentierte Befehl eine
  Behauptung ist und jede Ablage eine über ihre Wiedervorlage. Drei Fragen: Befehl in dieser
  Session ausgeführt (sonst als ungeprüft kennzeichnen)? Bezeugt die Quelle einen *Versuch* oder
  eine *Ausführung*? Welcher Mechanismus legt das Abgelegte wieder vor – verträgt der Zielstatus ihn?
  Gegenprobe für alle drei: Widerspricht die eigene Rechnung einer vorliegenden Messung um
  Größenordnungen, ist zuerst die Rechnung verdächtig.

- **Die Gegenprobe: das Gegenteil herstellen und prüfen, ob es auffällt.**
  Ein grünes Ergebnis belegt nur, dass der Aufbau lief – nicht, dass er das Fragliche geprüft hat.
  **Vor dem Messen/Testen:** Wie sähe es aus, wenn das Gegenteil wahr wäre? Zeigt der Aufbau
  Erfolg und Misserfolg nicht **unterscheidbar**, trägt das Ergebnis nichts – Testdaten, Mutant
  und Fixture danach wählen, nicht nach Verfügbarkeit.
  **Nach dem Bauen oder Ändern eines Prüfmechanismus** (Hook, Gate, Wrapper, Audit, Guard-Test):
  ihn einmal absichtlich brechen und bestätigen, dass er anspringt – und fragen, wodurch er selbst
  abgesichert ist. Ein Mechanismus, der nichts prüft, fällt lautlos aus.

- **Vor dem Ausgeben eines Prüfergebnisses fragen, ob die Prüfung hätte anschlagen können.**
  Wie die Gegenprobe, eine Ebene höher: Dort fällt das Werkzeug aus, hier war schon seine **Wahl**
  untauglich. Ein grünes Ergebnis fühlt sich wie ein Beleg an, auch wenn die Prüfung ihren
  Gegenstand nie berührt hat (ein Diff nach `TODO|FIXME` durchsucht, um Vollständigkeit zu belegen –
  bei Arbeit, die solche Marker nie setzt). Gegenfrage vor jeder Aussage: *Hätte dieses Ergebnis
  anders ausgesehen, wenn der Fehler vorläge?*

- **Vollständige Zerlegung vor Schluss/Empfehlung – umso gründlicher, je mehr daran hängt.**
  Bevor ein Schluss, eine Empfehlung oder eine abgeleitete Anforderung steht, den relevanten
  Raum **explizit zerlegen** und jede Dimension prüfen und bewerten – nicht den auffälligsten
  Teil für das Ganze nehmen. Was bisher fehlte, war fast immer eine von vier Arten:
  **Quellen** (welche Daten, Logs, Dokumente gibt es – schreibt der Schreiber noch dorthin?),
  **Formen und Pfade** (in welchen Varianten tritt der Fall auf, wer liest die Stelle noch?),
  **Optionen** (trifft ein Argument die anderen Optionen genauso?), **Zeitraum und
  Betriebsart** (enthält das Fenster jede Phase, über die die Aussage spricht?). Die vier sind
  ein Anfang, kein Abschluss – zuletzt fragen, welche Dimension *dieser* Fall darüber hinaus
  hat. Quantoren („alle", „nie", „selten") sind Allaussagen und brauchen den ganzen Raum.
  **Die Gründlichkeit skaliert mit der Folge:** Trägt die Aussage eine User-Entscheidung, das
  Design eines Guards oder etwas schwer Umkehrbares, wird jede Dimension mit einem Beleg
  geprüft (Lauf, Datei, Log), nicht mit einem Argument; was sich nicht prüfen lässt, wird als
  ungeprüft benannt.

- **Die berichtete Größe ist die gemessene – sonst ist es keine Messung mehr.**
  Erhoben wurde korrekt, berichtet wird eine andere Größe – unauffällig, weil beide Zahlen
  plausibel klingen und in dieselbe Richtung zeigen. Drei Fragen vor jeder Zahl, die in eine
  Aussage eingeht:
  **Zähleinheit** – was genau ist *ein* Treffer, und kann *ein* Ereignis mehrere erzeugen? (31
  Agenda-Injektionen in 11 Session-Logs, berichtet als „30 Session-Starts" – Resume, `/clear` und
  manuelle Aufrufe erzeugen je einen Treffer.)
  **Grundgesamtheit und Zeitpunkt** – worauf bezieht sich die Quote, und wurde zwischen Erhebung
  und Bericht daran etwas verändert? Wer eine Menge erst bearbeitet und dann misst, misst die
  Überlebenden (Fehlalarmquote auf dem schon bereinigten Bestand: 91 % statt realer 65–75 %).
  **Zielgröße** – rechnet der Mechanismus, über den geredet wird, in genau dieser Größe? Eine
  Ersatzgröße ist erst zulässig, wenn ihr Zusammenhang mit der Zielgröße selbst belegt ist (der
  Drain rechnet in Score, gemessen wurde Anzahl).
  Ein Muster trifft zudem Zeichenketten, keine Objekte der gemeinten Art: Zählt es in Dokumenten,
  die über den gesuchten Gegenstand *schreiben* (Logs, Retros, Archive), sind diese vor dem Zählen
  auszuschließen – und die Treffer sind anzusehen, nicht nur ihre Anzahl.
