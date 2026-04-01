#!/usr/bin/env python3
"""PreToolUse-Hook: Bash-Kommandos prüfen (deny/allow/ask).

Reihenfolge:
1. DENY_PATTERNS  → bekannte Fehlmuster und destruktive Befehle blockieren
2. ALLOW_PATTERNS → sichere, häufige Befehle automatisch erlauben
3. ask            → erzwungener Permission-Prompt für alles andere

Output-Redirects (>, >>):
  Erlaubt: .claude/tmp/  – temporäres Verzeichnis für Analyse-Ausgaben
  Erlaubt: /dev/null, /dev/stderr, /dev/stdout
  Sonst:   ask (User entscheidet)
  Hinweis: 2>&1 und >&N (keine Datei) sind immer erlaubt.
"""
import json
import re
import sys


# ---------------------------------------------------------------------------
# Erlaubte Ziele für Output-Redirects (>, >>)
# ---------------------------------------------------------------------------
SAFE_REDIRECT_PREFIXES: list[str] = [
    '/dev/null',
    '/dev/stderr',
    '/dev/stdout',
    '.claude/tmp/',
]

# Extrahiert das innere Kommando aus cmd.exe /c "..."
_CMDEXE_INNER_RE = re.compile(r'^cmd\.exe\s+/c\s+"(.*)"')


# ---------------------------------------------------------------------------
# Deny-Patterns
# ---------------------------------------------------------------------------
DENY_PATTERNS: list[tuple[re.Pattern[str], str]] = [
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
    # WSL: Pipe innerhalb cmd.exe
    (
        re.compile(r'^cmd\.exe\s.*\|'),
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
        re.compile(r'^python3\s+[/~]'),
        'python3 mit absolutem Pfad ist nicht erlaubt.\n'
        'Projekt-Scripts immer mit relativem Pfad aufrufen:\n'
        '  python3 .claude/scripts/dotnet-test.py\n'
        '  python3 .claude/scripts/dotnet-stryker.py\n'
        '  python3 .claude/hooks/...',
    ),
    # find mit destruktiven Flags
    (
        re.compile(r'\bfind\b.*\s-delete\b'),
        "find -delete löscht alle gefundenen Dateien – zu destruktiv für Auto-Approve.",
    ),
    (
        re.compile(r'\bfind\b.*\s-exec(?:dir)?\b.*\brm\b'),
        "find -exec rm umgeht den rm-Schutz – zu destruktiv für Auto-Approve.",
    ),
    # Destruktive rm
    (
        re.compile(r'\brm\s+-[a-zA-Z]*[rR]'),
        "rm -r/-rf ist zu destruktiv für Auto-Approve. "
        "Bitte einzelne Dateien/Verzeichnisse benennen oder User fragen.",
    ),
    # Destruktive git-Befehle
    (
        re.compile(r'\bgit\s+push\s+--force\b'),
        "Force-Push ist verboten.",
    ),
    (
        re.compile(r'\bgit\s+reset\s+--hard\b'),
        "git reset --hard ist destruktiv – Änderungen könnten verloren gehen.",
    ),
    (
        re.compile(r'\bgit\s+clean\s+-[a-zA-Z]*f'),
        "git clean -f ist destruktiv – Dateien könnten unwiderruflich gelöscht werden.",
    ),
    (
        re.compile(r'\bgit\s+checkout\s+\.'),
        "git checkout . verwirft alle unstaged Änderungen.",
    ),
    (
        re.compile(r'\bgit\s+restore\s+\.'),
        "git restore . verwirft alle unstaged Änderungen.",
    ),
    # git add -f: ignorierte Dateien könnten Secrets enthalten
    (
        re.compile(r'\bgit\s+add\b.*\s(?:-f\b|--force\b)'),
        "git add -f/--force ist nicht erlaubt. "
        "Wenn das Hinzufügen einer ignorierten Datei wirklich nötig ist, "
        "erkläre dem User warum und nenne den exakten Befehl zur manuellen Ausführung:\n"
        "  git add -f <datei>",
    ),
]


# ---------------------------------------------------------------------------
# Allow-Patterns
# ---------------------------------------------------------------------------
ALLOW_PATTERNS: list[re.Pattern[str]] = [
    # dotnet build über cmd.exe (direkt oder via Variable capturen)
    re.compile(r'^cmd\.exe\s+/c\s+"cd\s+/d\s+.*mahl[^"]*&&\s*dotnet\s+build\b'),
    re.compile(r'^output=\$\(cmd\.exe\s+/c\s+"cd\s+/d\s+.*mahl[^"]*&&\s*dotnet\s+build\b'),
    # dotnet ef (sichere Subcommands; database drop bleibt ask)
    re.compile(r'^cmd\.exe\s+/c\s+"cd\s+/d\s+.*mahl[^"]*&&\s*dotnet\s+ef\s+(migrations\s+(add|remove|list)|database\s+update)\b'),
    # npm run über cmd.exe (npm install bleibt ask – führt externen Code aus)
    re.compile(r'^cmd\.exe\s+/c\s+"cd\s+/d\s+.*mahl\\\\Client\s*&&\s*npm\s+run\s'),
    # python3 -m pytest auf .claude/ (Hook-Tests)
    re.compile(r'^python3\s+-m\s+pytest\s+\.claude/'),
    # Docker
    re.compile(r'^docker-compose\s+(up|down)\b'),
    re.compile(r'^docker\s+compose\s+(up|down)\b'),
    # Lese- und Analyse-Befehle
    re.compile(r'^ls\b'),
    re.compile(r'^cat\b'),
    re.compile(r'^tail\b'),
    re.compile(r'^head\b'),
    re.compile(r'^wc\b'),
    re.compile(r'^grep\b'),
    re.compile(r'^find\b'),
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
    # Python: nur .claude/-Verzeichnis (Projekt-Werkzeuge und Hooks)
    re.compile(r'^python3\s+(?!-)\.claude/'),
    # sed für \r-Bereinigung
    re.compile(r"^sed\s+-i\s+'s/\\\\r//'"),
    re.compile(r'^sed\s+-i\s+"s/\\\\r//"'),
    re.compile(r"^sed\s+-i\s+'s/\\r//'"),
    # git read-only
    re.compile(r'^git\s+(status|log|diff|branch|show|stash\s+list|remote|tag|rev-parse|ls-files|shortlog)\b'),
    # git safe write
    re.compile(r'^git\s+add\b'),
    re.compile(r'^git\s+stash\s+(push|save|pop|apply|drop)\b'),
]


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
                # >> oder > ? Offset berechnen
                offset = 2 if (i + 1 < len(command) and command[i + 1] == '>') else 1
                rest = command[i + offset:]

                # >&N – Redirect zu File-Descriptor (z.B. 2>&1, >&2)
                if rest.startswith('&'):
                    i += 1
                    continue

                # Ziel-Pfad extrahieren
                target_match = re.match(r'\s*(\S+)', rest)
                if target_match:
                    target = target_match.group(1)
                    if any(target.startswith(p) for p in SAFE_REDIRECT_PREFIXES):
                        i += 1
                        continue
                # Kein Ziel oder unsicheres Ziel
                return True

        i += 1

    return False


def split_compound_command(command: str) -> list[str]:
    """Splittet einen Compound-Command an bash-level Operatoren (|, ||, &&, ;).
    Respektiert Anführungszeichen.
    """
    segments: list[str] = []
    current: list[str] = []
    in_single_quote = False
    in_double_quote = False
    i = 0

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
        elif c == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            current.append(c)
        elif not in_single_quote and not in_double_quote:
            if c == '|':
                if i + 1 < len(command) and command[i + 1] == '|':
                    seg = ''.join(current).strip()
                    if seg:
                        segments.append(seg)
                    current = []
                    i += 2
                    continue
                else:
                    seg = ''.join(current).strip()
                    if seg:
                        segments.append(seg)
                    current = []
            elif c == '&' and i + 1 < len(command) and command[i + 1] == '&':
                seg = ''.join(current).strip()
                if seg:
                    segments.append(seg)
                current = []
                i += 2
                continue
            elif c == ';':
                seg = ''.join(current).strip()
                if seg:
                    segments.append(seg)
                current = []
            else:
                current.append(c)
        else:
            current.append(c)

        i += 1

    seg = ''.join(current).strip()
    if seg:
        segments.append(seg)

    return segments


def is_compound_command(command: str) -> bool:
    return len(split_compound_command(command)) > 1


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


def check_simple_command(command: str) -> tuple[str, str]:
    """Prüft einen einzelnen Befehl gegen Deny- und Allow-Patterns."""
    for pattern, reason in DENY_PATTERNS:
        if pattern.search(command):
            return ("deny", reason)
    for pattern in ALLOW_PATTERNS:
        if pattern.search(command):
            if has_unsafe_output_redirect(command):
                return ("deny", _UNSAFE_REDIRECT_DENY_REASON)
            return ("allow", "Auto-approved by bash permission hook")
    return ("fall-through", "")


def check_command(command: str) -> tuple[str, str]:
    """Prüft einen Befehl und gibt (decision, reason) zurück."""
    # 1. Deny auf dem vollständigen Befehl
    for pattern, reason in DENY_PATTERNS:
        if pattern.search(command):
            return ("deny", reason)

    # 2. Compound-Commands: alle Segmente prüfen
    segments = split_compound_command(command)
    if len(segments) > 1:
        for segment in segments:
            seg_decision, seg_reason = check_simple_command(segment)
            if seg_decision == "deny":
                return ("deny", seg_reason)
            if seg_decision == "fall-through":
                return ("fall-through", "")
        return ("allow", "Auto-approved by bash permission hook")

    # 3. Einfacher Befehl: Allow-Patterns mit Redirect-Check
    for pattern in ALLOW_PATTERNS:
        if pattern.search(command):
            if has_unsafe_output_redirect(command):
                return ("deny", _UNSAFE_REDIRECT_DENY_REASON)
            return ("allow", "Auto-approved by bash permission hook")

    return ("fall-through", "")


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

    decision, reason = check_command(command)

    if decision == "deny":
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        }))
        sys.exit(0)

    if decision == "allow":
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "permissionDecisionReason": reason,
            }
        }))
        sys.exit(0)

    # Explizites ask: erzwingt Prompt unabhängig von Claude Code's Session-State
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
