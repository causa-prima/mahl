#!/usr/bin/env python3
"""PreToolUse-Hook: Bash-Kommandos prüfen (deny/allow/ask).

Reihenfolge in check_command:
1. ONE_TIME_MARKER → ask (übersteuert alle anderen Prüfungen inkl. WRONG_APPROACH)
2. WRONG_APPROACH_PATTERNS → deny (kein impliziter Override – # --allow-once nötig)
3. Compound-Segmente → jedes Segment via check_simple_command
4. check_simple_command: ALLOW_PATTERNS → DESTRUCTIVE_PATTERNS → deny

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

# Extrahiert das innere Kommando aus cmd.exe /c "..."
_CMDEXE_INNER_RE = re.compile(r'^cmd\.exe\s+/c\s+"(.*)"')


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def _log_command(command: str, log_type: str) -> None:
    """Protokolliert einen Befehl in denied-commands.log.

    log_type: ALLOW | WRONG_APPROACH | DESTRUCTIVE | UNSAFE_REDIRECT | UNKNOWN |
              COMPOUND_DESTRUCTIVE | COMPOUND_UNSAFE_REDIRECT | COMPOUND_UNKNOWN |
              ONE_TIME
    Fehler beim Schreiben dürfen den Hook nicht unterbrechen.
    """
    try:
        os.makedirs(os.path.dirname(_LOG_FILE), exist_ok=True)
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(_LOG_FILE, 'a', encoding='utf-8') as f:
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
    # Dateien lesen via cmd.exe type → Read-Tool verwenden
    (
        re.compile(r'(?:output=\$\()?cmd\.exe\s+/c\s+"type\b'),
        'Dateien nicht via cmd.exe type lesen – stattdessen das Read-Tool verwenden.\n'
        'Das Read-Tool ist schneller, erzeugt keine Prozesse und liefert den Inhalt direkt.',
    ),
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
        '  python3 .claude/scripts/dotnet-stryker.py [--mutate Domain/Foo.cs] [--detail]\n'
        '--detail: zeigt alle nicht-getöteten Mutanten mit Status, StatusReason, Zeile und Spalte.',
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
        '  python3 .claude/scripts/stryker-frontend.py [--mutate src/pages/Foo.tsx] [--detail]',
    ),
    # WSL: Pipe direkt nach cmd.exe funktioniert nicht
    (
        re.compile(r'\bcmd\.exe\b.*\|'),
        "Pipe nach cmd.exe funktioniert nicht in WSL.\n"
        "Richtige Alternativen – je nach Situation:\n"
        "\n"
        "A) Normalfall (Output passt in Context): Variable capturen, dann filtern:\n"
        "   output=$(cmd.exe /c \"cd /d C:\\\\...\\\\mahl && dotnet build\")\n"
        "   echo \"$output\" | grep -E '(error|warning CS|Build)'\n"
        "\n"
        "B) Sehr große Outputs: Redirect in Datei:\n"
        "   cmd.exe /c \"... > .claude/tmp/out.txt 2>&1\"\n"
        "   cat /mnt/c/Users/kieritz/source/repos/mahl/.claude/tmp/out.txt\n"
        "   (Datei danach löschen!)\n"
        "\n"
        "C) Kein Filter nötig: cmd.exe direkt aufrufen, vollständiger Output.\n"
        "\n"
        "Für dotnet test und dotnet stryker: Projekt-Scripts verwenden statt cmd.exe direkt:\n"
        "  python3 .claude/scripts/dotnet-test.py / dotnet-stryker.py",
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
# Struktur: (pattern, hint_text)
# ---------------------------------------------------------------------------
DESTRUCTIVE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r'\bfind\b.*\s-delete\b'),
        "Destruktiver Befehl.",
    ),
    (
        re.compile(r'\bfind\b.*\s-exec(?:dir)?\s+(?:rm|bash|sh|dash|ksh)\b'),
        "Destruktiver Befehl.",
    ),
    (
        re.compile(r'\brm\s+-[a-zA-Z]*[rR]'),
        "Destruktiver Befehl.\n"
        "  Beispiel: rm -rf Client/dist/ # --allow-once",
    ),
    (
        re.compile(r'\bgit\s+push\s+--force\b'),
        "Destruktiver Befehl.",
    ),
    (
        re.compile(r'\bgit\s+reset\s+--hard\b'),
        "Destruktiver Befehl.",
    ),
    (
        re.compile(r'\bgit\s+clean\s+-[a-zA-Z]*f'),
        "Destruktiver Befehl.",
    ),
    (
        re.compile(r'\bgit\s+checkout\s+\.'),
        "Destruktiver Befehl.",
    ),
    (
        re.compile(r'\bgit\s+restore\s+\.'),
        "Destruktiver Befehl.",
    ),
    (
        re.compile(r'\btaskkill\b'),
        "Prozess-Kill ist ein destruktiver Eingriff.\n"
        "  Beispiel: cmd.exe /c \"taskkill /f /im dotnet.exe\" # --allow-once",
    ),
]


# ---------------------------------------------------------------------------
# Allow-Patterns
# ---------------------------------------------------------------------------
ALLOW_PATTERNS: list[re.Pattern[str]] = [
    # dotnet build über cmd.exe (direkt oder via Variable capturen)
    re.compile(r'^cmd\.exe\s+/c\s+"cd\s+/d\s+[^"]*mahl[^"]*&&\s*dotnet\s+build\b'),
    re.compile(r'^output=\$\(cmd\.exe\s+/c\s+"cd\s+/d\s+[^"]*mahl[^"]*&&\s*dotnet\s+build\b'),
    # dotnet run via cmd.exe (mit optionaler Env-Var-Präfix)
    re.compile(r'^cmd\.exe\s+/c\s+"cd\s+/d\s+[^"]*mahl[^"]*&&\s*(set\s+\S+\s+&&\s+)?dotnet\s+run\b'),
    # dotnet ef (sichere Subcommands; database drop bleibt deny)
    re.compile(r'^cmd\.exe\s+/c\s+"cd\s+/d\s+[^"]*mahl[^"]*&&\s*dotnet\s+ef\s+(migrations\s+(add|remove|list)|database\s+update)\b'),
    # docker-compose: WSL-direkt und via cmd.exe
    re.compile(r'^docker-compose\s+(up|down)\b'),
    re.compile(r'^docker\s+compose\s+(up|down)\b'),
    re.compile(r'^cmd\.exe\s+/c\s+"cd\s+/d\s+[^"]*mahl[^"]*&&\s*docker-compose\s+(up|down)\b'),
    # npm run / npm audit über cmd.exe (npm install bleibt deny – führt externen Code aus)
    re.compile(r'^cmd\.exe\s+/c\s+"cd\s+/d\s+[^"]*mahl\\Client[^"]*&&\s*npm\s+run\s'),
    re.compile(r'^cmd\.exe\s+/c\s+"cd\s+/d\s+[^"]*mahl\\Client[^"]*&&\s*npm\s+audit\b'),
    # python3 -m pytest auf .claude/ (Hook-Tests)
    re.compile(r'^python3\s+-m\s+pytest\s+\.claude/'),
    # Lese- und Analyse-Befehle
    re.compile(r'^ls\b'),
    re.compile(r'^cat\b'),
    re.compile(r'^tail\b'),
    re.compile(r'^head\b'),
    re.compile(r'^wc\b'),
    re.compile(r'^grep\b'),
    # find: -delete und -exec (alle Varianten) → DESTRUCTIVE_PATTERNS
    re.compile(r'^find\b(?!.*\s(?:-delete|-exec))'),
    re.compile(r'^echo\b'),
    re.compile(r'^pwd$'),
    re.compile(r'^date$'),
    re.compile(r'^which\b'),
    re.compile(r'^file\b'),
    re.compile(r'^stat\b'),
    re.compile(r'^diff\b'),
    re.compile(r'^sort\b'),
    re.compile(r'^uniq\b'),
    re.compile(r'^tr\b'),
    re.compile(r'^cut\b'),
    re.compile(r'^dirname\b'),
    re.compile(r'^basename\b'),
    re.compile(r'^realpath\b'),
    re.compile(r'^jq\b'),
    # Datei-/Verzeichnis-Verwaltung
    re.compile(r'^mkdir\b'),
    re.compile(r'^touch\b'),
    re.compile(r'^chmod\s+\+x\b'),  # nur +x, nicht 755/-R/andere
    re.compile(r'^rm\b(?!\s+-[a-zA-Z]*[rR])'),  # einzelne Dateien; rm -r/-rf → DESTRUCTIVE_PATTERNS
    re.compile(r'^mv\b'),                         # mv ist nicht-rekursiv (kein -r)
    re.compile(r'^cp\b(?!\s+-[a-zA-Z]*[rR])'),   # cp ohne -r/-R; rekursiv → deny
    # Python: nur .claude/-Verzeichnis (Projekt-Werkzeuge und Hooks)
    re.compile(r'^python3\s+(?!-)\.claude/'),
    # sed für \r-Bereinigung (\\r oder \\\\r, einfache oder doppelte Anführungszeichen)
    re.compile(r"^sed\s+-i\s+['\"]s/\\\\?r//['\"]"),
    # git read-only
    re.compile(r'^git\s+(status|log|diff|branch|show|stash\s+list|remote|tag|rev-parse|ls-files|shortlog)\b'),
    # git safe write (explizit kein -f/--force – das ist in WRONG_APPROACH_PATTERNS)
    re.compile(r'^git\s+add\b(?!.*\s(?:-f\b|--force\b))'),
    re.compile(r'^git\s+stash\s+(push|save|pop|apply|drop)\b'),
]


# ---------------------------------------------------------------------------
# Smart-Deny-Hints (für UNKNOWN-Fälle ohne passendes Pattern)
# ---------------------------------------------------------------------------
_SMART_DENY_HINTS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r'\bgit\s+push\b'),
        "git push: Befehl dem User mitteilen – Pushes sind User-Aktionen.",
    ),
    (
        re.compile(r'\bgit\s+commit\b'),
        "git commit: Befehl dem User mitteilen – Commits sind User-Aktionen.",
    ),
    (
        re.compile(r'\bnpm\s+install\b'),
        "npm install: DEPENDENCIES.md-Prozess durchführen, dann User bitten den Befehl auszuführen.",
    ),
    (
        re.compile(r'\bdotnet\s+run\b'),
        "dotnet run: cmd.exe /c \"cd /d C:\\\\...\\\\mahl && dotnet run --project Server\"\n"
        "  (.NET läuft nur auf Windows, nicht direkt in WSL)",
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
    "Dabei begründen warum der Hint nicht befolgt werden kann.\n"
    "Nicht kreativ umgehen – jedes Deny hat einen Grund."
)

_NO_HINT_MESSAGE = (
    "Kein Hint verfügbar. Zuerst CLAUDE.md Navigationstabelle prüfen\n"
    "ob eine definierte Alternative existiert.\n"
    "\n"
    "Falls keine Alternative bekannt – dem User erklären:\n"
    "  (1) Was der Befehl tun soll\n"
    "  (2) Warum keine bekannte Alternative ausreicht\n"
    "  (3) Ob regelmäßig benötigt → ggf. zur Allow-Liste hinzufügen\n"
    "  (4) Wenn regelmäßig + Output-Verarbeitung: Wrapper-Script sinnvoller?\n"
    "\n"
    "Einmalige Ausnahme: '# --allow-once' anhängen → User wird gefragt.\n"
    "Nicht kreativ umgehen – jedes Deny hat einen Grund."
)

_ALLOW_REASON = "Auto-approved by bash permission hook"

_UNSAFE_REDIRECT_DENY_REASON = (
    "Output-Redirect auf nicht erlaubtes Ziel.\n"
    "Bevorzugte Alternative: Output in Variable capturen (kein Datei-Müll):\n"
    "  output=$(cmd.exe /c \"...\")\n"
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

    Bei cmd.exe /c "..." wird der innere Befehl geprüft, da cmd.exe dessen
    Redirects direkt ausführt – auch wenn sie auf Shell-Ebene gequotet erscheinen.
    """
    m = _CMDEXE_INNER_RE.match(command)
    if m:
        return has_unsafe_output_redirect(m.group(1))

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
                    # Hinweis: cmd.exe kennt andere Redirect-Syntax (1>&2 statt 2>&1),
                    # aber wir prüfen hier bash-style. Ungültige cmd.exe-Syntax wird
                    # von cmd.exe selbst zur Laufzeit abgefangen.
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
    for pattern in ALLOW_PATTERNS:
        if pattern.search(command):
            if has_unsafe_output_redirect(command):
                return ("deny", _UNSAFE_REDIRECT_DENY_REASON, "UNSAFE_REDIRECT")
            return ("allow", _ALLOW_REASON, "ALLOW")

    for pattern, reason in DESTRUCTIVE_PATTERNS:
        if pattern.search(command):
            return ("deny", reason, "DESTRUCTIVE")

    hint = _get_smart_hint(command)
    return ("deny", hint, "UNKNOWN")


def check_command(command: str) -> tuple[str, str, str]:
    """Prüft einen Befehl und gibt (decision, reason, log_type) zurück.

    Reihenfolge:
      1. ONE_TIME_MARKER → ask (übersteuert alles)
      2. WRONG_APPROACH  → deny (auf Gesamtbefehl, vor Split)
      3. Compound-Split  → check_simple_command je Segment
      4. check_simple_command für einfache Befehle

    decision: 'allow' | 'deny' | 'ask'
    """
    # 1. ONE_TIME_MARKER übersteuert alles inkl. WRONG_APPROACH
    if ONE_TIME_MARKER in command:
        return ("ask", "", "ONE_TIME")

    # 2. WRONG_APPROACH auf Gesamtbefehl (ohne ^-Anker → matcht auch in Subshells)
    for pattern, reason in WRONG_APPROACH_PATTERNS:
        if pattern.search(command):
            return ("deny", reason, "WRONG_APPROACH")

    # 3. Compound-Split + Segment-Check (check_simple_command ohne WRONG_APPROACH)
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


def main() -> None:
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

    # allow: kein Log – denied-commands.log ist ausschließlich für Denies/Asks
    if decision == "allow":
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": reason,
            }
        }))
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
