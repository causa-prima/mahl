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

## Hinweise

- **Nach Schritt 4 stoppen.** Nicht weiter nach einzelner Assertion-Form zerschneiden – das
  erzeugt Mikro-Cluster ohne Mehrwert.
- **Singletons bleiben eigene Läufe.** Ergibt der Algorithmus einen Cluster mit nur einem
  Szenario, ihn *nicht* in einen unähnlichen Cluster zwingen, nur um einen Lauf zu sparen –
  das schleppte genau die Heterogenität ein, die wir vermeiden. Ein Singleton ist gewollt,
  kein Versehen. (Tritt natürlich auf, wenn die Story von einer Form nur ein Exemplar hat.)
- **Kein Größen-Deckel.** Ein homogener Cluster mit vielen Fällen ist *ein* parametrisierter
  Batch und braucht keinen Split. Fühlt sich ein Cluster „zu groß" an, wurde eine der Achsen
  aus 1–4 übersprungen – diese anwenden, statt willkürlich zu trennen.
- **Reihenfolge der Läufe:** zuerst der Full-stack-Success-Cluster der zentralen Mutation
  (er baut den Endpoint), darauf dessen Validierungs-Cluster; übrige Capabilities danach. Die
  Reihenfolge ist weich – hart ist nur, dass Validierung auf dem Endpoint des Success-Laufs
  aufsetzt.
- Der einzige Urteilspunkt ist Schritt 1 (welche Aktion = welche Capability). Den Rest bestimmt
  die Form.

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
