#!/usr/bin/env python3
"""PreToolUse-Hook: Bash-Kommandos prüfen (deny/allow/ask).

Reihenfolge in check_command:
1. ONE_TIME_MARKER → ask (übersteuert alle anderen Prüfungen inkl. WRONG_APPROACH)
2. Repo-Pfad-Normalisierung (normalize_repo_paths): absoluter Repo-Root-Präfix
   → relativ. Spart den Permission-Retry, den absolute Pfade sonst auslösen
   (OBS-S085-1). Bei Änderung gibt der Hook den normalisierten Befehl via
   updatedInput zurück (s. _build_allow_output).
3. WRONG_APPROACH_PATTERNS → deny (kein impliziter Override – # --allow-once nötig)
4. Compound-Segmente → jedes Segment via check_simple_command
5. check_simple_command: ALLOW_PATTERNS → DESTRUCTIVE_PATTERNS → deny

check_simple_command prüft kein WRONG_APPROACH – das ist Aufgabe von check_command
auf dem Gesamtbefehl, bevor gesplittet wird.

One-time-Ausnahme:
  '# --allow-once' an den Befehl anhängen → erzwingt User-Prompt statt deny.
  Dabei immer begründen warum der normale Weg nicht ausreicht.
  Beispiel: rm -rf Client/dist/ # --allow-once

Wenn ein Befehl regelmäßig benötigt wird: beim User anfragen ob er auf die Allow-Liste soll.

Output-Redirects (>, >>):
  Erlaubt: .claude/tmp/  – temporäres Verzeichnis für Analyse-Ausgaben
  Erlaubt: /dev/null, /dev/stderr, /dev/stdout
  Sonst:   deny
  Hinweis: 2>&1 und >&N (keine Datei) sind immer erlaubt.

Rückgabe von check_command / check_simple_command: tuple[str, str, str]
  (decision, reason, log_type)
  decision:  'allow' | 'deny' | 'ask'
  reason:    Hinweistext für den Agenten (leer wenn kein Hint vorhanden)
  log_type:  ALLOW | WRONG_APPROACH | DESTRUCTIVE | UNSAFE_REDIRECT | UNKNOWN |
             COMPOUND_DESTRUCTIVE | COMPOUND_UNSAFE_REDIRECT | COMPOUND_UNKNOWN |
             ONE_TIME
"""
import datetime
import json
import os
import re
import sys


# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------
SAFE_REDIRECT_PREFIXES: list[str] = [
    '/dev/null',
    '/dev/stderr',
    '/dev/stdout',
    '.claude/tmp/',
    '../.claude/tmp/',   # relativ aus Unterverzeichnissen (Client/, Server/, ...)
]

ONE_TIME_MARKER = '# --allow-once'

_REPO_ROOT = os.environ.get(
    "CLAUDE_PROJECT_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'),
)
_LOG_FILE = os.path.join(_REPO_ROOT, '.claude', 'tmp', 'denied-commands.log')
# Separates Log für erlaubte Befehle (OBS-S085-3 D): dient dem Aufspüren von
# Misuse-Patterns (z.B. Wrapper-Scripts mit nachgelagertem tail/grep), ohne das
# Deny-Log zu verrauschen. Beim Retro auswertbar (grep), kein Gate.
_ALLOWED_LOG_FILE = os.path.join(_REPO_ROOT, '.claude', 'tmp', 'allowed-commands.log')


# ---------------------------------------------------------------------------
# Repo-Pfad-Normalisierung (OBS-S085-1)
# Absolute Repo-Pfade verschwenden Token: der Agent läuft mit ihnen oft in
# Permission-Denies (z.B. python3 mit absolutem Pfad → WRONG_APPROACH), obwohl der
# relative Pfad erlaubt wäre. Wir normalisieren den Repo-Root-Präfix daher auf einen
# relativen Pfad (Arbeitsverzeichnis = Repo-Root) und geben den umgeschriebenen
# Befehl via updatedInput zurück. Breit angewandt (alle Vorkommen), da die
# Einheitlichkeit der Regel der Hauptnutzen ist.
# ---------------------------------------------------------------------------
_NORMALIZE_ROOT = os.path.normpath(_REPO_ROOT)

# Bare Repo-Root (optional mit einem Trailing-Slash) als eigenständige
# Verzeichnis-Referenz – gefolgt von Whitespace, Ende oder einem Shell-Operator.
_BARE_ROOT_RE = re.compile(re.escape(_NORMALIZE_ROOT) + r'/?(?=\s|$|[&|;])')

_NORMALIZE_HINT = (
    "Der absolute Repo-Pfad wurde automatisch auf einen relativen Pfad normalisiert "
    "(Arbeitsverzeichnis ist der Repo-Root). Künftig direkt relative Pfade verwenden – "
    "das vermeidet unnötige Permission-Denies."
)


def _strip_repo_root(text: str) -> str:
    """Ersetzt den Repo-Root in einem Textstück durch relative Pfade.

    Bare-Root (ohne Folge-Pfad) → '.', Präfix mit Pfad-Fortsetzung → relativ.
    Bare-Root zuerst, damit der Präfix-Replace die '/'-Fortsetzungen nicht stiehlt.
    """
    text = _BARE_ROOT_RE.sub('.', text)
    text = text.replace(_NORMALIZE_ROOT + '/', '')
    return text


def normalize_repo_paths(command: str) -> tuple[str, bool]:
    """Normalisiert absolute Repo-Root-Pfade auf relative.

    Gibt (neuer_befehl, geändert) zurück.
    """
    result = _strip_repo_root(command)
    return result, result != command


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def _log_command(command: str, log_type: str, log_file: str = _LOG_FILE) -> None:
    """Protokolliert einen Befehl in einem Log (Default: denied-commands.log).

    log_type: ALLOW | WRONG_APPROACH | DESTRUCTIVE | UNSAFE_REDIRECT | UNKNOWN |
              COMPOUND_DESTRUCTIVE | COMPOUND_UNSAFE_REDIRECT | COMPOUND_UNKNOWN |
              ONE_TIME
    log_file: Zielpfad – erlaubte Befehle gehen nach _ALLOWED_LOG_FILE (OBS-S085-3 D),
              alles andere nach _LOG_FILE.
    Fehler beim Schreiben dürfen den Hook nicht unterbrechen.
    """
    try:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{ts}] [{log_type}] {command}\n")
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Wrong-Approach-Patterns
# Falsche Werkzeuge oder Muster – es gibt immer eine bessere Alternative.
# Werden auf dem GESAMTBEFEHL geprüft (vor dem Compound-Split).
# Kein ^-Anker: Pattern soll auch in Compound-Kommandos und Subshells matchen.
# ---------------------------------------------------------------------------
WRONG_APPROACH_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # dotnet test: immer via Script aufrufen
    (
        re.compile(r'\bdotnet\s+test\b'),
        'dotnet test immer via Script aufrufen:\n'
        '  python3 .claude/scripts/dotnet-test.py [--filter TestName] [--verbose]\n'
        '--verbose zeigt den vollständigen Output.',
    ),
    # Stryker: immer via Wrapper-Script aufrufen
    (
        re.compile(r'\bdotnet\s+stryker\b'),
        'Stryker immer via Script aufrufen (führt stryker + Auswertung in einem Schritt aus):\n'
        '  python3 .claude/scripts/dotnet-stryker.py [--mutate Domain/Foo.cs] [--verbose]\n'
        '--verbose: zeigt alle nicht-getöteten Mutanten mit Status, StatusReason, Zeile und Spalte.',
    ),
    # Frontend E2E-Tests: immer via playwright-test.py (vor dem test-Pattern prüfen)
    (
        re.compile(r'\bnpm\s+run\s+test:e2e\b'),
        'E2E-Tests immer via Script aufrufen:\n'
        '  python3 .claude/scripts/playwright-test.py [--filter Pattern] [--verbose]',
    ),
    # Frontend Unit-Tests: immer via vitest-run.py (test:coverage und test:e2e sind ausgenommen)
    (
        re.compile(r'\bnpm\s+run\s+test(?![\w:])'),
        'Frontend-Tests immer via Script aufrufen:\n'
        '  python3 .claude/scripts/vitest-run.py [--filter Pattern] [--verbose]',
    ),
    # npx vitest: immer via vitest-run.py
    (
        re.compile(r'\bnpx\s+vitest\b'),
        'Vitest immer via Script aufrufen:\n'
        '  python3 .claude/scripts/vitest-run.py [--filter Pattern] [--verbose]',
    ),
    # npx playwright: immer via playwright-test.py
    (
        re.compile(r'\bnpx\s+playwright\b'),
        'Playwright immer via Script aufrufen:\n'
        '  python3 .claude/scripts/playwright-test.py [--filter Pattern] [--verbose]',
    ),
    # npx stryker: immer via stryker-frontend.py
    (
        re.compile(r'\bnpx\s+stryker\b'),
        'Stryker (Frontend) immer via Script aufrufen:\n'
        '  python3 .claude/scripts/stryker-frontend.py [--mutate src/pages/Foo.tsx] [--verbose]',
    ),
    # npx eslint / npm run lint: immer via eslint-run.py
    (
        re.compile(r'\bnpx\s+eslint\b|\bnpm\s+run\s+lint\b'),
        'ESLint immer via Script aufrufen:\n'
        '  python3 .claude/scripts/eslint-run.py [--verbose]',
    ),
    # npx jscpd / npm run lint:duplicates: immer via jscpd-run.py
    (
        re.compile(r'\bnpx\s+jscpd\b|\bnpm\s+run\s+lint:duplicates\b'),
        'jscpd immer via Script aufrufen:\n'
        '  python3 .claude/scripts/jscpd-run.py [--verbose]',
    ),
    # python3 mit absolutem Pfad
    (
        re.compile(r'\bpython3\s+[/~]'),
        'python3 mit absolutem Pfad ist nicht erlaubt.\n'
        'Projekt-Scripts immer mit relativem Pfad aufrufen:\n'
        '  python3 .claude/scripts/dotnet-test.py\n'
        '  python3 .claude/scripts/dotnet-stryker.py\n'
        '  python3 .claude/hooks/...',
    ),
    # git add -f: ignorierte Dateien könnten Secrets enthalten – User muss manuell handeln
    (
        re.compile(r'\bgit\s+add\b.*\s(?:-f\b|--force\b)'),
        "git add -f/--force ist nicht erlaubt. "
        "Wenn das Hinzufügen einer ignorierten Datei wirklich nötig ist, "
        "erkläre dem User warum und nenne den exakten Befehl zur manuellen Ausführung:\n"
        "  git add -f <datei>",
    ),
]


# ---------------------------------------------------------------------------
# Destructive-Patterns (destruktiv aber legitim – per '# --allow-once' freigabefähig)
# Struktur: (pattern, hint_text, short_label)
#   hint_text:   Deny-Nachricht für den Agenten (mehrzeilig, mit Beispiel)
#   short_label: Kurze Bezeichnung für --list (leer → kein Eintrag)
# ---------------------------------------------------------------------------
DESTRUCTIVE_PATTERNS: list[tuple[re.Pattern[str], str, str]] = [
    (
        re.compile(r'\bfind\b.*\s-delete\b'),
        "Destruktiver Befehl.",
        'find ... -delete',
    ),
    (
        re.compile(r'\bfind\b.*\s-exec(?:dir)?\s+(?:rm|bash|sh|dash|ksh)\b'),
        "Destruktiver Befehl.",
        'find ... -exec rm|bash|sh|dash|ksh',
    ),
    (
        re.compile(r'\brm\s+-[a-zA-Z]*[rR]'),
        "Destruktiver Befehl.\n"
        "  Beispiel: rm -rf Client/dist/ # --allow-once",
        'rm -r/-rf',
    ),
    (
        re.compile(r'\bgit\s+push\s+--force\b'),
        "Destruktiver Befehl.",
        'git push --force',
    ),
    (
        re.compile(r'\bgit\s+reset\s+--hard\b'),
        "Destruktiver Befehl.",
        'git reset --hard',
    ),
    (
        re.compile(r'\bgit\s+clean\s+-[a-zA-Z]*f'),
        "Destruktiver Befehl.",
        'git clean -f',
    ),
    (
        re.compile(r'\bgit\s+checkout\s+\.'),
        "Destruktiver Befehl.",
        'git checkout .',
    ),
    (
        re.compile(r'\bgit\s+restore\s+\.'),
        "Destruktiver Befehl.",
        'git restore .',
    ),
    (
        re.compile(r'\b(?:pkill|killall)\b'),
        "Prozess-Kill nach Name ist ein destruktiver Eingriff (trifft potenziell mehrere Prozesse).\n"
        "  Gezielt per PID ist erlaubt: kill <pid>\n"
        "  Beispiel: pkill -f dotnet # --allow-once",
        'pkill|killall <name>',
    ),
]


# ---------------------------------------------------------------------------
# Allow-Patterns
# Struktur: (pattern, group, description)
#   group:       Gruppenname (str) → _print_allow_list aggregiert Einträge derselben Gruppe
#                None → Standalone-Eintrag
#   description: Konkreter Beispiel-Befehl für --list
#                Leer ('') → kein Eintrag in --list (nur Pattern-Matching-Variante)
# ---------------------------------------------------------------------------
ALLOW_PATTERNS: list[tuple[re.Pattern[str], str | None, str]] = [
    # dotnet build (nativ)
    (
        re.compile(r'^dotnet\s+build\b'),
        None,
        'dotnet build',
    ),
    # dotnet run (nativ; Dev-Server). Kein DLL-Lock-Zwang mehr unter Linux → relativer --project ok.
    (
        re.compile(r'^dotnet\s+run\b'),
        None,
        'dotnet run [--project Server]',
    ),
    # kill eines einzelnen Prozesses per PID (gezielt). pkill/killall by-name → DESTRUCTIVE.
    (
        re.compile(r'^kill\s+(?:-\w+\s+)?\d+$'),
        None,
        'kill [-SIG] <PID>',
    ),
    # dotnet ef (sichere Subcommands; database drop bleibt deny)
    (
        re.compile(r'^dotnet\s+ef\s+(?:migrations\s+(?:add|remove|list)|database\s+update)\b'),
        None,
        'dotnet ef migrations add|remove|list  (auch: database update)',
    ),
    # dotnet tool restore/list (lokales Tool-Manifest .config/dotnet-tools.json)
    (
        re.compile(r'^dotnet\s+tool\s+(?:restore|list)\b'),
        None,
        'dotnet tool restore|list',
    ),
    # docker compose up|down (v2-Plugin, nativ in WSL). docker-compose (v1) → Smart-Deny-Hint.
    (
        re.compile(r'^docker\s+compose\s+(up|down)\b'),
        None,
        'docker compose up|down',
    ),
    # npm run/audit/outdated/update/ci (nativ). npm run test|lint → WRONG_APPROACH; npm install [pkg] → deny.
    (
        re.compile(r'^npm\s+(?:run\s|audit\b|outdated\b|update\b|ci\b)'),
        None,
        'npm run <script> | audit | outdated | update | ci',
    ),
    # python3 -m pytest auf .claude/ (Hook-Tests)
    (
        re.compile(r'^python3\s+-m\s+pytest\s+\.claude/'),
        None,
        'python3 -m pytest .claude/<test_script>.py',
    ),
    # Lesen: Datei- und Verzeichnisinhalte lesen/inspizieren
    (re.compile(r'^ls\b'), 'Lesen', 'ls'),
    (re.compile(r'^cat\b'), 'Lesen', 'cat'),
    (re.compile(r'^tail\b'), 'Lesen', 'tail'),
    (re.compile(r'^head\b'), 'Lesen', 'head'),
    (re.compile(r'^wc\b'), 'Lesen', 'wc'),
    (re.compile(r'^grep\b'), 'Lesen', 'grep'),
    # find: -delete und -exec (alle Varianten) → DESTRUCTIVE_PATTERNS
    (re.compile(r'^find\b(?!.*\s(?:-delete|-exec))'), 'Lesen', 'find (ohne -delete/-exec)'),
    (re.compile(r'^stat\b'), 'Lesen', 'stat'),
    (re.compile(r'^file\b'), 'Lesen', 'file'),
    (re.compile(r'^diff\b'), 'Lesen', 'diff'),
    # Shell: allgemeine Hilfsbefehle, Textverarbeitung, Pfad-Tools
    (re.compile(r'^echo\b'), 'Shell', 'echo'),
    # cd: reine Navigation. Gefährliche Kombis (cd + dotnet run / npx) sind unabhängig
    # via WRONG_APPROACH (Gesamtbefehl, vor Split) gedeckt; jedes Folge-Segment wird
    # ohnehin einzeln geprüft.
    (re.compile(r'^cd\b'), 'Shell', 'cd'),
    # sed read-only (kein -i / --in-place): druckt nur nach stdout, verändert keine Datei.
    # In-Place-Edits bleiben deny → Edit-Tool (Ausnahme: \r-Bereinigung, eigenes Pattern oben).
    (re.compile(r'^sed\b(?!.*\s(?:-i|--in-place))'), 'Shell', "sed (read-only, ohne -i)"),
    # xargs nur mit read-only Child-Command (xargs führt sein Argument als Befehl aus –
    # darum eng auf Lese-Werkzeuge begrenzt; xargs rm/mv/bash etc. bleibt deny).
    (
        re.compile(r'^xargs\s+(?:-\S+\s+(?:\{\}\s+)?)*(?:grep|cat|wc|head|tail|file|stat|sort|uniq|cut|ls)\b'),
        'Shell',
        'xargs grep|cat|wc|head|tail|file|stat|sort|uniq|cut|ls',
    ),
    (re.compile(r'^pwd$'), 'Shell', 'pwd'),
    (re.compile(r'^date$'), 'Shell', 'date'),
    (re.compile(r'^which\b'), 'Shell', 'which'),
    (re.compile(r'^sort\b'), 'Shell', 'sort'),
    (re.compile(r'^uniq\b'), 'Shell', 'uniq'),
    (re.compile(r'^tr\b'), 'Shell', 'tr'),
    (re.compile(r'^cut\b'), 'Shell', 'cut'),
    (re.compile(r'^dirname\b'), 'Shell', 'dirname'),
    (re.compile(r'^basename\b'), 'Shell', 'basename'),
    (re.compile(r'^realpath\b'), 'Shell', 'realpath'),
    (re.compile(r'^jq\b'), 'Shell', 'jq'),
    # Datei-/Verzeichnis-Verwaltung
    (re.compile(r'^mkdir\b'), 'Dateiverwaltung', 'mkdir'),
    (re.compile(r'^touch\b'), 'Dateiverwaltung', 'touch'),
    (re.compile(r'^chmod\s+\+x\b'), 'Dateiverwaltung', 'chmod +x'),  # nur +x, nicht 755/-R/andere
    (re.compile(r'^rm\b(?!\s+-[a-zA-Z]*[rR])'), 'Dateiverwaltung', 'rm (ohne -r/-R)'),  # rm -r/-rf → DESTRUCTIVE_PATTERNS
    (re.compile(r'^mv\b'), 'Dateiverwaltung', 'mv'),                   # mv ist nicht-rekursiv (kein -r)
    (re.compile(r'^cp\b(?!\s+-[a-zA-Z]*[rR])'), 'Dateiverwaltung', 'cp (ohne -r/-R)'),  # rekursiv → deny
    # Python: nur .claude/-Verzeichnis (Projekt-Werkzeuge und Hooks)
    (
        re.compile(r'^python3\s+(?!-)\.claude/'),
        None,
        'python3 .claude/scripts/<script>.py  /  python3 .claude/hooks/<hook>.py',
    ),
    # git read-only (optional mit -C <pfad>, um in anderem Repo/Worktree zu lesen)
    (
        re.compile(r'^git\s+(?:-C\s+\S+\s+)?(status|log|diff|branch|show|remote|tag|rev-parse|ls-files|shortlog)\b'),
        None,
        'git [-C <pfad>] status|log|diff|branch|show|remote|tag|rev-parse|ls-files|shortlog',
    ),
    # git safe write (explizit kein -f/--force – das ist in WRONG_APPROACH_PATTERNS)
    (re.compile(r'^git\s+add\b(?!.*\s(?:-f\b|--force\b))'), None, 'git add <datei>  (ohne -f/--force)'),
    (re.compile(r'^git\s+stash\s+(list|push|save|pop|apply|drop)\b'), None, 'git stash list|push|save|pop|apply|drop'),
]


# ---------------------------------------------------------------------------
# Smart-Deny-Hints (für UNKNOWN-Fälle ohne passendes Pattern)
# ---------------------------------------------------------------------------
_SMART_DENY_HINTS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r'\bdocker-compose\b'),
        "docker-compose (v1) ist in dieser WSL-Distro nicht verfügbar.\n"
        "  Nutze die v2-Form mit Leerzeichen: docker compose up|down.",
    ),
    (
        re.compile(r'\bsed\b'),
        "Für Datei-Edits: Edit-Tool verwenden.\n"
        "Für Lesen von Zeilenbereichen: Read-Tool mit offset/limit-Parametern verwenden.",
    ),
    (
        re.compile(r'\bgit\s+push\b'),
        "git push: Befehl dem User mitteilen – Pushes sind User-Aktionen.",
    ),
    (
        re.compile(r'\bgit\s+commit\b'),
        "git commit: Befehl dem User mitteilen – Commits sind User-Aktionen.",
    ),
    (
        re.compile(r'\bnpm\s+(?:install|i|add)\b'),
        "npm install <pkg> fügt eine Dependency hinzu → erst den docs/reference/dependencies.md-Prozess.\n"
        "Für reinen Lock-Install (nach Clone): npm ci (erlaubt, reproduzierbar aus package-lock.json).",
    ),
    (
        re.compile(r'\bnpm\b'),
        "npm-Subcommand nicht auf der Allow-Liste.\n"
        "  Erlaubt: npm run <script>, npm audit, npm outdated, npm update, npm ci\n"
        "  Tests/Lint/Mutation NICHT direkt – via Wrapper-Scripts (vitest-run.py, eslint-run.py, …).",
    ),
    (
        re.compile(r'^python3\s+-c\b'),
        "python3 -c führt beliebigen Code aus (nicht erlaubt).\n"
        "Für Ad-hoc-Analyse: Script nach .claude/tmp/foo.py schreiben (Write-Tool), dann\n"
        "  python3 .claude/tmp/foo.py   (anschließend löschen).\n"
        "Für Datei-Inspektion: Read/Grep/Glob-Tools statt Python.",
    ),
    (
        re.compile(r'^(?:for|while)\b'),
        "Shell-Schleifen sind nicht erlaubt.\n"
        "Über mehrere Dateien iterieren: Glob/Grep-Tools nutzen, oder ein\n"
        "Analyse-Script nach .claude/tmp/ schreiben und mit python3 .claude/tmp/<name>.py ausführen.",
    ),
]


def _get_smart_hint(command: str) -> str:
    """Gibt einen kontextspezifischen Hinweis für UNKNOWN-Fälle zurück."""
    for pattern, hint in _SMART_DENY_HINTS:
        if pattern.search(command):
            return hint
    return ""


# ---------------------------------------------------------------------------
# Deny-Message-Texte
# ---------------------------------------------------------------------------
_ALLOW_ONCE_WITH_HINT_FOOTER = (
    "\n\n"
    "Einmalige Ausnahme: '# --allow-once' anhängen → User wird gefragt.\n"
    "⚠️  Nur für echte Einzelfälle ohne reguläre Alternative – nie für Befehle die auf der Allow-Liste stehen.\n"
    "   Dabei begründen warum der Hint oben nicht befolgt werden kann.\n"
    "   Alle erlaubten Patterns: python3 .claude/hooks/check-bash-permission.py --list\n"
    "Nicht kreativ umgehen – jedes Deny hat einen Grund."
)

_NO_HINT_MESSAGE = (
    "Befehl nicht auf der Allow-Liste. Erlaubte Befehle + Alternativen ansehen:\n"
    "  python3 .claude/hooks/check-bash-permission.py --list\n"
    "\n"
    "Für Ad-hoc-Logik: Script nach .claude/tmp/foo.py schreiben, dann python3 .claude/tmp/foo.py.\n"
    "\n"
    "Falls --list nichts Passendes zeigt – dem User erklären:\n"
    "  (1) Was der Befehl tun soll\n"
    "  (2) Warum keine erlaubte Alternative ausreicht\n"
    "  (3) Ob regelmäßig benötigt → ggf. auf die Allow-Liste / als Wrapper-Script\n"
    "\n"
    "Einmalige Ausnahme: '# --allow-once' anhängen → User wird gefragt.\n"
    "⚠️  Nur für echte Einzelfälle ohne reguläre Alternative.\n"
    "Nicht kreativ umgehen – jedes Deny hat einen Grund."
)

_ALLOW_REASON = "Auto-approved by bash permission hook"

_UNSAFE_REDIRECT_DENY_REASON = (
    "Output-Redirect auf nicht erlaubtes Ziel.\n"
    "Bevorzugte Alternative: Output in Variable capturen (kein Datei-Müll):\n"
    "  output=$(dotnet build)\n"
    "  echo \"$output\" | grep ...\n"
    "Falls Datei-Redirect nötig (sehr großer Output): nur .claude/tmp/ erlaubt; Datei danach löschen.\n"
    "Sonstige erlaubte Redirect-Ziele: /dev/null, /dev/stderr, /dev/stdout.\n"
    "Für dotnet test/stryker: Projekt-Scripts verwenden statt Redirect:\n"
    "  python3 .claude/scripts/dotnet-test.py / dotnet-stryker.py"
)


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def has_unsafe_output_redirect(command: str) -> bool:
    """Gibt True zurück wenn der Befehl einen unquotierten Output-Redirect (>, >>)
    auf ein nicht-erlaubtes Ziel enthält.

    Erlaubt: SAFE_REDIRECT_PREFIXES (z.B. .claude/tmp/, /dev/null)
    Erlaubt: >&N / N>&M (redirect zu File-Descriptor, keine Datei)
    """
    in_single_quote = False
    in_double_quote = False
    i = 0

    while i < len(command):
        c = command[i]

        if c == '\\' and not in_single_quote:
            i += 2
            continue

        if c == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
        elif c == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
        elif not in_single_quote and not in_double_quote:
            if c == '>':
                offset = 2 if (i + 1 < len(command) and command[i + 1] == '>') else 1
                rest = command[i + offset:]

                if rest.startswith('&'):
                    # File-Descriptor-Redirect (2>&1, >&2 etc.) – immer erlaubt.
                    i += 1
                    continue

                target_match = re.match(r'\s*(\S+)', rest)
                if not target_match:
                    return True  # kein Redirect-Ziel → unsafe
                target = target_match.group(1).replace('\\', '/')
                if any(target.startswith(p) for p in SAFE_REDIRECT_PREFIXES):
                    i += 1
                    continue
                return True  # Ziel nicht in SAFE_REDIRECT_PREFIXES

        i += 1

    return False


def split_compound_command(command: str) -> list[str]:
    """Splittet einen Compound-Command an bash-level Operatoren (|, ||, &&, ;).
    Respektiert Anführungszeichen. Gibt immer mindestens [command] zurück.

    Hinweis: Backtick-Command-Substitution (`...`) und $(...) werden nicht als
    Quote-Kontext behandelt. Praktisch unkritisch, weil WRONG_APPROACH- und
    DESTRUCTIVE_PATTERNS via .search() auch innerhalb von Subshells matchen.
    """
    segments: list[str] = []
    current: list[str] = []
    in_single_quote = False
    in_double_quote = False
    i = 0

    def flush() -> None:
        seg = ''.join(current).strip()
        if seg:
            segments.append(seg)
        current.clear()

    while i < len(command):
        c = command[i]

        if c == '\\' and not in_single_quote:
            current.append(c)
            if i + 1 < len(command):
                current.append(command[i + 1])
            i += 2
            continue

        if c == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            current.append(c)
            i += 1
            continue

        if c == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            current.append(c)
            i += 1
            continue

        if in_single_quote or in_double_quote:
            current.append(c)
            i += 1
            continue

        # Ab hier: definitiv außerhalb von Quotes
        if c == '|':
            flush()
            i += 2 if (i + 1 < len(command) and command[i + 1] == '|') else 1
            continue

        if c == '&' and i + 1 < len(command) and command[i + 1] == '&':
            flush()
            i += 2
            continue

        if c == ';':
            flush()
            i += 1
            continue

        current.append(c)
        i += 1

    flush()
    return segments if segments else [command]


# ---------------------------------------------------------------------------
# Kern-Logik
# ---------------------------------------------------------------------------

def check_simple_command(command: str) -> tuple[str, str, str]:
    """Prüft ein einzelnes Segment: ALLOW → DESTRUCTIVE → deny.

    WRONG_APPROACH wird nicht geprüft – das übernimmt check_command auf dem
    Gesamtbefehl vor dem Split.

    Gibt (decision, reason, log_type) zurück. decision: 'allow' | 'deny'.
    """
    for pattern, _, _ in ALLOW_PATTERNS:
        if pattern.search(command):
            if has_unsafe_output_redirect(command):
                return ("deny", _UNSAFE_REDIRECT_DENY_REASON, "UNSAFE_REDIRECT")
            return ("allow", _ALLOW_REASON, "ALLOW")

    for pattern, reason, _ in DESTRUCTIVE_PATTERNS:
        if pattern.search(command):
            return ("deny", reason, "DESTRUCTIVE")

    hint = _get_smart_hint(command)
    return ("deny", hint, "UNKNOWN")


def check_command(command: str) -> tuple[str, str, str]:
    """Prüft einen Befehl und gibt (decision, reason, log_type) zurück.

    Reihenfolge:
      1. ONE_TIME_MARKER → ask (übersteuert alles)
      2. Repo-Pfad-Normalisierung (absolute Repo-Pfade → relativ)
      3. WRONG_APPROACH  → deny (auf Gesamtbefehl, vor Split)
      4. Compound-Split  → check_simple_command je Segment
      5. check_simple_command für einfache Befehle

    decision: 'allow' | 'deny' | 'ask'
    """
    # 1. ONE_TIME_MARKER übersteuert alles inkl. WRONG_APPROACH (vor Normalisierung)
    if ONE_TIME_MARKER in command:
        return ("ask", "", "ONE_TIME")

    # 2. Repo-Pfad-Normalisierung: absolute Repo-Pfade → relativ, dann auf dem
    #    normalisierten Befehl weiterprüfen (so wird z.B. python3 <absoluter Pfad>
    #    zu python3 .claude/... und matcht die Allow-Liste statt WRONG_APPROACH).
    command, _ = normalize_repo_paths(command)

    # 3. WRONG_APPROACH auf Gesamtbefehl (ohne ^-Anker → matcht auch in Subshells)
    for pattern, reason in WRONG_APPROACH_PATTERNS:
        if pattern.search(command):
            return ("deny", reason, "WRONG_APPROACH")

    # 4. Compound-Split + Segment-Check (check_simple_command ohne WRONG_APPROACH)
    segments = split_compound_command(command)
    is_compound = len(segments) > 1
    for segment in segments:
        decision, reason, log_type = check_simple_command(segment)
        if decision == "deny":
            if is_compound:
                log_type = f"COMPOUND_{log_type}"
            return ("deny", reason, log_type)

    return ("allow", _ALLOW_REASON, "ALLOW")


def _build_deny_message(reason: str) -> str:
    """Baut die vollständige Deny-Nachricht für den Agenten."""
    if reason:
        return reason + _ALLOW_ONCE_WITH_HINT_FOOTER
    return _NO_HINT_MESSAGE


# Projekt-Tasks, die NIE direkt laufen (Tests/Lint/Mutation) → immer via Wrapper-Script.
# Die direkten Befehle (dotnet test, npm run test, npx …) sind WRONG_APPROACH → deny.
# Hier nur für --list, damit der korrekte Weg PROAKTIV sichtbar ist (sonst lernt der Agent
# ihn erst nach einem unnötigen Deny). Bei Script-Umbenennung hier + WRONG_APPROACH_PATTERNS syncen.
_PROJECT_TASK_SCRIPTS: list[str] = [
    "Backend-Tests:       python3 .claude/scripts/dotnet-test.py [--filter X] [--verbose]",
    "Backend-Mutation:    python3 .claude/scripts/dotnet-stryker.py [--mutate Domain/Foo.cs] [--verbose]",
    "Frontend-Unit-Tests: python3 .claude/scripts/vitest-run.py [--filter X] [--verbose]",
    "Frontend-E2E:        python3 .claude/scripts/playwright-test.py [--filter X] [--verbose]",
    "Frontend-Mutation:   python3 .claude/scripts/stryker-frontend.py [--mutate src/..] [--verbose]",
    "ESLint:              python3 .claude/scripts/eslint-run.py [--verbose]",
    "Duplikate (jscpd):   python3 .claude/scripts/jscpd-run.py [--verbose]",
]

# Nutzungshinweis zu den Wrapper-Scripts (OBS-S085-3 C). Erscheint via --list auch in
# der SessionStart-Injection (session-start.sh ruft --list auf) → eine Quelle.
_SCRIPT_USAGE_HINT: str = (
    "Diese Wrapper geben bereits NUR das Relevante aus – normal OHNE nachgelagertes\n"
    "| tail / | grep / | head aufrufen (der Output ist dafür kuratiert). Mehr Tiefe bei\n"
    "Bedarf: --verbose (einheitlich bei allen Wrappern). Details/Beispiele: --help.\n"
    "Ist der Output trotzdem zu viel oder zu wenig → als Beobachtung in\n"
    "docs/kaizen/observations.md sammeln, statt ad-hoc zu filtern (so verbessern wir die\n"
    "Scripts, statt das Symptom zu kaschieren)."
)


def _print_allow_list() -> None:
    """Gibt eine lesbare Übersicht der erlaubten Befehle aus (--list-Flag)."""
    print(
        "Diese Liste regelt das Bash-Tool. Befehle die hier nicht passen, werden vom\n"
        "PreToolUse-Hook automatisch geblockt (deny) – nicht nur \"unerwünscht\", sondern\n"
        "hart blockiert. '# --allow-once' anhängen erzwingt eine einmalige User-Freigabe\n"
        "(nur für echte Einzelfälle ohne regulären Weg).\n"
        "Tool-Vorrang: für Datei-Lesen/-Ändern/-Suchen sind Read/Edit/Grep/Glob meist\n"
        "besser als cat/sed/grep – Bash nur wenn kein Tool passt.\n"
    )

    print("Häufige Projekt-Tasks – immer via Wrapper-Script (Direktaufruf wird geblockt):")
    for line in _PROJECT_TASK_SCRIPTS:
        print(f"  {line}")
    print()
    print(_SCRIPT_USAGE_HINT)
    print()

    print("Erlaubte Befehle (Allow-Liste):")

    # Erst alle Einträge sammeln, dann alphabetisch sortiert ausgeben
    groups: dict[str, list[str]] = {}
    standalone: list[str] = []

    for _pattern, group, desc in ALLOW_PATTERNS:
        if group is not None:
            groups.setdefault(group, [])
            if desc:
                groups[group].append(desc)
        elif desc:
            standalone.append(desc)

    for _, line in sorted((desc.lower(), f"  {desc}") for desc in standalone):
        print(line)

    if groups:
        print()
        for grp in sorted(groups, key=str.lower):
            items = sorted(groups[grp], key=str.lower)
            print(f"  [{grp}]")
            print(f"    {', '.join(items)}")

    print()
    print("Verknüpfung mit |, ||, &&, ; ist erlaubt – jedes Segment wird einzeln geprüft.")
    print()
    print("Destruktive Befehle (nur mit # --allow-once, User-Freigabe nötig):")
    for _pattern, _hint, label in sorted(
        ((p, h, lb) for p, h, lb in DESTRUCTIVE_PATTERNS if lb),
        key=lambda x: x[2].lower(),
    ):
        print(f"  {label}")


def _build_allow_output(command: str) -> dict:
    """Baut den allow-`hookSpecificOutput`.

    Enthält die Normalisierung einen geänderten Befehl (außer bei # --allow-once),
    werden `updatedInput` (umgeschriebener Befehl) und `additionalContext` (Hinweis)
    ergänzt, damit Claude Code den relativen Befehl ausführt und der Agent lernt,
    künftig relative Pfade zu nutzen.
    """
    hso: dict = {
        "hookEventName": "PreToolUse",
        "permissionDecision": "allow",
        "permissionDecisionReason": _ALLOW_REASON,
    }
    if ONE_TIME_MARKER not in command:
        normalized, changed = normalize_repo_paths(command)
        if changed:
            hso["updatedInput"] = {"command": normalized}
            hso["additionalContext"] = _NORMALIZE_HINT
    return hso


def main() -> None:
    if "--list" in sys.argv:
        _print_allow_list()
        sys.exit(0)

    try:
        inp = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = inp.get("tool_name", "")
    if tool_name != "Bash":
        sys.exit(0)

    command = inp.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)

    decision, reason, log_type = check_command(command)

    # allow: in separates allowed-commands.log (Misuse-Pattern-Analyse, OBS-S085-3 D) –
    # denied-commands.log bleibt ausschließlich für Denies/Asks.
    # _build_allow_output ergänzt bei normalisiertem Repo-Pfad updatedInput + Hinweis.
    if decision == "allow":
        _log_command(command, "ALLOW", _ALLOWED_LOG_FILE)
        print(json.dumps({"hookSpecificOutput": _build_allow_output(command)}))
        sys.exit(0)

    if decision == "ask":
        _log_command(command, "ONE_TIME")
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
            }
        }))
        sys.exit(0)

    # deny: loggen + blockieren mit Hinweis
    _log_command(command, log_type)
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": _build_deny_message(reason),
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
