# Befehlslaufzeiten

> **Zweck:** Regelmäßig ausgeführte Befehle mit ihren Laufzeiten im Blick behalten.
> Ziel: Am Phasen-Ende prüfen, ob es schnellere Alternativen gibt.
>
> **Pflege:** Bestehende Zeilen aktualisieren – für jeden Befehl genau ein Eintrag.
> Einmalige Befehle gehören nicht hier rein.

| Befehl | Zweck | Dauer normal | Dauer max | Notizen / Alternativen |
|--------|-------|-------------|-----------|------------------------|
| `dotnet build` | Kompilierung prüfen | – | – | – |
| `python3 .claude/scripts/dotnet-test.py` | Alle Tests | – | – | **WSL/Windows Cache-Konflikt:** Nach Dateiänderungen via WSL schlägt `dotnet test` (mit Build) wegen MSB3492 fehl. Zuverlässiger Workflow: `dotnet build Server/mahl.Server.csproj` → `dotnet build Server.Tests/mahl.Server.Tests.csproj` → dann Script mit `--no-build` (falls künftig unterstützt) oder Build-Fehler ignorieren. Bei DLL-Sperr-Fehler (Copying file...) kurz warten und nochmal. |
| `python3 .claude/scripts/dotnet-stryker.py --mutate ...` | Mutation Testing (eine Datei) | – | – | – |
| `python3 .claude/scripts/dotnet-stryker.py` | Mutation Testing (vollständig) | – | – | – |
| `npm run build` | Frontend-Build | – | – | – |
| `npm run test` | Frontend-Tests | – | – | – |
| `docker-compose up -d` | DB starten | – | – | – |
