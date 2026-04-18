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

**Jede Erweiterung erfordert eine explizite Freigabe durch den User.**

Der Agent bereitet dafür eine Anfrage mit folgenden fünf Punkten vor:

1. **Was macht das Paket?** – Kurze Beschreibung des Funktionsumfangs
2. **Was brauchen wir konkret daraus?** – Welcher Teil wird genutzt, was bleibt ungenutzt
3. **Warum nicht selbst schreiben?** – Konkrete Begründung: Komplexität, Typsicherheit, Fehleranfälligkeit, Zeitaufwand
4. **Betrachtete Alternativen** – Welche anderen Pakete oder Eigenimplementierungen wurden evaluiert und warum scheiden sie aus
5. **Paket-Status** – Wer maintained es, wie aktiv (Commit-Frequenz, offene Issues/PRs), wie viele Sicherheitslücken gab es historisch und in letzter Zeit (CVE-Historie)

Erst nach expliziter Freigabe: Eintrag in Allowlist + Begründung in `docs/history/decisions.md` + Installation.

## Allowlist

> Freigegeben Session 044 (2026-04-01). Begründungen in `docs/history/decisions.md`.

### TypeScript / npm

| Paket | Kategorie |
|-------|-----------|
| `vite` | Build |
| `@vitejs/plugin-react` | Build |
| `typescript` | Build |
| `react` | Framework |
| `react-dom` | Framework |
| `@types/react` | Framework |
| `@types/react-dom` | Framework |
| `@mui/material` | UI |
| `@mui/icons-material` | UI |
| `@emotion/react` | UI (Peer) |
| `@emotion/styled` | UI (Peer) |
| `react-router` | Routing |
| `@tanstack/react-query` | Data Fetching |
| `neverthrow` | ROP |
| `vitest` | Testing |
| `@vitest/coverage-v8` | Testing |
| `@testing-library/react` | Testing |
| `@playwright/test` | E2E Testing |
| `happy-dom` | Testing |
| `@stryker-mutator/core` | Testing |
| `@stryker-mutator/vitest-runner` | Testing |
| `@stryker-mutator/typescript-checker` | Testing |
| `msw` | Testing |

### C# / NuGet

| Paket | Projekt |
|-------|---------|
| `Npgsql.EntityFrameworkCore.PostgreSQL` | Infrastructure |
| `Microsoft.EntityFrameworkCore.Design` | Server (Design-Time) |
| `Microsoft.AspNetCore.OpenApi` | Server |
| `OneOf` | Server |
| `Serilog.AspNetCore` | Server |
| `Serilog.Sinks.Console` | Server |
| `Serilog.Sinks.File` | Server |
| `Microsoft.AspNetCore.Mvc.Testing` | Server.Tests |
| `Microsoft.EntityFrameworkCore.InMemory` | Server.Tests |
| `Microsoft.NET.Test.Sdk` | Server.Tests |
| `xunit.v3` | Server.Tests |
| `xunit.runner.visualstudio` | Server.Tests |
| `AwesomeAssertions` | Server.Tests |
| `coverlet.collector` | Server.Tests |

## Enforcement

Hooks blockieren Änderungen an `Client/package.json`, `**/*.csproj` und `docs/DEPENDENCIES.md` durch den Agenten vollständig. Alle drei Dateien müssen vom User manuell bearbeitet werden.
