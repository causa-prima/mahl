# Szenario-Clustering

Gruppiert die fertigen Szenarien einer User Story in **Implementierungs-Läufe** –
ein Lauf = ein Implementierungs-Durchlauf. Ziel ist nicht „möglichst wenige Läufe",
sondern **möglichst homogene** Läufe.

## Worum es geht

Mehrere Szenarien in einem Durchlauf umzusetzen statt jedes einzeln spart den fixen Overhead,
der pro Durchlauf anfällt. Der Preis ist ein Risiko: je **heterogener** ein Bündel, desto
schwerer fällt es, jede Assertion sauber auf ihr Szenario-Kriterium zurückzuführen – und desto
eher entsteht Code oder ein Test, den kein Kriterium fordert (Gold-Plating).

Der Hebel dagegen ist **Homogenität**, nicht Größe. Ein homogenes Bündel (gleiches Setup,
gleiche Assertion-Form, nur der Input variiert) kollabiert ohnehin zu *einem* parametrisierten
Test – das Mapping ist dann „jede Zeile = eine Input-Partition", trivial zu prüfen, auch bei
vielen Fällen. Ein heterogenes Bündel derselben Größe zwingt dazu, mehrere unabhängige Mappings
gleichzeitig zu halten. Zielfunktion daher: **Homogenität maximieren** – die passende Größe
ergibt sich von selbst.

**Bewusste Abwägung:** Homogenität geht vor Durchsatz. Wo der Algorithmus ein einzelnes
Szenario isoliert, bleibt es ein eigener Lauf (siehe Hinweis „Singletons").

## Algorithmus

Eingabe: alle Szenarien der Story. Ein resultierender Cluster = ein Lauf. Die vier Schritte in
Reihenfolge anwenden:

1. **Nach Capability gruppieren** (aus dem `When` / der Hauptaktion): Lesen/Liste, Anlegen,
   Ändern, Löschen – plus story-spezifische Operationen (z.B. Reaktivierung). Jede Capability
   ist zunächst ein eigener Cluster.

2. **Mutations-Capabilities** (Anlegen/Ändern/Löschen) nach **Ergebnisklasse** trennen:
   - **Validierung** – das `Then` behauptet einen *abgelehnten oder grenzwertigen* Input
     (Fehlermeldung **und** Zustand unverändert).
   - **Success/Verhalten** – das `Then` behauptet eine *erfolgreiche* Mutation oder reines
     Dialog-/UI-Verhalten.

3. **Validierung** weiter splitten – zuerst nach **Form**, dann nach **Feld**:
   - *stateless* (kein Seed, reine Input-Prüfung) vs. *state-driven* (Seed nötig,
     Eindeutigkeit/Konflikt) – unterschiedliches Setup, unterschiedliche Invariante.
   - innerhalb *stateless* nach **Eingabefeld** (Name, Einheit, …).
   - Der **valide Grenzwert** einer Feldregel („genau N akzeptiert") gehört in die Familie
     dieses Feldes – als Boundary-Paar mit dem Reject-Fall, nicht zu Success.

4. **Success/Verhalten** nach **Schicht** splitten:
   - *frontend-only* – kein HTTP-Call / keine Persistenz-Assertion (Dialog öffnen/schließen/
     zurücksetzen, Fokus, Pflichtfeld-Markierung, Pending-Disabled).
   - *full-stack* – behauptet persistierten Zustand / Liste nach realer Mutation.

5. **Zustands-Abhängigkeiten auflösen** – kein weiterer Split, nur Reihenfolge und Zuordnung:
   Notiere je Cluster, welche Lebenszyklus-Zustände seine `Given` **voraussetzen** (Reader) und
   welche seine `Then` **herstellen** (Writer). Prüffrage je Cluster: *Lässt sich sein `Given` mit
   dem, was bis zu diesem Lauf gebaut ist, über die Oberfläche herstellen?* Lautet die Antwort
   nein, hängt der Cluster an einem Zustand, den bis dahin kein Lauf schreibt.
   Regel: **Der Writer-Cluster eines Zustands liegt vor jedem Reader-Cluster desselben Zustands.**
   Bei Verletzung drei Auswege, in dieser Reihenfolge prüfen:
   - **Umordnen** – wenn die Abhängigkeit nur in eine Richtung läuft.
   - **Szenario verschieben** – wenn Reader und Writer sich **gegenseitig** voraussetzen (Zyklus;
     keine Reihenfolge erfüllt dann beide Seiten). Das lesende Szenario gehört in den Lauf, der
     den Zustand schreibt: Es beschreibt die Wirkung *dieser Mutation*, nicht die Grundfunktion
     des lesenden Endpoints.
   - **Zusammenlegen** – wenn beide Cluster ohnehin dieselbe Mutation umkreisen.
   Ohne diesen Schritt entsteht ein Lauf, dessen E2E-Arrangement keinen Weg über die Oberfläche
   hat – er erzwingt dann einen Test-only-Endpoint oder das Vorziehen eines späteren Laufs.

6. **Erstmaligkeiten flaggen** – vor der Implementierung, nicht während:
   Prüfe je Lauf in der festgelegten Reihenfolge: *Was tut dieser Lauf, das noch kein Lauf zuvor
   getan hat?* Führt er den ersten Vertreter einer Klasse ein (erster mutierender
   Single-Resource-Endpoint, erste zweite Seite, erste Liste mit Pagination …), zieht das eine
   **Querschnitts-Policy** nach – Optimistic Concurrency via ETag/If-Match, Navigations-Struktur,
   Ähnliches –, die die feature-orientierte Clusterung nicht abbildet. Benenne sie beim Lauf und
   kläre sie **vor** dessen Implementierung; sonst kommt sie als PLANUNG-Eskalation des
   Schicht-Subagenten mitten im Lauf hoch und erzwingt eine Scope-Diskussion im laufenden
   Betrieb. Bewusst als offene Frage formuliert statt als feste Klassenliste – eine solche Liste
   wäre nie vollständig.

## Hinweise

- **Nach Schritt 4 nicht weiter splitten.** Nicht nach einzelner Assertion-Form zerschneiden – das
  erzeugt Mikro-Cluster ohne Mehrwert. (Schritte 5–6 splitten nicht, sie ordnen und flaggen.)
- **Singletons bleiben eigene Läufe.** Ergibt der Algorithmus einen Cluster mit nur einem
  Szenario, ihn *nicht* in einen unähnlichen Cluster zwingen, nur um einen Lauf zu sparen –
  das schleppte genau die Heterogenität ein, die wir vermeiden. Ein Singleton ist gewollt,
  kein Versehen. (Tritt natürlich auf, wenn die Story von einer Form nur ein Exemplar hat.)
- **Kein Größen-Deckel.** Ein homogener Cluster mit vielen Fällen ist *ein* parametrisierter
  Batch und braucht keinen Split. Fühlt sich ein Cluster „zu groß" an, wurde eine der Achsen
  aus 1–4 übersprungen – diese anwenden, statt willkürlich zu trennen.
- **Reihenfolge der Läufe:** zuerst der Full-stack-Success-Cluster der zentralen Mutation
  (er baut den Endpoint), darauf dessen Validierungs-Cluster; übrige Capabilities danach. Die
  Reihenfolge ist im Übrigen weich – hart sind zwei Bedingungen: Validierung setzt auf dem
  Endpoint des Success-Laufs auf, und die Zustands-Bedingung aus Schritt 5 (Writer vor Reader).
- Der einzige Urteilspunkt in 1–4 ist Schritt 1 (welche Aktion = welche Capability). Den Rest
  bestimmt die Form; Schritte 5–6 kommen danach auf das fertige Clustering.

## Output: Lauf-Kommentar-Tags

Jedes Szenario erhält einen **Kommentar-Tag** direkt oberhalb seiner `@US-NNN-…`-Tag-Zeile
(über etwaigen Erklär-Kommentaren – so bleibt der `@`-Tag adjazent zum `Scenario:`):

```gherkin
  # @run-1 · Anlegen·Success · Full-Stack
  @US-904-happy-path
  Scenario: Zutat anlegen
```

Format: `# @run-<N> · <Cluster-Label> · <Schicht>[ · Singleton]`

- **Frontend-only** / **Full-Stack** – die Schicht des Laufs: *Frontend-only* braucht keinen
  Backend-Subagenten (reines UI-/Dialog-Verhalten), *Full-Stack* berührt Frontend und Backend.
- **Singleton** – ein Lauf mit nur einem Szenario; wird ergänzt, damit klar ist, dass der
  einzelne Eintrag Absicht ist (siehe Hinweise).
- Bewusst ein **Kommentar**, kein echter Gherkin-`@tag`: der Bauplan soll die Spec nicht
  verunreinigen und keine Test-Runner-Tags belegen.
- Greppbar via `# @run-`. `<N>` = Lauf-Nummer = Implementierungs-Reihenfolge.

## Beispiel

`scenario-clustering-example.html` (in diesem Ordner) – interaktive Visualisierung des
Algorithmus an US-904 (31 Szenarien → 11 Läufe, Schritte durchklickbar).
