---
name: committing
description: >
  Commit, Amend und Push erstellen – mit Gesamtprüfung des ganzen Diffs unmittelbar vorher,
  verbindlicher Befehlsform und abgesichertem Push. Verwende diesen Skill vor JEDEM
  `git commit`, `git commit --amend` und `git push`, auch wenn der Commit trivial wirkt: Er
  enthält die Gesamtprüfung, die ohne ihn ausfällt. Greift auch bei beiläufiger Formulierung
  ohne das Wort „Commit" – „sichere den Stand", „ins Repo damit", „push das", „nimm das noch
  in den letzten Commit". closing-session und implementing-scenario rufen ihn für ihren
  Commit auf.
user-invocable: true
---

# Commit und Push

Der aufrufende Workflow bestimmt, **was** in der Nachricht steht (`closing-session`: Inhaltsregel
und Session-Marke; `implementing-scenario`: Lauf-Betreff). Dieser Skill regelt, **wie** committet
wird – und dass vorher der ganze Stand geprüft ist.

<a id="CMT-gesamtpruefung"></a>
## Gesamtprüfung – unmittelbar vor dem Befehl

**Warum:** Die Prüfungen während der Arbeit – Hooks je Edit, Selbstcheck und Auditoren je
Änderung – sehen nie den ganzen Stand. Was dabei durchrutscht, ist dateiübergreifend: dieselbe
Aussage an mehreren Stellen, weil jede Iteration sie dort ergänzt hat, wo sie gerade war; ein
Verweis in die falsche Richtung; ein Rückfall, als neuer Fall erfasst. Sichtbar wird das erst im
Gesamt-Diff.

**Wann:** Nach der letzten inhaltlichen Änderung – also auch nach Review-Fixes, Tracker-Einträgen,
Lessons und AGENT_MEMORY – und direkt vor dem Befehl. Kommt danach noch etwas hinzu, gilt die
Prüfung für das Neue erneut. Ein Amend ist ein Commit und braucht sie ebenso.

**Wie:** Stagen, dann `git diff --cached` vollständig lesen, dazu den Entwurf der Nachricht – nicht
Datei für Datei aus dem Gedächtnis. Drei Fragen, Befunde sofort beheben und neu stagen:

- **Überflüssig?** Steht eine Aussage mehrfach, gehört sie an die passendste Stelle, die anderen
  verweisen ([Single Source of Truth](../../../docs/kaizen/principles.md#KPI-doku-referenzen)).
  Wiederholt ein Kommentar eine Begründung, die schon woanders steht? Lässt sich etwas kürzen, ohne
  an Präzision oder Wirkung zu verlieren?
- **An der richtigen Stelle?** Tracker nach der [Ablage-Tabelle](../../../CLAUDE.md#CLA-ablage);
  Verweise laufen von volatil nach stabil; ein neuer LL/OBS ist womöglich der Rückfall oder die
  Dublette eines bestehenden. Stimmt jede Behauptung in Doku und Kommentar mit dem, was
  ausgeführt oder gemessen wurde?
- **Nur vorwärtsgerichtet?** Zustandsdokumente tragen nichts Erledigtes – es wird entfernt, nicht
  als erledigt markiert ([Zustandsdokumente](../../../docs/kaizen/principles.md#KPI-doku-referenzen)).
  Jeder Verweis auf eine Session (`S134`) oder einen Tracker-Eintrag (OBS, LL, TD, OQ, ADR) muss
  seinen Platz verdienen: Erklärt er etwas, das ohne ihn unverständlich bliebe – oder erzählt er
  nur, woher etwas kommt? Entstehungsgeschichte gehört in die Commit-Nachricht. In Code, Doku und
  Skills altert sie und schickt den Leser zu einer Quelle, die er zum Verstehen nicht braucht.
  Eine ADR, die die Begründung trägt, bleibt; „seit S089" oder „Anlass: OBS-S…" fällt weg.
  Erzählte Herkunft kommt auch ohne ID aus: „vorher", „bisher", „seit", „früher",
  „ursprünglich". Beschreibt „bisher" den heutigen Stand („bisher für Button"), ist es in Ordnung.
  Finden lässt sich beides in den hinzugefügten Zeilen – IDs, Session-Nummern, diese Wörter:
  `git diff --cached -U0 | grep '^+'` und darin suchen (beim Amend `git diff --cached HEAD~1 -U0`,
  sonst fehlt der Inhalt des ersetzten Commits). Jeder Treffer wird angesehen; die Suche findet
  Kandidaten, sie entscheidet nicht.

<a id="CMT-befehl"></a>
## Stagen und Befehl

`git status` prüfen, jede zugehörige Datei einzeln stagen (`git add <datei>`). Nicht `-A`: Das
nimmt mit, was zufällig im Arbeitsbaum liegt. Nicht `-f`: Das überstimmt `.gitignore`, das genau
solche Dateien fernhält. Dann:

```
git commit -F - <<'EOF'  # --allow-once
<Betreff, höchstens 72 Zeichen>

<Rumpf>

Co-Authored-By: <MODELLNAME> <noreply@anthropic.com>
EOF
```

- `git commit` ist eine User-Aktion; der Marker `# --allow-once` holt die einmalige Freigabe. Er
  steht in der **ersten** Zeile: Die Zeile `EOF` darf nichts außer dem Endmarker enthalten, sonst
  endet der Heredoc nicht.
- `<MODELLNAME>` kommt aus dem System-Kontext.
- Ohne aufrufenden Workflow (ad hoc): Betreff sagt, was sich geändert hat; der Rumpf ist nicht
  leer. Der `commit-msg`-Hook prüft Betreff-Länge und – falls vorhanden – die Session-Marke.

<a id="CMT-amend-push"></a>
## Amend und Push

Beides nur auf ausdrückliche Ansage des Users, je Vorgang: Ein Amend schreibt Historie um, ein
Push veröffentlicht – beides lässt sich nicht still zurücknehmen. Eine frühere Freigabe gilt
deshalb nicht für den nächsten Vorgang.

- **Amend:** `git commit --amend -F - <<'EOF'  # --allow-once`, die Nachricht vollständig neu
  angeben. Gesamtprüfung vorher, für alles seit dem letzten Commit.
- **Push:** `git push origin <branch>  # --allow-once`. War der Commit schon gepusht und wurde
  ersetzt: `git push --force-with-lease=<branch>:<alter SHA> origin <branch>  # --allow-once` –
  nie nacktes `--force`. Der Lease überschreibt nur, wenn auf dem Server noch genau der erwartete
  Stand liegt.
