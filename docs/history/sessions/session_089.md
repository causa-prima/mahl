# Session 089 – 2026-06-18

**Phase:** SKELETON
**Fokus:** WSL-native Toolchain-Migration (.NET + Node nativ, Repo auf ext4)

> **Hinweis:** Retroaktiv in S090 rekonstruiert – aus Commit `0a8d1ee` **und** dem Session-Transkript (alter Projekt-Slug `-mnt-c-Users-kieritz-source-repos-mahl`, Datei `62e73a90…`, endet 23:50 zum Commit). S089 war eine Infrastruktur-/Toolchain-Session ohne produktiven Feature-Code.

## Auslöser / Diagnose

Im alten Setup lagen `node`/`npm` in WSL nur als **Windows-Shims**: `which node` → `~/bin/node`, aber `file` meldete `PE32+ executable for MS Windows` (byte-identisch zur Windows-`node.exe` aus `/mnt/c/nvm4w/…`); `npm` zeigte auf die Windows-nvm4w-Installation. Aus WSL heraus war das kaputt → npm lief bis dahin via `cmd.exe /c`, analog zu dotnet.

Zwei Kernbefunde trieben die Migration:
1. **`/mnt/c` ist der Performance-Killer:** Repo auf dem Windows-Dateisystem über den WSL2-Mount → File-I/O (Build, Test-Läufe, Vite-HMR, File-Watching) drastisch langsamer als natives ext4. *(Gut belegtes WSL2-Allgemeinwissen, auf dieser Maschine bewusst nicht gemessen – als Unschärfe geflaggt.)*
2. **Der Repo-Umzug auf ext4 ist Voraussetzung, nicht optionaler Extraschritt:** Ohne ihn wäre die WSL-native Toolchain nur halb so nützlich bzw. teils langsamer. VS Code (WSL-Remote) macht den Umzug schmerzlos.

## Implementiert

### Node (nativ via fnm)
- **Manager `fnm`** (kompiliertes Rust-Binary) statt klassischem `nvm`: nvm sourct ein großes Bash-Script in *jede* Shell (`.bashrc`) → Startup-Penalty (100 ms–>1 s); fnm setzt nur `eval "$(fnm env)"` → vernachlässigbar. Installiert als **direktes GitHub-Release-Binary** (kein `curl|bash`, auditierbar, Checksum), entpackt mit Python `zipfile` (kein `unzip` vorhanden). `fnm 1.39.0`.
- **Node 24 (Active LTS):** Web-verifiziert (Juni 2026: 24 = aktive LTS, 22 = Maintenance, 26 = „Current", erst Okt 2026 LTS). Projekt pinnte vorher **nichts** (kein `.nvmrc`/`engines`/`volta`) → kein Paritäts-Vertrag → direkt auf aktive LTS statt das zufällige Windows-Inkrement nachbauen. `Node v24.17.0` + `npm 11.13.0`. `.nvmrc` mit `24` ins Repo.

### .NET (nativ)
- **.NET 10 SDK** via `dotnet-install.sh` nach `~/.dotnet`.
- **Tools per-Projekt** statt global: lokales Manifest `.config/dotnet-tools.json` (dotnet-ef, dotnet-stryker). Vorher lag Stryker global auf Windows; bewusst auf Projekt-Manifest umgestellt.
- `typescript-language-server` installiert (entblockt OBS-S085-4).

### `.claude`-Scripts & Hooks nativ
- `_util.py` nativ (subprocess statt cmd.exe); Windows-only `check_dotnet_dll_lock` entfernt; alle Wrapper nativ.
- `check-bash-permission.py`: Allow-Liste nativ (dotnet/npm/npx/kill); cmd.exe-Konzept + `sed -i`-CRLF-Sonderfall raus; `test-bash-permission.py` mitmigriert (grün).

### ext4-Umzug & Konsequenzen
- Repo per frischem `git clone` auf ext4 (Endzustand: `~/repos/mahl`). LF-Normalisierung via `.gitattributes`; `launchSettings.json` pinnt Dev-Port **5059** (plain `dotnet run`).
- **Claude-Projekt-Identität** wird aus dem cwd-Slug abgeleitet → neuer Slug, neuer Memory-Pfad (kein offizieller „Projekt umschlüsseln"-Weg).
- **Memory-/Quirk-Bereinigung:** `quirk_case_only_rename.md` + der WSL/Zeilenenden-Eintrag in `MEMORY.md` beschreiben NTFS + `core.ignorecase=true` + CRLF — auf case-sensitivem ext4 entfällt die Prämisse → **nicht migriert, sondern stillgelegt** (Mitnehmen würde aktiv irreführen).

### Doku
- `dev-workflow.md` + `CLAUDE.md`: cmd.exe/NTFS-Abschnitte auf WSL-nativ umgeschrieben.

## Entscheidungen
- **Migration ist KEIN ADR:** Erst als ADR-S089-1 entworfen, nach User-Provokation („ist das wirklich ein ADR?") verworfen. Begründung: Alle ~50 ADRs beschreiben das **gebaute System** (Architektur/Laufzeit/Deps/Artefakt); die Migration ändert nur die **Entwickler-Host-Umgebung** (WSL statt Windows, ext4) → Workflow-/Setup-Entscheidung. Stärkstes Argument: die *inverse* Entscheidung („Node auf Windows via cmd.exe") war nie ein ADR, sondern lebte als Workaround in `dev-workflow.md` + Session-Log (S044). → Dokumentation dort, nicht als ADR.
- **ADR-S089-1 (neu vergeben):** Coverage-Gate **geparkt** — der ext4-Umzug deckte ein Stale-Masking im Gate auf; `coverlet.runsettings` entfernt. Das *ist* eine Build-/Architektur-Entscheidung → legitimer ADR. Begleitet von **TD-S089-1** (Gate reaktivieren).
- **Push auf `main` direkt** akzeptiert (User: außer ihm nutzt niemand das Repo; bei Bedarf später force-löschbar).

## Verifikation
- Nativ grün: build, Backend-Tests, Mutation BE+FE, ESLint, jscpd, EF-Migrationen, E2E 5/5.

## Offene Punkte
- **TD-S089-1** Coverage-Gate reaktivieren (Stale-Masking-Ursache adressieren).
- **OBS-S085-4** TS-LSP-Pilot (Toolchain jetzt entblockt; Bewertung in späterer Retro).
