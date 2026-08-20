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
  Erlaubt: <scratchpad>/ – Arbeitsverzeichnis der Session, außerhalb des Repos
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
ONE_TIME_MARKER = '# --allow-once'

_REPO_ROOT = os.environ.get(
    "CLAUDE_PROJECT_DIR",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'),
)

def _resolve_scratchpad() -> str | None:
    """Pfad des Session-Scratchpads (Arbeitsverzeichnis außerhalb des Repos), oder None.

    Muster: /tmp/claude-<uid>/<repo-pfad-mit-bindestrichen>/<session-id>/scratchpad
    Exakt aufgelöst statt per Wildcard – Schreibziel ist nur das eigene Scratchpad,
    nicht das fremder Sessions.
    """
    session_id = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if not session_id:
        return None
    slug = os.path.normpath(_REPO_ROOT).replace('/', '-')
    return f"/tmp/claude-{os.getuid()}/{slug}/{session_id}/scratchpad"


_SCRATCHPAD = _resolve_scratchpad()

SAFE_REDIRECT_PREFIXES: list[str] = [
    '/dev/null',
    '/dev/stderr',
    '/dev/stdout',
]
if _SCRATCHPAD:
    SAFE_REDIRECT_PREFIXES.append(_SCRATCHPAD + '/')
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

# OBS-S085-3: Rewrite statt Deny, damit ein frisch startender Subagent keine Runde verliert.
_FILTER_STRIPPED_HINT = (
    "Der nachgelagerte Filter wurde entfernt – dieser Wrapper gibt im Erfolgsfall nur das "
    "Verdikt aus (ein bis zwei Zeilen), im Fehlerfall nur das zur Analyse Nötige. Ein "
    "`| tail`/`| head` kann das Verdikt sogar abschneiden. Brauchst du mehr Tiefe, nutze "
    "`--verbose` statt eines Filters. Liefert der Wrapper etwas Nötiges gar nicht, ist das "
    "eine Beobachtung für docs/kaizen/observations.md – dann verbessern wir den Wrapper."
)

# OBS-S091-2: Der Wechsel überlebt den Befehl und zerstört die folgenden Wrapper-Aufrufe.
_CD_NPM_HINT = (
    "npm-Befehle ohne Verzeichniswechsel aufrufen:\n"
    "  npm --prefix Client run typecheck   (statt: cd Client && npm run typecheck)\n"
    "  npm --prefix Client ci\n"
    "Grund: Ein `cd` überlebt den Befehl, und die folgenden Wrapper-Aufrufe scheitern dann "
    "an ihrem repo-root-relativen Pfad (`.claude/scripts/…` → „No such file“)."
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
# Nachgelagerte Filter auf Wrapper-Ausgaben (OBS-S085-3)
# ---------------------------------------------------------------------------
# Gemessene Quote nach dem S109-Wrapper-Umbau: 95 % (110 Läufe ab dem Umbau-Commit) gegen
# eine Basislinie von 83 %. Drei Soft-Maßnahmen (Hinweis S087, Rezidiv S090, Output-Umbau
# S109) haben daran nichts geändert – das Verhalten ist antrainiert, nicht bedarfsgetrieben.
# Gewählt wurde der Rewrite statt eines Deny, weil Subagenten immer frisch starten und über
# Sessions nicht lernen können: ein Deny kostet sie jedes Mal eine Runde, der Rewrite keine.
#
# Bewusst NUR die Gate-/Test-Wrapper, deren Ausgabe im Erfolgsfall schon das Verdikt ist.
# Analyse-Scripte (read-breakdown.py, tool-usage.py …) sind zum Zerschneiden gedacht – ein
# Filter darauf ist bestimmungsgemäß. Dieselbe Abgrenzung zieht `tool-usage.py` (WRAPPERS).
_FILTERABLE_WRAPPERS = ("dotnet-test", "dotnet-stryker", "vitest-run", "playwright-test",
                        "stryker-frontend", "eslint-run", "jscpd-run", "qa-check",
                        "stryker-summary")
_WRAPPER_RUN_RE = re.compile(r'python3\s+\S*\.claude/scripts/('
                             + "|".join(_FILTERABLE_WRAPPERS) + r')\.py')
_FILTER_CMD_RE = re.compile(r'(?:tail|head|grep|sed|awk)\b')


def strip_wrapper_filter(command: str) -> tuple[str, bool]:
    """Entfernt nachgelagerte Filter-Pipes hinter einem Wrapper-Aufruf.

    Gibt (neuer_befehl, geändert) zurück. Zwei Abgrenzungen tragen die Korrektheit:
    Ein Filter **vor** dem Wrapper filtert dessen Ausgabe nicht (`grep … | python3 … .py`)
    und bleibt unberührt; und alles zwischen Wrapper und erstem Filter bleibt erhalten,
    damit Argumente und Redirects (`--layer frontend 2>&1`) nicht verlorengehen.
    """
    match = _WRAPPER_RUN_RE.search(command)
    if not match:
        return command, False

    parts = command[match.end():].split("|")
    keep = [parts[0]]
    for part in parts[1:]:
        if _FILTER_CMD_RE.match(part.strip()):
            break  # ab hier ist der Rest reine Filterung
        keep.append(part)

    if len(keep) == len(parts):
        return command, False
    return (command[:match.end()] + "|".join(keep)).rstrip(), True


# ---------------------------------------------------------------------------
# Verzeichniswechsel vor npm (OBS-S091-2)
# ---------------------------------------------------------------------------
_CD_TARGET_RE = re.compile(r'^cd\s+(\S+)')
_NPM_SEGMENT_RE = re.compile(r'^npm\b')


def cd_npm_conflict(segments: list[str]) -> bool:
    """Verlässt ein Segment den Repo-Root, und nutzt ein späteres Segment `npm`?

    Der Wechsel selbst wäre harmlos – aber er überlebt den Befehl, und die FOLGENDEN
    Wrapper-Aufrufe scheitern dann an ihrem repo-root-relativen Pfad (`.claude/scripts/…`).
    In S111 belegt: vier Wrapper-Fehlschläge nach einem `cd Client`. `npm --prefix <dir>`
    erreicht dasselbe ohne Wechsel, es gibt also keinen Bedarf, den die Regel bestraft.
    """
    left_root = False
    for segment in segments:
        stripped = segment.strip()
        target = _CD_TARGET_RE.match(stripped)
        if target:
            # `cd .` (auch der normalisierte bare-root) bleibt im Repo-Root → unkritisch.
            left_root = target.group(1).rstrip("/") not in (".", "")
        elif left_root and _NPM_SEGMENT_RE.match(stripped):
            return True
    return False


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


# `npm run <script>`, wahlweise mit vorangestelltem `--prefix <dir>`. Das Fragment MUSS in den
# Allow- UND den Wrong-Approach-Mustern dasselbe sein: erlaubte man `--prefix` nur im Allow-Teil,
# liefe `npm --prefix Client run test` an der Wrapper-Pflicht vorbei (die Muster verlangen sonst
# npm und run direkt nebeneinander).
_NPM_RUN = r'\bnpm\s+(?:--prefix\s+\S+\s+)?run\s+'

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
        re.compile(_NPM_RUN + r'test:e2e\b'),
        'E2E-Tests immer via Script aufrufen:\n'
        '  python3 .claude/scripts/playwright-test.py [--filter Pattern] [--verbose]',
    ),
    # Frontend Unit-Tests: immer via vitest-run.py (test:coverage und test:e2e sind ausgenommen)
    (
        re.compile(_NPM_RUN + r'test(?![\w:])'),
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
        re.compile(r'\bnpx\s+eslint\b|' + _NPM_RUN + r'lint\b'),
        'ESLint immer via Script aufrufen:\n'
        '  python3 .claude/scripts/eslint-run.py [--verbose]',
    ),
    # npx jscpd / npm run lint:duplicates: immer via jscpd-run.py
    (
        re.compile(r'\bnpx\s+jscpd\b|' + _NPM_RUN + r'lint:duplicates\b'),
        'jscpd immer via Script aufrufen:\n'
        '  python3 .claude/scripts/jscpd-run.py [--verbose]',
    ),
    # python3 mit absolutem Pfad (Ausnahmen, beide in ALLOW_PATTERNS: das globale
    # recall-session-Script und das Session-Scratchpad – beide liegen zwangsläufig
    # außerhalb des Repos, ein relativer Pfad existiert dafür nicht)
    (
        re.compile(r'\bpython3\s+(?!\S*\.claude/skills/recall-session/scripts/recall\.py)'
                   + (r'(?!' + re.escape(_SCRATCHPAD) + r'/)' if _SCRATCHPAD else '')
                   + r'[/~]'),
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
# Scripte, die inhaltliche Einträge in versionierte Projektdokumente schreiben.
#
# Sie sind fachlich erwünscht – sie garantieren die Eintragsform und ersparen den vom Harness
# erzwungenen Vor-Edit-Read der ganzen Datei. Genau dadurch umgehen sie aber den Freigabe-Dialog,
# den `Edit`/`Write` auslösen: Der geschriebene Text liefe sonst nirgends am User vorbei. Deshalb
# `ask` statt `allow` – der Befehl steht samt Text im Freigabe-Prompt.
#
# Bewusst NICHT hier: rein mechanische Umbauten ohne neuen Text (`obs-archive.py` verschiebt
# aufgelöste Einträge ins Archiv) und alle `get`-Unterbefehle (read-only).
WRITE_ACCESS_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r'\.claude/scripts/obs\.py\s+(?:add|set)\b'),
        'obs.py add/set schreibt einen Eintrag nach docs/kaizen/observations.md. Freigabe wie '
        'bei einem Edit, damit der Text vor dem Schreiben sichtbar ist.',
    ),
    (
        re.compile(r'\.claude/scripts/lessons\.py\s+add\b'),
        'lessons.py add schreibt einen Eintrag nach docs/kaizen/lessons_learned.md. Freigabe wie '
        'bei einem Edit, damit der Text vor dem Schreiben sichtbar ist.',
    ),
]

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
        # `config` rendert die effektive Compose-Konfiguration und startet nichts.
        re.compile(r'^docker\s+compose\s+(up|down|config)\b'),
        None,
        'docker compose up|down|config',
    ),
    # npm run/audit/outdated/update/ci (nativ). npm run test|lint → WRONG_APPROACH; npm install [pkg] → deny.
    # `--prefix <dir>` ist erlaubt, damit npm-Scripts nicht erst ein `cd Client` erzwingen – dieses
    # cd ließ danach jeden repo-root-relativen Wrapper-Aufruf scheitern.
    (
        re.compile(r'^npm\s+(?:--prefix\s+\S+\s+)?(?:run\s|audit\b|outdated\b|update\b|ci\b)'),
        None,
        'npm [--prefix <dir>] run <script> | audit | outdated | update | ci',
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
    (re.compile(r'^printf\b'), 'Shell', 'printf'),   # wie echo: schreibt nur nach stdout
    # Bedingungs-Builtin, wertet nur aus.
    (re.compile(r'^test\s'), 'Shell', 'test'),
    (re.compile(r'^\[\s'), 'Shell', '[ … ]  (test)'),
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
        # `xargs` selbst genügt: expand_segment trennt das Sub-Kommando ab und prüft
        # es voll – strenger als eine Namens-Whitelist, die Argumente ungesehen ließe.
        re.compile(r'^xargs\b'),
        'Shell',
        'xargs grep|cat|wc|head|tail|file|stat|sort|uniq|cut|ls',
    ),
    (re.compile(r'^pwd$'), 'Shell', 'pwd'),
    (re.compile(r'^date\b'), 'Shell', 'date'),
    # Liest/verarbeitet wie sed/cut/tr, schreibt nichts – Parität zu `cat`/`head`/`sed -n`.
    (re.compile(r'^awk\b'), 'Shell', 'awk (read-only)'),
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
    # Wegwerf-Scripte im Session-Scratchpad – der reguläre Ort für Ad-hoc-Auswertungen.
    *([(
        re.compile(r'^python3\s+(?!-)' + re.escape(_SCRATCHPAD) + r'/\S+\.py\b'),
        None,
        'python3 <scratchpad>/<script>.py  (Wegwerf-Auswertungen)',
    )] if _SCRATCHPAD else []),
    # Globales recall-session-Script (read-only Session-Log-Analyse, liegt unter
    # ~/.claude/skills/ außerhalb des Repos). Absoluter Pfad ist hier erlaubt –
    # die WRONG_APPROACH-Regel für absolute python3-Pfade nimmt es explizit aus.
    # Per-Segment-Check bleibt: in Compounds wird jeder andere Teil weiter geprüft.
    (
        re.compile(r'^python3\s+\S*\.claude/skills/recall-session/scripts/recall\.py\b'),
        None,
        'python3 ~/.claude/skills/recall-session/scripts/recall.py <befehl>  (read-only Session-Log-Analyse)',
    ),
    # git read-only (optional mit -C <pfad>, um in anderem Repo/Worktree zu lesen)
    (
        re.compile(r'^git\s+(?:-C\s+\S+\s+)?(status|log|diff|branch|show|remote|tag|rev-parse|ls-files|shortlog|check-ignore)\b'),
        None,
        'git [-C <pfad>] status|log|diff|branch|show|remote|tag|rev-parse|ls-files|shortlog|check-ignore',
    ),
    # git safe write (explizit kein -f/--force – das ist in WRONG_APPROACH_PATTERNS)
    (re.compile(r'^git\s+add\b(?!.*\s(?:-f\b|--force\b))'), None, 'git add <datei>  (ohne -f/--force)'),
    (re.compile(r'^git\s+stash\s+(list|push|save|pop|apply|drop)\b'), None, 'git stash list|push|save|pop|apply|drop'),
    # git hash-object: berechnet Blob-SHA (mit -w höchstens ein unreferenziertes Blob-Objekt in
    # die Object-DB) – verändert weder Working Tree, Index, Refs noch History. Keine gefährlichen
    # Flags → beliebige Optionen/Dateien erlaubt. Nutzung: Test-Freigabe-Anker (qa-check --approved-tests).
    (
        re.compile(r'^git\s+(?:-C\s+\S+\s+)?hash-object\b'),
        None,
        'git [-C <pfad>] hash-object [-w] <datei>…  (Blob-SHA für Test-Freigabe-Anker)',
    ),
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
        "Für Ad-hoc-Analyse: Script ins Scratchpad schreiben (Write-Tool), dann\n"
        "  python3 <scratchpad>/foo.py\n"
        "Das Scratchpad liegt außerhalb des Repos und verschwindet mit der Session –\n"
        "nichts muss aufgeräumt werden.\n"
        "Für Datei-Inspektion: Read/Grep/Glob-Tools statt Python.",
    ),
    (
        re.compile(r'^(?:for|while)\b'),
        "Schleifen sind erlaubt, solange jeder Befehl im Rumpf erlaubt und lesend ist.\n"
        "Geblockt wurde also ein Befehl im Rumpf, nicht die Schleife selbst – der Hinweis\n"
        "oben nennt ihn. Datei-Operationen (rm/mv/cp/chmod) sind im Rumpf grundsätzlich\n"
        "gesperrt: wie oft sie laufen, ist vor der Ausführung nicht sichtbar.",
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
    "Für Ad-hoc-Logik: Script ins Scratchpad schreiben, dann python3 <scratchpad>/foo.py.\n"
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

_ONE_TIME_UNNEEDED_HINT = (
    "Hinweis: '# --allow-once' war nicht nötig – dieser Befehl steht ohnehin auf der Allow-Liste "
    "und wurde direkt ausgeführt. Künftig ohne Marker aufrufen; der Marker ist nur für echte "
    "Deny-Fälle gedacht (sonst inflationär)."
)

_INDIRECT_EXEC_DENY_REASON = (
    "Indirekte Befehlsausführung ist nicht erlaubt.\n"
    "Der auszuführende Befehl steht hier nicht im Klartext (Variable, Substitution, "
    "eval/source/bash -c) – damit lässt sich jede Prüfung umgehen:\n"
    "  CMD=\"rm -rf /\"; $CMD\n"
    "Befehl direkt hinschreiben. Braucht es wirklich Shell-Logik, gehört sie in ein "
    "Script im Scratchpad statt in einen Einzeiler."
)

_LOOP_WRITE_DENY_REASON = (
    "Datei-Operationen im Schleifenrumpf sind nicht erlaubt.\n"
    "`rm`/`mv`/`cp` sind einzeln erlaubt, in einer Schleife baut man daraus aber ein "
    "`rm -rf` – und wie oft der Rumpf läuft, ist vor der Ausführung nicht sichtbar.\n"
    "Betroffene Dateien einzeln nennen, oder ein Script im Scratchpad schreiben, das "
    "vorher anzeigt was es täte."
)

_UNSAFE_REDIRECT_DENY_REASON = (
    "Output-Redirect auf nicht erlaubtes Ziel.\n"
    "Bevorzugte Alternative: Output in Variable capturen (kein Datei-Müll):\n"
    "  output=$(dotnet build)\n"
    "  echo \"$output\" | grep ...\n"
    "Falls Datei-Redirect nötig (sehr großer Output): nur ins Scratchpad – es liegt außerhalb\n"
    "des Repos und verschwindet mit der Session, es bleibt also nichts liegen.\n"
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

    Erlaubt: SAFE_REDIRECT_PREFIXES (Session-Scratchpad, /dev/null)
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


def strip_heredoc_bodies(command: str) -> str:
    """Entfernt Heredoc-Bodies – sie sind Daten, kein Code.

    Sonst sucht der Splitter im Fließtext nach `|`/`;`/`&&` und zerlegt ihn in
    „Befehle", die kein Allow-Muster treffen.

    Der Konsument bleibt geprüft: nach dem Strippen steht noch `python3 -` bzw.
    `bash` da, beides ohne Allow-Muster. Ein Heredoc erkauft keine Freigabe.

    Fail-closed bei fehlendem Endmarker: Rest bleibt stehen und wird geprüft.
    """
    in_single = in_double = False
    i = 0
    while i < len(command):
        c = command[i]

        if c == '\\' and not in_single:
            i += 2
            continue
        if c == "'" and not in_double:
            in_single = not in_single
            i += 1
            continue
        if c == '"' and not in_single:
            in_double = not in_double
            i += 1
            continue
        if in_single or in_double:
            i += 1
            continue

        # Ab hier: außerhalb von Quotes. `<<` startet ein Heredoc – aber `<<<`
        # ist ein Here-String (einzeiliger Wert, kein Body zum Entfernen).
        if command.startswith('<<', i) and not command.startswith('<<<', i):
            m = re.match(r"<<-?\s*(['\"]?)(\w+)\1", command[i:])
            if not m:
                i += 2
                continue
            marker = m.group(2)
            body_start = command.find('\n', i)
            if body_start == -1:
                return command[:i]  # Heredoc angekündigt, aber kein Body → Rest ist leer
            # Endmarker: eigene Zeile, nur der Marker (bei <<- mit führendem Whitespace)
            end_re = re.compile(r'^[ \t]*' + re.escape(marker) + r'[ \t]*$', re.M)
            end = end_re.search(command, body_start)
            if not end:
                i += 2  # fail-closed: Body bleibt stehen und wird geprüft
                continue
            # Heredoc-Operator und Body herausschneiden, Rest weiter untersuchen
            command = command[:i] + command[end.end():]
            continue

        i += 1

    return command


# Shell-Strukturwörter, die selbst kein Kommando sind (Schleifen/Bedingungen).
_LOOP_OPEN_RE = re.compile(r'^(for|while|until)\b')
_STRUCT_ONLY_RE = re.compile(r'^(do|done|then|fi|else|elif|esac|;;)\b|^(do|done|then|fi|else|esac)$')
_LEADING_STRUCT_RE = re.compile(r'^(?:do|then|else)\s+')
_IF_OPEN_RE = re.compile(r'^(if|case)\b')

# Variablen-Zuweisungs-Präfixe: `FOO=bar cmd`, `out=$(cmd)`, `A=1 B=2 cmd`
_ASSIGN_PREFIX_RE = re.compile(r'^[A-Za-z_][A-Za-z_0-9]*=(?:"[^"]*"|\'[^\']*\'|[^\s;|&]*)\s*')

# Kommando-Substitution und Prozess-Substitution
_SUBST_RE = re.compile(r'\$\(([^()]*(?:\([^()]*\)[^()]*)*)\)|`([^`]*)`|<\(([^()]*)\)|>\(([^()]*)\)')

# Indirekte Ausführung: der Befehlsname selbst stammt aus einer Expansion, oder
# ein Interpreter führt beliebigen Text aus. Beides umgeht jede Musterprüfung,
# weil zur Prüfzeit nur `$CMD` bzw. der Interpreter dasteht.
_INDIRECT_EXEC_RE = re.compile(
    r'^\s*(?:"?\$\{?[A-Za-z_]|\$\()'                      # $VAR …, ${VAR} …, "$VAR" …, $(…) …
    r'|^\s*(?:eval|exec|source)\b'
    r'|^\s*\.\s+\S'                                        # . script.sh
    r'|^\s*(?:ba|da|k|z)?sh\s+-c\b'
    r'|^\s*sh\s+-c\b'
)


# Befehle, die einen übergebenen String AUSFÜHREN statt ihn als Daten zu behandeln.
# Nur bei diesen darf ein quotiertes Argument die Wrapper-Pflicht auslösen; bei allen
# anderen ist ein String ein Suchmuster, ein Beschreibungstext oder eine Commit-Message.
_STRING_EXECUTING_CMDS = re.compile(
    r'^\s*(?:eval|exec|source|\.|bash|sh|dash|ksh|zsh|xargs|watch|env|nohup|sudo|timeout|find)\b'
)

_QUOTED_STRING_RE = re.compile(r'"[^"]*"|\'[^\']*\'')


def mask_data_strings(command: str) -> str:
    """Maskiert quotierte Argumente, sofern der Befehl sie als Daten behandelt.

    Die Wrapper-Pflicht prüft den rohen Befehlstext und trifft sonst auch Befehle, die
    einen Namen nur ERWÄHNEN – eine Volltextsuche nach 'npx vitest' galt als Start.

    `eval "npx vitest"` und `xargs npx vitest` bleiben voll geprüft: dort ist der String
    Code. Segmentweise, damit `grep "…" | eval "…"` nicht mitmaskiert wird.
    """
    parts = []
    for segment in split_compound_command(command):
        if _STRING_EXECUTING_CMDS.match(segment):
            parts.append(segment)
        else:
            parts.append(_QUOTED_STRING_RE.sub('TEXT', segment))
    return ' ; '.join(parts)


def _split_exec_argument(segment: str) -> tuple[str, str | None]:
    """Trennt `find … -exec CMD …` / `xargs [flags] CMD …` in (Träger, Sub-Kommando).

    Der -exec-Teil ist ein vollwertiges Kommando und wird wie ein eigenes Segment
    geprüft: `find … -exec cat {} \\;` ist damit erlaubt (cat steht auf der Liste),
    `find … -exec rm {} \\;` bleibt destruktiv.
    """
    m = re.search(r'\s-(?:exec|execdir|ok)\s+(.*?)(?:\s+\\;|\s+\+|$)', segment)
    if m:
        return segment[:m.start()], m.group(1).replace('{}', 'DATEI').strip()

    m = re.match(r'^xargs\s+((?:-\S+\s+|\{\}\s+)*)(.+)$', segment)
    if m:
        return 'xargs ' + m.group(1).strip(), m.group(2).replace('{}', 'DATEI').strip()

    return segment, None


def expand_segment(segment: str) -> list[tuple[str, bool]]:
    """Zerlegt ein Segment in die tatsächlich ausgeführten Kommandos.

    Ein Segment kann mehrere enthalten, ohne Top-Level-Operator: `out=$(python3 x.py)`
    führt `python3 x.py` aus, `find … -exec cat {} \\;` führt `cat` aus.

    Gibt (kommando, ist_massenoperation)-Paare zurück; leer bei reiner Struktur oder
    Wertzuweisung. `ist_massenoperation` markiert Kommandos aus `-exec`/`xargs`: die
    laufen einmal pro Fundstelle, also dieselben Grenzen wie ein Schleifenrumpf.
    """
    segment = segment.strip()
    if not segment:
        return []

    # Führendes Strukturwort abstreifen: `do echo $f` → `echo $f`
    segment = _LEADING_STRUCT_RE.sub('', segment).strip()
    if not segment or _STRUCT_ONLY_RE.match(segment):
        return []

    out: list[tuple[str, bool]] = []

    # Eingebettete Substitutionen zuerst einsammeln – sie werden ausgeführt,
    # egal an welcher Stelle sie stehen.
    def collect_substitutions(text: str) -> str:
        def repl(m: re.Match[str]) -> str:
            inner = next((g for g in m.groups() if g is not None), '')
            if inner.strip():
                out.extend(expand_segment(inner))
            return 'WERT'
        return _SUBST_RE.sub(repl, text)

    segment = collect_substitutions(segment)

    # Schleifen-/Bedingungskopf: `for f in a b`, `while [ -f x ]` – der Kopf führt
    # selbst kein Kommando aus (Substitutionen darin sind oben schon erfasst).
    if _LOOP_OPEN_RE.match(segment) or _IF_OPEN_RE.match(segment):
        return out

    # Zuweisungs-Präfixe abstreifen: `FOO=bar ls -la` → `ls -la`; `SP=/pfad` → nichts
    while True:
        stripped = _ASSIGN_PREFIX_RE.sub('', segment, count=1)
        if stripped == segment:
            break
        segment = stripped.strip()
    if not segment:
        return out

    carrier, sub = _split_exec_argument(segment)
    out.append((carrier, False))
    if sub:
        out.extend((cmd, True) for cmd, _ in expand_segment(sub))
    return out


def split_compound_command(command: str) -> list[str]:
    """Splittet einen Compound-Command an bash-level Operatoren (|, ||, &&, ;, Newline).

    Respektiert Anführungszeichen. Gibt immer mindestens [command] zurück.

    Newline ist seit S121 Trenner (OBS-S111-4): vorher war jeder mehrzeilige Befehl
    per Konstruktion ein einziges unbekanntes Segment und wurde immer abgelehnt.

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

        if c == ';' or c == '\n':
            # Newline trennt wie `;`. Ohne das ist ein mehrzeiliger Befehl EIN Segment,
            # und da Allow-Muster per .search() greifen, erlaubt eine passende erste
            # Zeile den ganzen Rest mit (`ls -la\nrm -rf /tmp/x` lief durch).
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

def check_simple_command(command: str, in_loop: bool = False) -> tuple[str, str, str]:
    """Prüft ein einzelnes Segment: INDIRECT → ALLOW → DESTRUCTIVE → deny.

    WRONG_APPROACH wird nicht geprüft – das übernimmt check_command auf dem
    Gesamtbefehl vor dem Split.

    in_loop: Kommando aus einem Schleifenrumpf oder aus `-exec`/`xargs`. Dort sind
    Dateiverwaltungs-Befehle gesperrt – `rm` ist einzeln erlaubt, wiederholt ergibt
    es ein `rm -rf`, und die Wiederholungszahl ist zur Prüfzeit unsichtbar.

    Gibt (decision, reason, log_type) zurück. decision: 'allow' | 'deny'.
    """
    if _INDIRECT_EXEC_RE.search(command):
        return ("deny", _INDIRECT_EXEC_DENY_REASON, "INDIRECT_EXEC")

    for pattern, category, _ in ALLOW_PATTERNS:
        if pattern.search(command):
            if in_loop and category == 'Dateiverwaltung':
                return ("deny", _LOOP_WRITE_DENY_REASON, "LOOP_WRITE")
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
      1. ONE_TIME_MARKER → nackten Befehl klassifizieren (erlaubt → allow+Hinweis, sonst ask+Grund)
      2. Repo-Pfad-Normalisierung (absolute Repo-Pfade → relativ)
      3. WRONG_APPROACH  → deny (auf Gesamtbefehl, vor Split)
      4. Compound-Split  → check_simple_command je Segment
      5. check_simple_command für einfache Befehle

    decision: 'allow' | 'deny' | 'ask'
    """
    # 1. ONE_TIME_MARKER (# --allow-once): nicht blind fragen, sondern den NACKTEN Befehl klassifizieren.
    #    - wäre er ohnehin erlaubt → Marker war unnötig: direkt erlauben + Agent-Hinweis (kein Prompt).
    #    - wäre er deny            → legitimer Einzelfall: ask, und der Deny-Grund/die Gefahr wird dem
    #      User am Freigabe-Prompt als Reason mitgegeben (statt eines kontextlosen „erlauben?").
    if ONE_TIME_MARKER in command:
        bare = command.replace(ONE_TIME_MARKER, "").strip()
        decision, reason, _ = check_command(bare)  # bare hat keinen Marker → terminiert
        if decision == "allow":
            return ("allow", _ONE_TIME_UNNEEDED_HINT, "ONE_TIME_UNNEEDED")
        return ("ask", reason, "ONE_TIME")

    # 2. Repo-Pfad-Normalisierung: absolute Repo-Pfade → relativ, dann auf dem
    #    normalisierten Befehl weiterprüfen (so wird z.B. python3 <absoluter Pfad>
    #    zu python3 .claude/... und matcht die Allow-Liste statt WRONG_APPROACH).
    command, _ = normalize_repo_paths(command)

    # 2b. Heredoc-Bodies sind Daten, kein Code (OBS-S111-4) – vor jeder weiteren
    #     Analyse entfernen, sonst wird Fließtext als Befehlsfolge gelesen.
    command = strip_heredoc_bodies(command)

    # 3. WRONG_APPROACH auf Gesamtbefehl (ohne ^-Anker → matcht auch in Subshells).
    #    String-Argumente nicht-ausführender Befehle werden dabei maskiert: eine
    #    ERWÄHNUNG ist keine Ausführung (OBS-S111-4).
    for pattern, reason in WRONG_APPROACH_PATTERNS:
        if pattern.search(mask_data_strings(command)):
            return ("deny", reason, "WRONG_APPROACH")

    # 3b. Schreibende Zugriffs-Scripte → ask. Muss VOR dem Segment-Check liegen, sonst greift
    #     das generische Allow-Muster für `.claude/scripts/<script>.py` und der Text ginge
    #     ohne Freigabe durch.
    for pattern, reason in WRITE_ACCESS_PATTERNS:
        if pattern.search(command):
            return ("ask", reason, "WRITE_ACCESS")

    # 4. Compound-Split + Segment-Check (check_simple_command ohne WRONG_APPROACH)
    segments = split_compound_command(command)
    is_compound = len(segments) > 1

    # 4a. Verzeichniswechsel vor npm (OBS-S091-2): braucht die Segmente, deshalb erst hier
    #     und nicht als WRONG_APPROACH-Regex auf dem Gesamtbefehl.
    if cd_npm_conflict(segments):
        return ("deny", _CD_NPM_HINT, "WRONG_APPROACH")

    # 4b. Jedes Segment in die tatsächlich ausgeführten Kommandos zerlegen und einzeln
    #     prüfen. `loop_depth` verfolgt Schleifenrümpfe über Segmentgrenzen hinweg –
    #     `for f in …; do rm "$f"; done` zerfällt beim Split in drei Segmente, die
    #     Schleifen-Eigenschaft steckt also nicht im Segment selbst.
    loop_depth = 0
    checked_any = False
    for segment in segments:
        bare = segment.strip()
        if _STRUCT_ONLY_RE.match(bare) and bare.startswith('done'):
            loop_depth = max(0, loop_depth - 1)
            continue

        for cmd, is_mass in expand_segment(segment):
            checked_any = True
            decision, reason, log_type = check_simple_command(
                cmd, in_loop=loop_depth > 0 or is_mass)
            if decision == "deny":
                if is_compound:
                    log_type = f"COMPOUND_{log_type}"
                return ("deny", reason, log_type)

        if _LOOP_OPEN_RE.match(bare):
            loop_depth += 1

    # Kein einziges prüfbares Kommando (leerer Befehl, nur Struktur/Zuweisung) →
    # nicht durchwinken. Fail-closed: was wir nicht klassifizieren, erlauben wir nicht.
    if not checked_any:
        return ("deny", _get_smart_hint(command), "UNKNOWN")

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
# der SessionStart-Injection (session-agenda.py, Modul `bash-allowlist`, ruft --list auf) → eine Quelle.
_SCRIPT_USAGE_HINT: str = (
    "Im Erfolgsfall geben diese Wrapper nur noch das VERDIKT aus – meist ein bis zwei\n"
    "Zeilen (z.B. „✓ 29 Tests grün, 3 Dateien, 9.2s“). Im Fehlerfall nur das, was zur\n"
    "Analyse nötig ist. Ein nachgelagertes | tail / | grep / | head ist damit sinnlos und\n"
    "kann das Verdikt sogar abschneiden. Mehr Tiefe bei Bedarf: --verbose (einheitlich bei\n"
    "allen Wrappern). Details/Beispiele: --help.\n"
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
    print(
        "Zusammensetzen (jedes Teilstück wird einzeln geprüft – erlaubt ist die Struktur,\n"
        "nicht ein Freibrief für ihren Inhalt):\n"
        "  Verkettung   |  ||  &&  ;  sowie Zeilenumbruch\n"
        "  Zuweisung    out=$(befehl); echo \"$out\"\n"
        "  Substitution $(…), `…`, Prozess-Substitution <(…)\n"
        "  Heredoc      befehl <<'EOF' … EOF   (Body gilt als Text, nicht als Befehl)\n"
        "  Schleifen    for/while – im Rumpf nur lesende Befehle, keine Datei-Operationen\n"
        "  Sub-Befehle  find … -exec <befehl> \\;  und  xargs <befehl>\n"
        "\n"
        "Nicht erlaubt, weil es jede Prüfung aushebelt: indirekte Ausführung – der Befehl\n"
        "kommt aus einer Variablen ($CMD), aus eval/source oder aus bash -c."
    )
    print()
    if _SCRATCHPAD:
        print("Scratchpad (Wegwerf-Scripte, Zwischenergebnisse, Redirect-Ziel):")
        print(f"  {_SCRATCHPAD}/")
        print("  Liegt außerhalb des Repos, verschwindet mit der Session – kein Aufräumen nötig.")
        print("  python3 <scratchpad>/<name>.py ist erlaubt, .claude/tmp/ ist KEIN Schreibziel mehr.")
        print()
    print("Schreiben in Projektdokumente (User-Freigabe nötig, kein Marker):")
    print("  python3 .claude/scripts/obs.py add|set …       → docs/kaizen/observations.md")
    print("  python3 .claude/scripts/lessons.py add …       → docs/kaizen/lessons_learned.md")
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
        rewritten, changed = normalize_repo_paths(command)
        hint = _NORMALIZE_HINT if changed else ""

        # Filter-Strip auf dem bereits normalisierten Befehl: so greift das Wrapper-Muster
        # auch bei absolut geschriebenen Pfaden, und beide Rewrites landen in EINEM
        # updatedInput (zwei würden sich gegenseitig überschreiben).
        rewritten, filtered = strip_wrapper_filter(rewritten)
        if filtered:
            changed = True
            hint = (hint + "\n\n" if hint else "") + _FILTER_STRIPPED_HINT

        if changed:
            hso["updatedInput"] = {"command": rewritten}
            hso["additionalContext"] = hint
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
        hso = _build_allow_output(command)
        if log_type == "ONE_TIME_UNNEEDED":  # # --allow-once war unnötig → Agenten nudgen
            hso["additionalContext"] = _ONE_TIME_UNNEEDED_HINT
        print(json.dumps({"hookSpecificOutput": hso}))
        sys.exit(0)

    if decision == "ask":
        # Echten log_type schreiben statt pauschal "ONE_TIME" (OBS-S111-4): sonst sind
        # Design-Rückfragen (WRITE_ACCESS beim Tracker-Schreiben) im Log nicht von
        # echter Reibung (--allow-once, weil kein regulärer Weg existiert) zu trennen –
        # und genau diese Unterscheidung braucht man, um die Allow-Liste zu justieren.
        _log_command(command, log_type)
        hso = {"hookEventName": "PreToolUse", "permissionDecision": "ask"}
        if reason:  # Deny-Grund/Gefahr des nackten Befehls am User-Prompt zeigen (statt kontextlos)
            hso["permissionDecisionReason"] = reason
        print(json.dumps({"hookSpecificOutput": hso}))
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
