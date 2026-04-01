# Dependency-Allowlist

<!--
wann-lesen: Bevor ein neues Paket (npm oder NuGet) hinzugefügt wird
kritische-regeln:
  - Nur Pakete aus dieser Liste dürfen verwendet werden
  - Neues Paket → erst Allowlist erweitern + decisions.md → dann installieren
  - Hooks erzwingen diese Regel automatisch (blockieren package.json- und .csproj-Änderungen die nicht-gelistete Pakete einführen)
-->

## Prinzip

Externe Abhängigkeiten haben immer einen Preis: Wartungsaufwand, Sicherheitsfläche, Versionskonflikte, Bundle-Größe. Eine Abhängigkeit wird nur hinzugefügt, wenn **alle** der folgenden Bedingungen erfüllt sind:

1. Die Funktionalität ist nicht in wenigen Zeilen selbst baubar (Faustregel: ≤ 20 Zeilen eigener Code → selbst schreiben)
2. Das Paket ist in dieser Allowlist eingetragen
3. Die Entscheidung ist in `docs/history/decisions.md` begründet

## Prozess: Neues Paket hinzufügen

**Die Allowlist darf vom Agenten nicht eigenständig erweitert werden.** Jede Erweiterung erfordert eine explizite Freigabe durch den User.

Der Agent bereitet dafür eine Anfrage mit folgenden fünf Punkten vor:

1. **Was macht das Paket?** – Kurze Beschreibung des Funktionsumfangs
2. **Was brauchen wir konkret daraus?** – Welcher Teil wird genutzt, was bleibt ungenutzt
3. **Warum nicht selbst schreiben?** – Konkrete Begründung: Komplexität, Typsicherheit, Fehleranfälligkeit, Zeitaufwand
4. **Betrachtete Alternativen** – Welche anderen Pakete oder Eigenimplementierungen wurden evaluiert und warum scheiden sie aus
5. **Paket-Status** – Wer maintained es, wie aktiv (Commit-Frequenz, offene Issues/PRs), wie viele Sicherheitslücken gab es historisch und in letzter Zeit (CVE-Historie)

Erst nach expliziter Freigabe: Eintrag in Allowlist + Begründung in `docs/history/decisions.md` + Installation.

## Allowlist

> **Status: Wird vor dem Rewrite abgestimmt.**

### TypeScript / npm

*(leer – wird vor dem Rewrite befüllt)*

### C# / NuGet

*(leer – wird vor dem Rewrite befüllt)*

## Enforcement

Hooks blockieren Änderungen an `Client/package.json` und `**/*.csproj`, die Pakete einführen, die nicht in dieser Liste stehen.

> **Status: Hook noch nicht implementiert** – wird als Teil des Rewrite-Setups ergänzt.
