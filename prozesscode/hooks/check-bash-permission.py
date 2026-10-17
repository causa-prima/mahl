#!/usr/bin/env python3
"""PreToolUse-Hook: Bash-Kommandos prüfen (deny/allow/ask).

Die Reihenfolge der Prüfungen steht im Docstring von check_command (einzige Quelle).
Umschreibungen (Repo-Pfad → relativ, Filter hinter Wrappern entfernt) liefert der Hook
via updatedInput zurück (s. _build_allow_output).

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
             ONE_TIME | UNSUPPORTED_QUOTING | INDIRECT_WRAPPER_FILTER
"""
import datetime
import json
import os
import re
import sys

# Vorschau für Tracker-Schreibbefehle (OBS-S116-1). Bewusst fail-safe importiert: Dieser Hook
# entscheidet über JEDEN Bash-Aufruf – ein Fehler in der Darstellung darf ihn nie lahmlegen.
try:
    from .. import tracker_preview
except Exception:  # noqa: BLE001 – bewusst jede Ursache, s.o.
    tracker_preview = None


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

# Der Repo-Root im Befehl: wahlweise als Ziel von `cd`, dann entweder bare (optional mit
# Trailing-Slash, gefolgt von Whitespace, Ende oder Shell-Operator) oder mit Pfad-Fortsetzung.
# Bare wird er zu ".", mit Fortsetzung fällt der Präfix weg – außer als bares `cd`-Ziel: Das
# Arbeitsverzeichnis bleibt zwischen Bash-Aufrufen bestehen, und nach einem `cd` in ein
# Unterverzeichnis hieße `cd .` „bleib hier". `cd <root>` ist dann der einzige Rückweg.
_ROOT_RE = re.compile(r'(?P<cd>\bcd\s+)?' + re.escape(_NORMALIZE_ROOT)
                      + r'(?:(?P<bare>/?)(?=\s|$|[&|;])|/)')

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
    "am Paketpfad – `python3 -m prozesscode.…` findet das Paket nur vom Repo-Root aus."
)


def _strip_repo_root(text: str) -> str:
    """Ersetzt den Repo-Root in einem Textstück durch relative Pfade (s. `_ROOT_RE`)."""
    def ersetze(m: re.Match[str]) -> str:
        cd = m.group("cd") or ""
        if m.group("bare") is None:
            return cd
        return m.group(0) if cd else "."
    return _ROOT_RE.sub(ersetze, text)


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
def werkzeug_aufruf(modul: str) -> str:
    """Beide Aufrufformen eines Paketmoduls als Regex-Fragment.

    `-m prozesscode.td` ist der reguläre Weg. Der Pfadaufruf `prozesscode/td.py` scheitert
    heute schon an den paketinternen Importen – das Muster deckt ihn trotzdem ab: Fiele ein
    relativer Import einmal weg, wäre er wieder möglich und dieser Schutz still verschwunden,
    ohne dass irgendetwas anschlüge.
    """
    return rf'(?:-m\s+prozesscode\.{modul}|\S*prozesscode/{modul}\.py)'


_WRAPPER_RUN_RE = re.compile(
    r'python3\s+' + werkzeug_aufruf("(?:" + "|".join(_FILTERABLE_WRAPPERS) + ")"))
_FILTER_CMD_RE = re.compile(r'(?:tail|head|grep|sed|awk)\b')
# Ein Filter, dessen Entfernen mehr ändert als die Menge der Ausgabe: grep mit Exit-Code- oder
# Zähl-Semantik (`-q`, `-c`, `-l`) kehrt sonst still die Logik um, eine Umleitung fiele weg.
_FILTER_MIT_WIRKUNG_RE = re.compile(
    r'^grep\b.*\s-(?:[a-zA-Z]*[qcl][a-zA-Z]*\b|-(?:quiet|silent|count|files-with-matches)\b)|[<>]')
_TEE_RE = re.compile(r'tee\b')
# Ende der eigenen Pipeline eines Wrappers – auf dem maskierten Befehl gesucht, damit ein `)`
# oder `;` in einem Argument sie nicht vorzeitig beendet.
_PIPELINE_ENDE_RE = re.compile(r'&&|\|\||;|\n|\)|`')
# Hinter einem verschachtelten Wrapper: alles, was dessen aufgefangene Ausgabe weiterreichen kann.
_WEITERGABE_RE = re.compile(r'(?<!\|)\|(?!\|)|<<<|<\(|>\(')
_BLOCK_WORT_RE = re.compile(r'(?<![\w-])(do|done|if|fi|case|esac)(?![\w-])')

_INDIRECT_FILTER_REASON = (
    "Die Ausgabe eines Wrappers würde hier gefiltert oder weiterverarbeitet – {erkannt}. "
    "Wrapper geben im Erfolgsfall nur das Verdikt aus; ein Filter kann es abschneiden, und "
    "still umschreiben lässt sich dieser Befehl nicht, ohne seine Bedeutung zu ändern.\n"
    "Ausweg: den Wrapper in einem eigenen Aufruf ungefiltert laufen lassen; mehr Tiefe über "
    "--verbose. Einen fremden Befehl mit Filter in einen eigenen Aufruf legen."
)
# Was `{erkannt}` darin einsetzt – je Fall, den die Prüfung unterscheidet.
_GRUND_PROZESS_SUBSTITUTION = "der Wrapper steht in einer Prozess-Substitution"
_GRUND_STUFE = "in seiner Pipeline steht eine Stufe, die nicht nur filtert"
_GRUND_WEITERGABE = "die aufgefangene Ausgabe kann weitergereicht werden"
_GRUND_HEREDOC = "er steht in einem Befehl mit Heredoc"


_UNGEQUOTETER_HEREDOC_RE = re.compile(r"(?<!<)<<(?!<)-?\s*[A-Za-z_]")
_UNGEQUOTETER_HEREDOC_REASON = (
    "Heredoc ohne Anführungszeichen am Endmarker: Die Shell führt $(…) und `…` im Text aus, "
    "der Hook prüft den Text aber nicht als Befehl.\n"
    "Ausweg: den Marker quoten – <<'EOF' statt <<EOF."
)
_ANSI_C_QUOTE_REASON = (
    "ANSI-C-Quoting ($'…') kann der Hook nicht sicher zerlegen – ein \\' darin verschiebt, wo "
    "der nächste Befehl beginnt.\n"
    "Ausweg: normale Anführungszeichen ('…' oder \"…\"); Sonderzeichen über printf erzeugen."
)


def _maskiere_strings(command: str) -> str:
    """Gleich lange Kopie, in der Text in Anführungszeichen durch `_` ersetzt ist.

    Ausgenommen sind Befehlssubstitutionen `$(…)` und `` `…` `` in doppelten Anführungszeichen
    – sie werden ausgeführt, ein Wrapper darin ist ein Aufruf. Eine Zeilenfortsetzung (`\\`
    vor dem Zeilenumbruch) wird maskiert: Sie trennt keine Befehle. Gleiche Länge, damit
    Positionen aus der maskierten Fassung auf das Original übertragbar bleiben.

    Strings innerhalb einer solchen Substitution werden ebenfalls maskiert (`"$(grep '^$' x)"`
    – im Bestand vorgekommen), ohne dort Escapes oder weitere Verschachtelung zu verfolgen.
    """
    zeichen = list(command)
    quote, innen, tiefe, backtick, i = None, None, 0, False, 0
    while i < len(command):
        c = command[i]
        if quote == "'":
            if c == "'":
                quote = None
            else:
                zeichen[i] = "_"
        elif quote == '"' and backtick:
            backtick = c != "`"
        elif quote == '"' and tiefe and innen:
            if c == innen:
                innen = None
            else:
                zeichen[i] = "_"
        elif quote == '"' and tiefe:
            if c in "'\"":
                innen = c
            else:
                tiefe += {"(": 1, ")": -1}.get(c, 0)
        elif quote == '"':
            if command.startswith("$(", i):
                tiefe = 1
                i += 1
            elif c == "`":
                backtick = True
            elif c == '"':
                quote = None
            else:
                zeichen[i] = "_"
                if c == "\\" and i + 1 < len(command):
                    i += 1
                    zeichen[i] = "_"
        elif c == "\\" and command.startswith("\n", i + 1):
            zeichen[i] = zeichen[i + 1] = "_"
            i += 1
        elif c == "\\":
            i += 1
        elif c in "'\"":
            quote = c
        i += 1
    return "".join(zeichen)


def _umschliessung(maskiert_davor: str) -> str | None:
    """Das innerste Konstrukt, in dem ein Wrapper steht und dessen Ausgabe auffängt.

    `"<("`/`">("` für Prozess-Substitution, `"("`/`"{"`/`` "`" `` für Substitution, Subshell,
    Gruppe, `"block"` für Schleife/if/case – oder None, wenn der Wrapper frei steht.
    """
    if maskiert_davor.count("`") % 2:
        return "`"
    offen: list[int] = []
    for i, c in enumerate(maskiert_davor):
        if c in "({":
            offen.append(i)
        elif c in ")}" and offen:
            offen.pop()
    if offen:
        pos = offen[-1]
        if maskiert_davor[pos] == "(" and maskiert_davor[pos - 1:pos] in ("<", ">"):
            return maskiert_davor[pos - 1:pos + 1]
        return maskiert_davor[pos]
    woerter = [m.group(1) for m in _BLOCK_WORT_RE.finditer(maskiert_davor)]
    for auf, zu in (("do", "done"), ("if", "fi"), ("case", "esac")):
        if woerter.count(auf) > woerter.count(zu):
            return "block"
    return None


def _stufen_urteil(stufen: list[str]) -> str:
    """Einordnung der Stufen hinter einem Wrapper: 'tee', 'filter' oder 'andere'."""
    stufen = [s.strip() for s in stufen]
    if all(_TEE_RE.match(s) and ">(" not in s for s in stufen):
        return "tee"  # reicht die vollständige Ausgabe durch
    if all(_FILTER_CMD_RE.match(s) and not _FILTER_MIT_WIRKUNG_RE.search(s) for s in stufen):
        return "filter"
    return "andere"


def _bewerte_wrapper(command: str) -> tuple[str | None, list[tuple[int, int]]]:
    """(Ablehnungsgrund oder None, zu entfernende Bereiche) für alle Wrapper-Aufrufe.

    Je Wrapper drei Fälle, entschieden an der Struktur des maskierten Befehls:
    - **eigene Pipeline** bis zur ersten Verkettung, zum Zeilenumbruch oder zur schließenden
      Klammer: Folgen nur einfache Filter, werden sie entfernt; ein reines `tee` bleibt;
      jede andere Stufe (`wc`, `grep -q`, Umleitung, `>(…)`, `|&`) führt zur Ablehnung, weil
      das Entfernen die Bedeutung änderte.
    - **verschachtelt** (`$(…)`, Subshell, Gruppe, Schleife, if): Die Ausgabe fließt weiter.
      Wird danach gepiped, per Here-String oder `${…}` weiterverarbeitet → Ablehnung.
      In Prozess-Substitution (`head <(wrapper)`) immer.
    - **frei**: Was hinter der eigenen Pipeline steht, ist ein fremder Befehl und bleibt.
    """
    maskiert = _maskiere_strings(command)
    schnitte: list[tuple[int, int]] = []
    for match in _WRAPPER_RUN_RE.finditer(maskiert):
        umschliessung = _umschliessung(maskiert[:match.start()])
        if umschliessung in ("<(", ">("):
            return _GRUND_PROZESS_SUBSTITUTION, []

        ende = _PIPELINE_ENDE_RE.search(maskiert, match.end())
        pipeline_ende = ende.start() if ende else len(maskiert)
        stufen = maskiert[match.end():pipeline_ende].split("|")[1:]
        urteil = _stufen_urteil(stufen)  # ohne Stufen: "tee" – nichts zu entfernen
        if urteil == "andere":
            return _GRUND_STUFE, []
        if urteil == "filter":
            schnitte.append((maskiert.index("|", match.end()), pipeline_ende))

        # `${` bewusst im unmaskierten Befehl: `"${out: -200}"` steht in Anführungszeichen und
        # wäre in der Maske unsichtbar.
        if umschliessung and (_WEITERGABE_RE.search(maskiert, pipeline_ende)
                              or "${" in command[pipeline_ende:]):
            return _GRUND_WEITERGABE, []
    return None, schnitte


def strip_wrapper_filter(command: str) -> tuple[str, bool]:
    """Entfernt einfache Filter in der eigenen Pipeline jedes Wrapper-Aufrufs.

    Gibt (neuer_befehl, geändert) zurück. Abgrenzungen (Einzelheiten: `_bewerte_wrapper`):
    Ein Filter **vor** dem Wrapper filtert dessen Ausgabe nicht und bleibt; Argumente und
    Redirects des Wrappers (`--layer frontend 2>&1`) bleiben; was hinter der eigenen Pipeline
    steht, bleibt unverändert. Fälle, in denen ein Rewrite raten müsste, lehnt `check_command`
    ab, bevor es hierher kommt.

    Die Grenzen halten zwei Fehlformen fern. Ein Strip, der alles ab dem Filter verwirft,
    verliert ein `&& nächster-befehl` – ausgeführt würde weniger als angefordert. Einer, der
    alles hinter dem Wrapper durchsucht, entfernt Filter fremder Befehle (`wrapper && git log
    | head`), reißt eine schließende Klammer mit und liest Wrapper-Namen in Strings als Aufruf.
    """
    grund, schnitte = _bewerte_wrapper(command)
    if grund or not schnitte:
        return command, False
    for von, bis in reversed(schnitte):
        davor, danach = command[:von].rstrip(), command[bis:]
        # Stand der Filter hinter einer Zeilenfortsetzung, fällt der Backslash mit weg.
        davor = davor.removesuffix("\\").rstrip()
        # `.rstrip()` nimmt den Abstand vor dem Filter mit – `&&`/`||` bekommen ihn zurück;
        # `;`, `)` und Zeilenumbruch schließen direkt an.
        command = davor + (" " if danach.startswith(("&&", "||")) else "") + danach
    return command, True


def wrapper_filter_ablehnung(command: str) -> str | None:
    """Grund für die Ablehnung, wenn die Wrapper-Ausgabe nicht sicher umschreibbar gefiltert wird.

    Grenzen: Der Umweg über eine Datei (`wrapper > x`, später `head x`) ist für eine Prüfung
    des Befehlstexts unsichtbar. Hinter einem verschachtelten Wrapper wird jede Weitergabe
    abgelehnt, auch eine ohne Bezug zu ihm (`out=$(wrapper); git log | head`) – im Zweifel
    laut statt still.
    """
    grund, _ = _bewerte_wrapper(command)
    return _INDIRECT_FILTER_REASON.format(erkannt=grund) if grund else None


# ---------------------------------------------------------------------------
# Verzeichniswechsel vor npm (OBS-S091-2)
# ---------------------------------------------------------------------------
_CD_TARGET_RE = re.compile(r'^cd\s+(\S+)')
_NPM_SEGMENT_RE = re.compile(r'^npm\b')


def cd_npm_conflict(segments: list[str]) -> bool:
    """Verlässt ein Segment den Repo-Root, und nutzt ein späteres Segment `npm`?

    Der Wechsel selbst wäre harmlos – aber er überlebt den Befehl, und die FOLGENDEN
    Wrapper-Aufrufe scheitern dann am Paketpfad (`prozesscode` ist von dort nicht auffindbar).
    In S111 belegt: vier Wrapper-Fehlschläge nach einem `cd Client`. `npm --prefix <dir>`
    erreicht dasselbe ohne Wechsel, es gibt also keinen Bedarf, den die Regel bestraft.
    """
    left_root = False
    for segment in segments:
        stripped = segment.strip()
        target = _CD_TARGET_RE.match(stripped)
        if target:
            # `cd .` und `cd <root>` (bleibt absolut, s. `_ROOT_RE`) → im Repo-Root, unkritisch;
            # `cd /` ist die Dateisystem-Wurzel.
            left_root = target.group(1).rstrip("/") not in (".", _NORMALIZE_ROOT)
        elif left_root and _NPM_SEGMENT_RE.match(stripped):
            return True
    return False


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def _log_command(command: str, log_type: str, log_file: str | None = None) -> None:
    """Protokolliert einen Befehl in einem Log (Default: denied-commands.log).

    log_type: ALLOW | WRONG_APPROACH | DESTRUCTIVE | UNSAFE_REDIRECT | UNKNOWN |
              COMPOUND_DESTRUCTIVE | COMPOUND_UNSAFE_REDIRECT | COMPOUND_UNKNOWN |
              ONE_TIME
    log_file: Zielpfad – erlaubte Befehle gehen nach _ALLOWED_LOG_FILE (OBS-S085-3 D),
              alles andere nach _LOG_FILE.
    Fehler beim Schreiben dürfen den Hook nicht unterbrechen.

    Der Default wird erst beim Aufruf aufgelöst: Als Default-Argument band er `_LOG_FILE` beim
    Import, und ein Test, der das Log umlenkte, schrieb trotzdem ins echte Deny-Log (S133) –
    die Datenquelle, aus der die Retro Reibung misst.
    """
    log_file = log_file or _LOG_FILE
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
        '  python3 -m prozesscode.dotnet-test [--filter TestName] [--verbose]\n'
        '--verbose zeigt den vollständigen Output.',
    ),
    # Stryker: immer via Wrapper-Script aufrufen
    (
        re.compile(r'\bdotnet\s+stryker\b'),
        'Stryker immer via Script aufrufen (führt stryker + Auswertung in einem Schritt aus):\n'
        '  python3 -m prozesscode.dotnet-stryker [--mutate Domain/Foo.cs] [--verbose]\n'
        '--verbose: zeigt alle nicht-getöteten Mutanten mit Status, StatusReason, Zeile und Spalte.',
    ),
    # mutmut: immer via Wrapper – der Rohlauf schüttet minutenlang Fortschritt aus und
    # nennt am Ende nur Emoji-Zähler, ohne zu sagen, WELCHE Mutanten überlebt haben.
    (
        re.compile(r'(?:^|\s|/)mutmut\s+(?:run|results|browse|show|apply)\b'),
        'mutmut immer via Script aufrufen (Lauf + Auswertung in einem Schritt):\n'
        '  python3 -m prozesscode.mutmut-run [--mutate prozesscode.anchors] [--verbose]\n'
        '--mutate nimmt einen Modulpfad, keinen Dateipfad – mutmut adressiert Mutanten so.',
    ),
    # Frontend E2E-Tests: immer via playwright-test.py (vor dem test-Pattern prüfen)
    (
        re.compile(_NPM_RUN + r'test:e2e\b'),
        'E2E-Tests immer via Script aufrufen:\n'
        '  python3 -m prozesscode.playwright-test [--filter Pattern] [--verbose]',
    ),
    # Frontend Unit-Tests: immer via vitest-run.py (test:coverage und test:e2e sind ausgenommen)
    (
        re.compile(_NPM_RUN + r'test(?![\w:])'),
        'Frontend-Tests immer via Script aufrufen:\n'
        '  python3 -m prozesscode.vitest-run [--filter Pattern] [--verbose]',
    ),
    # npx vitest: immer via vitest-run.py
    (
        re.compile(r'\bnpx\s+vitest\b'),
        'Vitest immer via Script aufrufen:\n'
        '  python3 -m prozesscode.vitest-run [--filter Pattern] [--verbose]',
    ),
    # npx playwright: immer via playwright-test.py
    (
        re.compile(r'\bnpx\s+playwright\b'),
        'Playwright immer via Script aufrufen:\n'
        '  python3 -m prozesscode.playwright-test [--filter Pattern] [--verbose]',
    ),
    # npx stryker: immer via stryker-frontend.py
    (
        re.compile(r'\bnpx\s+stryker\b'),
        'Stryker (Frontend) immer via Script aufrufen:\n'
        '  python3 -m prozesscode.stryker-frontend [--mutate src/pages/Foo.tsx] [--verbose]',
    ),
    # npx eslint / npm run lint: immer via eslint-run.py. `(?!:)`: `lint:duplicates` hat
    # unten eine eigene Regel – `\b` allein träfe es hier schon und nennte den falschen Wrapper.
    (
        re.compile(r'\bnpx\s+eslint\b|' + _NPM_RUN + r'lint\b(?!:)'),
        'ESLint immer via Script aufrufen:\n'
        '  python3 -m prozesscode.eslint-run [--verbose]',
    ),
    # npx jscpd / npm run lint:duplicates: immer via jscpd-run.py
    (
        re.compile(r'\bnpx\s+jscpd\b|' + _NPM_RUN + r'lint:duplicates\b'),
        'jscpd immer via Script aufrufen:\n'
        '  python3 -m prozesscode.jscpd-run [--verbose]',
    ),
    # python3 mit absolutem Pfad. Zwei Ausnahmen, beide liegen zwangsläufig außerhalb des
    # Repos – ein relativer Pfad existiert dafür nicht:
    #   recall-session: steht in ALLOW_PATTERNS, läuft also durch.
    #   Scratchpad: seit S130 NICHT mehr erlaubt (s. dort). Der Lookahead bleibt trotzdem,
    #     damit der Aufruf als gewöhnliches Deny mit der Werkzeugfrage landet statt mit
    #     „nutze einen relativen Pfad" – ein Rat, den man hier nicht befolgen kann.
    (
        re.compile(r'\bpython3\s+(?!\S*\.claude/skills/recall-session/scripts/recall\.py)'
                   + (r'(?!' + re.escape(_SCRATCHPAD) + r'/)' if _SCRATCHPAD else '')
                   + r'[/~]'),
        'python3 mit absolutem Pfad ist nicht erlaubt.\n'
        'Projekt-Scripts immer mit relativem Pfad aufrufen:\n'
        '  python3 -m prozesscode.dotnet-test\n'
        '  python3 -m prozesscode.dotnet-stryker\n'
        '  python3 -m prozesscode.hooks.<hook>',
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
# `ask` statt `allow`. Der Prompt nennt, was angefasst wird (`tracker_preview`); die Änderung
# selbst zeigt der Mod `tracker-diff` im Pane daneben.
#
# Bewusst NICHT hier: rein mechanische Umbauten ohne neuen Text (`obs-archive.py` verschiebt
# aufgelöste Einträge ins Archiv) und alle `get`-Unterbefehle (read-only).
def _mit_vorschau(command: str, reason: str) -> str:
    """Stellt dem Freigabe-Grund die Kopfzeile aus `tracker_preview` voran (OBS-S116-1).

    Jeder Fehlschlag fällt auf den reinen Hinweistext zurück: Ohne Vorschau ist der Dialog
    so gut wie vorher, mit einer abgestürzten Prüfung wäre er unbrauchbar.
    """
    if tracker_preview is None:
        return reason
    try:
        block = tracker_preview.vorschau(command)
    except Exception:  # noqa: BLE001 – Darstellung darf die Entscheidung nie kippen
        return reason
    return f"{block}\n\n{reason}" if block else reason


# Ein echtes Hilfe-Argument: eigenständiges Token, nicht Teil eines längeren Wortes.
_HILFE_ARGUMENT = re.compile(r"(?:^|\s)(?:--help|-h)(?=\s|$)")

WRITE_ACCESS_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(werkzeug_aufruf("td") + r'\s+(?:add|set|remove)\b'),
        'td.py ändert docs/tech-debt.md – bei `Fällig: jetzt` zusätzlich den Prioritäten-Punkt '
        'in docs/AGENT_MEMORY.md.',
    ),
    (
        re.compile(werkzeug_aufruf("oq") + r'\s+(?:add|set|remove)\b'),
        'oq.py ändert docs/open-questions.md. Vor `remove` gehört das Ergebnis an einen '
        'stabilen Ort (ADR, Guideline, tech-debt.md).',
    ),
    (
        re.compile(werkzeug_aufruf("obs") + r'\s+(?:add|set)\b'),
        'obs.py schreibt nach docs/kaizen/observations.md.',
    ),
    (
        re.compile(werkzeug_aufruf("lessons") + r'\s+add\b'),
        'lessons.py schreibt nach docs/kaizen/lessons_learned.md.',
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
    # Update-Abfragen der monatlichen Abhängigkeits-Durchsicht (dev-workflow.md) – lesend.
    # Nur mit --outdated/--vulnerable: Die schreibenden Nachbarn (dotnet add package,
    # dotnet tool install|update) bleiben deny, die Abhängigkeiten ändert der User.
    (
        re.compile(r'^dotnet\s+list\s+(?:\S+\s+)?package\s+(?:.*\s)?--(?:outdated|vulnerable)\b'),
        None,
        'dotnet list [<projekt>] package --outdated|--vulnerable',
    ),
    (
        re.compile(r'^dotnet\s+tool\s+search\s+\S'),
        None,
        'dotnet tool search <id>',
    ),
    # Python-Werkzeuge aus requirements-dev.txt; `pip install` bleibt deny wie oben.
    (
        re.compile(r'^\.venv/bin/pip\s+list\s+(?:.*\s)?--outdated\b'),
        None,
        '.venv/bin/pip list --outdated',
    ),
    # Toolchain-Stand für die Abhängigkeits-Durchsicht. Nur das nackte `--version`: Schon
    # ein weiteres Argument (`node -e`, `python3 -c`) führte Code aus.
    (
        re.compile(r'^(?:dotnet|node|npm|python3|docker)\s+--version$'),
        None,
        'dotnet|node|npm|python3|docker --version',
    ),
    # Mods (.claude/mods/): validate liest nur, test läuft die Mod-Tests ohne Session.
    # Installieren und Einstellungen ändern bleibt beim User.
    (
        re.compile(r'^claude\s+plugin\s+(?:validate|test)\s+\S'),
        None,
        'claude plugin validate|test <ordner>',
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
    # python3 -m pytest auf tests/ (die Suite des Prozess-Codes)
    (
        re.compile(r'^python3\s+-m\s+pytest\s+tests/'),
        None,
        'python3 -m pytest tests/[<test_script>.py]',
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
    # Wie tr/cut: formen stdin um und schreiben nach stdout (S130, OBS-S127-2 – blockten je einzeln).
    (re.compile(r'^fold\b'), 'Shell', 'fold'),
    (re.compile(r'^rev\b'), 'Shell', 'rev'),
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
    # Eigenständige Runner der Werkzeug-Suite. `pytest tests/` deckt sie über einen
    # Wrapper-Test mit ab; für die Fehleranalyse braucht es den Direktstart, auf den die
    # Fehlermeldung selbst verweist.
    (
        re.compile(r'^python3\s+(?!-)tests/\S+\.py'),
        None,
        'python3 tests/<runner>.py',
    ),
    # Prozess-Code als Paket. Module dort nutzen relative Importe und laufen deshalb nur mit
    # `-m` – als Datei gestartet fehlt ihnen der Paketkontext.
    (
        re.compile(r'^python3\s+-m\s+prozesscode\.[\w.-]+'),
        None,
        'python3 -m prozesscode.<modul>  (Prozess-Code als Paket)',
    ),
    # Kein Allow-Pattern für Scratchpad-Scripte (S130, OBS-S127-2): Ein Python-Script führt
    # beliebigen Code aus und umgeht damit genau die Prüfung, für die dieser Hook existiert –
    # der Ablageort ändert daran nichts. Bis S130 war `python3 <scratchpad>/x.py` erlaubt,
    # während `python3 - <<EOF` blockte; das war keine Sicherheitsgrenze, sondern ein Umweg
    # um dieselbe. Wegwerf-Auswertungen laufen weiter, brauchen aber `# --allow-once`.
    # Das ABLEGEN im Scratchpad bleibt frei (SAFE_REDIRECT_PREFIXES) – nur das Ausführen nicht.
    # Globales recall-session-Script (read-only Session-Log-Analyse, liegt unter
    # ~/.claude/skills/ außerhalb des Repos). Absoluter Pfad ist hier erlaubt –
    # die WRONG_APPROACH-Regel für absolute python3-Pfade nimmt es explizit aus.
    # Per-Segment-Check bleibt: in Compounds wird jeder andere Teil weiter geprüft.
    (
        re.compile(r'^python3\s+\S*\.claude/skills/recall-session/scripts/recall\.py\b'),
        None,
        'python3 ~/.claude/skills/recall-session/scripts/recall.py <befehl>  (read-only Session-Log-Analyse)',
    ),
    # `git config --get…` liest einen Wert (auch --get-all/--get-regexp). Ohne `--get` schreibt
    # der Befehl die Konfiguration und bleibt deny – deshalb ein eigenes Muster statt eines
    # weiteren Subcommands in der Liste darunter (S130, OBS-S127-2).
    (
        re.compile(r'^git\s+(?:-C\s+\S+\s+)?config\s+--get\b'),
        None,
        'git [-C <pfad>] config --get <key>  (lesend; ohne --get schreibt git config)',
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
# Auditoren: nur lesend
# Reviewt wird vor dem Commit – was ein Auditor im Arbeitsbaum ändert, trifft Arbeit, die git
# noch nicht sichert. Für Auditoren ist Bash der einzige Schreibweg (kein Edit/Write), deshalb
# muss ein Befehl zusätzlich zu ALLOW_PATTERNS eines dieser Muster treffen. Die Gruppen der
# Allow-Liste taugen dafür nicht: „Lesen" und „Shell" sind Anzeigegruppen für --list und
# enthalten Schreiber (`awk '{print > "f"}'`, `sort -o`, `sed 'w f'`, `find -fprint`).
# Grenze: Erkannt wird, wer `agent_type` mitbringt und in AUDITOREN steht – ein umbenannter
# Auditor liefe mit vollen Rechten (abgesichert durch einen Abgleich mit .claude/agents/), ein
# mit `name` gestarteter ebenso: Dann steht dort der Name (abgesichert durch check-agent-start).
# `pytest` führt Testcode aus; was der schreibt, liegt in tmp_path, nicht im Arbeitsbaum.
# ---------------------------------------------------------------------------
AUDITOREN = frozenset({
    "code-quality-auditor", "functional-correctness-auditor", "security-auditor",
    "test-quality-auditor", "ux-ui-auditor", "workflow-auditor",
})
# Das Paket-Muster der Allow-Liste erlaubt jedes Modul, auch solche, die ohne Rückfrage
# schreiben (`obs-archive`). Die schreibenden Unterbefehle der Tracker-Werkzeuge fängt
# WRITE_ACCESS ab. Nicht dabei: `dotnet-test` – parallel laufende Auditoren teilten sich die
# Build-Ausgabe – und die Mutationsläufe mit ihrem Run-Lock.
_LESENDE_MODULE = frozenset({
    "doc", "anchors", "decisions", "test-inventory", "tracker", "ordinale",
    "obs", "td", "oq", "lessons", "ruff-run", "eslint-run", "vitest-run",
})
_GIT = r'^git\s+(?:-C\s+\S+\s+)?'
AUDITOR_PATTERNS: list[re.Pattern[str]] = [
    # Befehle ohne jede Option, die eine Datei schreibt.
    re.compile(r'^(?:ls|cat|head|tail|wc|grep|stat|file|diff|echo|printf|test|\[|cd|pwd|date|'
               r'which|tr|cut|rev|fold|dirname|basename|realpath|jq|xargs)(?=\s|$)'),
    re.compile(r'^sort\b(?!.*(?:\s-[a-zA-Z]*o|\s--output))'),
    re.compile(r'^uniq(?:\s+-\S+)*$'),                      # `uniq ein aus` schriebe `aus`
    re.compile(r"^sed\s+-n\s+'(?:\d+|\$)(?:,(?:\d+|\$))?p'(?:\s|$)"),  # nur Zeilenbereich drucken
    re.compile(r'^find\b(?!.*\s-(?:delete|exec|execdir|ok|okdir|fprint|fprint0|fprintf|fls)\b)'),
    re.compile(_GIT + r'(?:status|log|diff|show|rev-parse|ls-files|shortlog|check-ignore)\b'
               r'(?!.*\s--output\b)'),
    re.compile(_GIT + r'branch(?:\s+(?:-a|-r|-v|-vv|--all|--remotes|--list|--show-current))*\s*$'),
    re.compile(_GIT + r'tag(?:\s+(?:-l|--list)(?:\s+\S+)?)?\s*$'),
    re.compile(_GIT + r'remote(?:\s+-v)?\s*$'),
    re.compile(_GIT + r'config\s+--get\b'),
    re.compile(r'^python3\s+-m\s+pytest\s+tests/'),
    re.compile(r'^python3\s+(?!-)tests/\S+\.py'),
    re.compile(r'^python3\s+\S*\.claude/skills/recall-session/scripts/recall\.py\b'),
    re.compile(r'^python3\s+-m\s+prozesscode\.(?:'
               + '|'.join(re.escape(m) for m in sorted(_LESENDE_MODULE))
               + r')(?=\s|$)(?!.*\s--fix\b)'),
]

_NUR_LESEND_DENY_REASON = (
    "Auditoren arbeiten nur lesend: Lesebefehle ohne schreibende Optionen (kein awk, kein sort -o, "
    "sed nur als `sed -n '10,20p' <datei>`), git lesend, pytest, die Test-Runner und die Lese-, "
    "Test- und Lint-Werkzeuge aus prozesscode (ohne --fix). Was Dateien, Index oder einen "
    "Tracker ändert, bleibt dem Orchestrator."
)
_NUR_LESEND_FOOTER = (
    "\n\nAls Auditor gibt es keine Freigabe per Marker. Was sich nur schreibend prüfen ließe, "
    "im Finding als offene Prüfung nennen."
)


def _fuer_auditoren(command: str) -> bool:
    return any(pattern.search(command) for pattern in AUDITOR_PATTERNS)


# ---------------------------------------------------------------------------
# Smart-Deny-Hints (für UNKNOWN-Fälle ohne passendes Pattern)
# ---------------------------------------------------------------------------
# Der Kern beider Deny-Texte, einmal formuliert (S130, OBS-S119-1): Ein Deny lenkte bis dahin
# direkt in ein Wegwerf-Script, ohne die Vorfrage zu stellen, ob überhaupt eines nötig ist.
# Genau ein Text erreicht den Agenten – der Smart-Hint ODER `_NO_HINT_MESSAGE` –, deshalb eine
# geteilte Konstante statt zweier Fassungen, die auseinanderlaufen.
_WERKZEUGFRAGE = (
    "Erst die Werkzeugfrage – ein Deny heißt nicht, dass ein Script fällig ist:\n"
    "  Datei ändern → Edit · Abschnitt lesen → Read / doc.py get\n"
    "  suchen → grep / find (erlaubt; Muster mit ` oder $( in '…') · Tracker/Doku →\n"
    "  prozesscode-Werkzeug (tracker zeigt welches)\n"
    "Ein eigenes Script lohnt nur, wenn es effizienter oder weniger fehleranfällig ist als\n"
    "diese Werkzeuge – nicht deshalb, weil Bash gerade geblockt hat. Oft ist es das\n"
    "riskantere Werkzeug: Ein Edit-Mismatch schlägt fehl, blindes Slicing schneidet still.\n"
    "\n"
    "Bleibt es echte Ad-hoc-Logik: ins Scratchpad schreiben, dann ausführen mit\n"
    "  python3 <scratchpad>/foo.py " + ONE_TIME_MARKER + "\n"
    "Auch das Ausführen ist freigabepflichtig – ein Script führt beliebigen Code aus und\n"
    "umginge sonst genau diese Prüfung."
)
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
    # `python3 -c` und `python3 - <<EOF` sind derselbe Fall: beliebiger Code über die
    # Kommandozeile bzw. stdin. Der Heredoc-Body ist zwar lesbar, aber der Hook prüft ihn
    # nicht – ausgeführt wird er trotzdem (S130, OBS-S127-2). Die stdin-Form ist die
    # häufigste geblockte Klasse; ohne eigenes Muster fiele sie auf den generischen Text.
    (
        re.compile(r'^python3\s+(?:-c\b|-\s*(?:<<|$))'),
        "python3 -c / python3 - führt beliebigen Code aus – daran ändert der Heredoc nichts:\n"
        "Der Body ist lesbar, geprüft wird er nicht.\n"
        "\n" + _WERKZEUGFRAGE,
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
    "   Alle erlaubten Patterns: python3 -m prozesscode.hooks.check-bash-permission --list\n"
    "Nicht kreativ umgehen – jedes Deny hat einen Grund."
)

_NO_HINT_MESSAGE = (
    "Befehl nicht auf der Allow-Liste. Erlaubte Befehle + Alternativen ansehen:\n"
    "  python3 -m prozesscode.hooks.check-bash-permission --list\n"
    "\n"
    + _WERKZEUGFRAGE + "\n"
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
    "  python3 -m prozesscode.dotnet-test  /  python3 -m prozesscode.dotnet-stryker"
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

    Der Konsument bleibt geprüft: Ausgeblendet werden nur der Operator und der Body, der Rest
    der Operatorzeile bleibt stehen. Von `cat <<'EOF' | bash` bleibt `cat  | bash`, von
    `python3 - <<'EOF'` bleibt `python3 -` – ohne Allow-Muster. Ein Heredoc erkauft keine
    Freigabe.

    Nur gequotete Heredocs (`<<'EOF'`, `<<"EOF"`) sind reiner Text. Einer ohne Quote führt
    `$(…)` im Body aus; `check_command` lehnt ihn vorher ab, hier bleibt sein Body stehen.

    Fail-closed bei fehlendem Endmarker: Rest bleibt stehen und wird geprüft.

    Eine Klammer – `$(…)` oder `(…)` – hebt die umgebenden Anführungszeichen auf: In
    `git commit -m "$(cat <<'EOF' … EOF)"` ist der Heredoc echt. Der Stapel merkt sich
    je offener Klammer, ob sie in "…" begann, und stellt das bei `)` wieder her. Eine
    überzählige `)` (etwa ein case-Muster) schließt zu früh – dann wird weniger
    ausgeblendet. Eine überzählige `(` ist nicht abgesichert: Sie kann nur in einem
    Heredoc-Text stehen, dessen Endmarker hier nicht erkannt wird (`<<"$VAR"`).
    """
    in_single = in_double = False
    quote_stack: list[bool] = []
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
        if not in_single and command.startswith('$(', i):
            quote_stack.append(in_double)
            in_double = False
            i += 2
            continue
        if in_single or in_double:
            i += 1
            continue
        if c == '(':
            quote_stack.append(False)
            i += 1
            continue
        if c == ')' and quote_stack:
            in_double = quote_stack.pop()
            i += 1
            continue

        # Ab hier: außerhalb von Quotes. `<<<` ist ein Here-String (einzeiliger Wert, kein
        # Body) – als Ganzes überspringen: Ab seinem zweiten `<` stünde sonst `<< 'E'` da,
        # und die Zeilen danach verschwänden als vermeintlicher Body aus der Prüfung.
        if command.startswith('<<<', i):
            i += 3
            continue
        if command.startswith('<<', i):
            m = re.match(r"<<-?\s*(['\"]?)(\w+)\1", command[i:])
            if not m or not m.group(1):
                i += 2  # ungequotet: Body ist Code, bleibt stehen (fail-closed)
                continue
            marker = m.group(2)
            body_start = command.find('\n', i)
            if body_start == -1:
                # Heredoc angekündigt, aber kein Body: nur den Operator entfernen – der Rest
                # der Zeile (`| bash; rm …`) bleibt geprüft
                command = command[:i] + command[i + m.end():]
                continue
            # Endmarker: eigene Zeile, nur der Marker (bei <<- mit führendem Whitespace)
            end_re = re.compile(r'^[ \t]*' + re.escape(marker) + r'[ \t]*$', re.M)
            end = end_re.search(command, body_start)
            if not end:
                i += 2  # fail-closed: Body bleibt stehen und wird geprüft
                continue
            # Operator und Body herausschneiden; der Rest der Operatorzeile bleibt geprüft
            command = command[:i] + command[i + m.end():body_start] + command[end.end():]
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


def _woertliche_bereiche(text: str) -> list[tuple[int, int]]:
    """Positionen, an denen Bash `…` und $(…) NICHT ausführt: in '…' und nach einem `\\`.

    Ohne diese Unterscheidung galt eine Suche nach Markdown-Code wie grep '`tdd`' als
    Ausführung des Befehls `tdd` und wurde abgelehnt. Ein ' in "…" öffnet nichts.
    """
    bereiche: list[tuple[int, int]] = []
    in_double = False
    i = 0
    while i < len(text):
        zeichen = text[i]
        if zeichen == '\\':
            bereiche.append((i, i + 2))
            i += 2
            continue
        if zeichen == '"':
            in_double = not in_double
        elif zeichen == "'" and not in_double:
            ende = text.find("'", i + 1)
            ende = len(text) if ende == -1 else ende
            bereiche.append((i, ende + 1))
            i = ende
        i += 1
    return bereiche


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
        woertlich = _woertliche_bereiche(text)

        def repl(m: re.Match[str]) -> str:
            if any(start <= m.start() < ende for start, ende in woertlich):
                return m.group(0)
            inner = next(g for g in m.groups() if g is not None)  # genau eine Alternative trifft
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
        stripped = _ASSIGN_PREFIX_RE.sub('', segment)  # `^`-verankert: höchstens ein Treffer
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

        # Ab hier: definitiv außerhalb von Quotes. `||` trennt wie zwei `|` – das leere
        # Stück dazwischen verwirft flush().
        if c == '|':
            flush()
            i += 1
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

def check_simple_command(command: str, in_loop: bool = False,
                         nur_lesend: bool = False) -> tuple[str, str, str]:
    """Prüft ein einzelnes Segment: INDIRECT → ALLOW → DESTRUCTIVE → deny.

    WRONG_APPROACH wird nicht geprüft – das übernimmt check_command auf dem
    Gesamtbefehl vor dem Split.

    in_loop: Kommando aus einem Schleifenrumpf oder aus `-exec`/`xargs`. Dort sind
    Dateiverwaltungs-Befehle gesperrt – `rm` ist einzeln erlaubt, wiederholt ergibt
    es ein `rm -rf`, und die Wiederholungszahl ist zur Prüfzeit unsichtbar.
    nur_lesend: Aufruf eines Auditors – zusätzlich muss ein AUDITOR_PATTERNS-Muster passen.

    Gibt (decision, reason, log_type) zurück. decision: 'allow' | 'deny'.
    """
    if _INDIRECT_EXEC_RE.search(command):
        return ("deny", _INDIRECT_EXEC_DENY_REASON, "INDIRECT_EXEC")

    for pattern, category, _ in ALLOW_PATTERNS:
        if pattern.search(command):
            if nur_lesend and not _fuer_auditoren(command):
                return ("deny", _NUR_LESEND_DENY_REASON, "NUR_LESEND")
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


def check_command(command: str, nur_lesend: bool = False) -> tuple[str, str, str]:
    """Prüft einen Befehl und gibt (decision, reason, log_type) zurück.

    nur_lesend: Aufruf eines Auditors (AUDITOREN). Jede Rückfrage wird dann zum Deny mit
    log_type `NUR_LESEND_<bisheriger Typ>` – an dieser einen Stelle, damit kein künftiger
    ask-Pfad sie umgeht.

    decision: 'allow' | 'deny' | 'ask' (für Auditoren nie 'ask')
    """
    decision, reason, log_type = _entscheide(command, nur_lesend)
    if nur_lesend and decision == "ask":
        return ("deny", _NUR_LESEND_DENY_REASON, f"NUR_LESEND_{log_type}")
    return (decision, reason, log_type)


def _entscheide(command: str, nur_lesend: bool) -> tuple[str, str, str]:
    """Die eigentliche Prüfung hinter check_command.

    Reihenfolge (die Namen stehen so auch an den Stellen im Körper – bewusst keine Nummern:
    zwei Nummerierungen derselben Abfolge liefen bereits auseinander, der Docstring kannte
    fünf Schritte, der Körper acht, inklusive der Einschübe `2b`/`3b`/`4a`/`4b`):
      Einmal-Marker      → nackten Befehl klassifizieren (erlaubt → allow+Hinweis, sonst ask+Grund)
      Pfad-Normalisierung  absolute Repo-Pfade → relativ
      Quoting-Grenzen    → deny bei ungequotetem Heredoc und $'…'
      Heredoc-Ausblendung  Bodies sind Daten, kein Code
      Wrapper + Heredoc  → deny, wenn ein Wrapper-Filter umzuschreiben wäre
      WRONG_APPROACH     → deny, auf dem Gesamtbefehl vor dem Split
      Wrapper-Filter     → deny, wo ein Rewrite raten müsste (_bewerte_wrapper)
      Zugriffs-Scripte   → ask, vor dem Segment-Check
      Compound-Split     → Segmente bilden
      Verzeichniswechsel   npm-Sonderfall, braucht die Segmente
      Segment-Prüfung    → check_simple_command je Segment

    decision: 'allow' | 'deny' | 'ask'
    """
    # Einmal-Marker (# --allow-once): nicht blind fragen, sondern den NACKTEN Befehl klassifizieren.
    #    - wäre er ohnehin erlaubt → Marker war unnötig: direkt erlauben + Agent-Hinweis (kein Prompt).
    #    - wäre er deny            → legitimer Einzelfall: ask, und der Deny-Grund/die Gefahr wird dem
    #      User am Freigabe-Prompt als Reason mitgegeben (statt eines kontextlosen „erlauben?").
    if ONE_TIME_MARKER in command:
        bare = command.replace(ONE_TIME_MARKER, "").strip()
        decision, reason, _ = _entscheide(bare, nur_lesend)  # bare hat keinen Marker → terminiert
        if decision == "allow":
            return ("allow", _ONE_TIME_UNNEEDED_HINT, "ONE_TIME_UNNEEDED")
        return ("ask", reason, "ONE_TIME")

    # Pfad-Normalisierung: absolute Repo-Pfade → relativ, dann auf dem
    #    normalisierten Befehl weiterprüfen (so wird z.B. python3 <absoluter Pfad>
    #    zu python3 .claude/... und matcht die Allow-Liste statt WRONG_APPROACH).
    command, _ = normalize_repo_paths(command)

    # Quoting, das die Zerlegung nicht sicher liest: ablehnen statt auszuwerten. Beides
    #     kam im Bestand nicht vor; der Ausweg kostet nichts.
    maskiert = _maskiere_strings(command)
    if _UNGEQUOTETER_HEREDOC_RE.search(maskiert):
        return ("deny", _UNGEQUOTETER_HEREDOC_REASON, "UNSUPPORTED_QUOTING")
    if "$'" in maskiert:
        return ("deny", _ANSI_C_QUOTE_REASON, "UNSUPPORTED_QUOTING")

    # Heredoc-Ausblendung: Bodies sind Daten, kein Code (OBS-S111-4) – vor jeder weiteren
    #     Analyse entfernen, sonst wird Fließtext als Befehlsfolge gelesen.
    mit_heredoc = command
    command = strip_heredoc_bodies(command)

    # Wrapper mit Filter UND Heredoc: Geprüft würde die Fassung ohne Body, umgeschrieben
    #     (_build_allow_output) das Original – zwei Fassungen, eine Entscheidung. Kam im Bestand
    #     nicht vor; ablehnen statt beide abzugleichen.
    if command != mit_heredoc and strip_wrapper_filter(command)[1]:
        return ("deny", _INDIRECT_FILTER_REASON.format(erkannt=_GRUND_HEREDOC), "INDIRECT_WRAPPER_FILTER")

    # WRONG_APPROACH auf Gesamtbefehl (ohne ^-Anker → matcht auch in Subshells).
    #    String-Argumente nicht-ausführender Befehle werden dabei maskiert: eine
    #    ERWÄHNUNG ist keine Ausführung (OBS-S111-4).
    for pattern, reason in WRONG_APPROACH_PATTERNS:
        if pattern.search(mask_data_strings(command)):
            return ("deny", reason, "WRONG_APPROACH")

    # Wrapper-Ausgabe auf einem Umweg gefiltert: ablehnen statt umschreiben – welcher Teil
    #    ohne Filter gemeint war, lässt sich nicht sicher erraten (strip_wrapper_filter).
    ablehnung = wrapper_filter_ablehnung(command)
    if ablehnung:
        return ("deny", ablehnung, "INDIRECT_WRAPPER_FILTER")

    # Zugriffs-Scripte (schreibend) → ask. Muss VOR dem Segment-Check liegen, sonst greift
    #     das generische Allow-Muster für `prozesscode/<script>.py` und der Text ginge
    #     ohne Freigabe durch. Der Grund trägt zusätzlich eine lesbare Vorschau des Eintrags
    #     (OBS-S116-1) – ohne sie steht im Dialog nur die Kommandozeile.
    # `--help` druckt die Doku und schreibt nichts (S124, User-Meldung). Geprüft wird auf der
    #     maskierten Fassung: `--titel "Warum --help nervt"` ist ein Eintragstext, kein
    #     Hilfeaufruf. Wer für Doku eine Freigabe klicken muss, liest die Doku seltener.
    if not _HILFE_ARGUMENT.search(mask_data_strings(command)):
        for pattern, reason in WRITE_ACCESS_PATTERNS:
            if pattern.search(command):
                return ("ask", _mit_vorschau(command, reason), "WRITE_ACCESS")

    # Compound-Split + Segment-Check (check_simple_command ohne WRONG_APPROACH)
    segments = split_compound_command(command)
    is_compound = len(segments) > 1

    # Verzeichniswechsel vor npm (OBS-S091-2): braucht die Segmente, deshalb erst hier
    #     und nicht als WRONG_APPROACH-Regex auf dem Gesamtbefehl.
    if cd_npm_conflict(segments):
        return ("deny", _CD_NPM_HINT, "WRONG_APPROACH")

    # Segment-Prüfung: jedes Segment in die tatsächlich ausgeführten Kommandos zerlegen und einzeln
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
                cmd, in_loop=loop_depth > 0 or is_mass, nur_lesend=nur_lesend)
            if decision == "deny":
                if is_compound:
                    log_type = f"COMPOUND_{log_type}"
                return ("deny", reason, log_type)

        # Ohne das führende Strukturwort: Eine innere Schleife steht im Segment `do for …`.
        if _LOOP_OPEN_RE.match(_LEADING_STRUCT_RE.sub('', bare)):
            loop_depth += 1

    # Kein einziges prüfbares Kommando (leerer Befehl, nur Struktur/Zuweisung) →
    # nicht durchwinken. Fail-closed: was wir nicht klassifizieren, erlauben wir nicht.
    if not checked_any:
        return ("deny", _get_smart_hint(command), "UNKNOWN")

    return ("allow", _ALLOW_REASON, "ALLOW")


def _build_deny_message(reason: str, nur_lesend: bool = False) -> str:
    """Baut die vollständige Deny-Nachricht für den Agenten."""
    # Für Auditoren nie der ursprüngliche Grund: Die Hinweistexte empfehlen `# --allow-once`
    # oder Wrapper, die ihnen gesperrt sind.
    if nur_lesend:
        return _NUR_LESEND_DENY_REASON + _NUR_LESEND_FOOTER
    if reason:
        return reason + _ALLOW_ONCE_WITH_HINT_FOOTER
    return _NO_HINT_MESSAGE


# Projekt-Tasks, die NIE direkt laufen (Tests/Lint/Mutation) → immer via Wrapper-Script.
# Die direkten Befehle (dotnet test, npm run test, npx …) sind WRONG_APPROACH → deny.
# Hier nur für --list, damit der korrekte Weg PROAKTIV sichtbar ist (sonst lernt der Agent
# ihn erst nach einem unnötigen Deny). Bei Script-Umbenennung hier + WRONG_APPROACH_PATTERNS syncen.
_PROJECT_TASK_SCRIPTS: list[str] = [
    "Backend-Tests:       python3 -m prozesscode.dotnet-test [--filter X] [--verbose]",
    "Backend-Mutation:    python3 -m prozesscode.dotnet-stryker [--mutate Domain/Foo.cs] [--verbose]",
    "Frontend-Unit-Tests: python3 -m prozesscode.vitest-run [--filter X] [--verbose]",
    "Frontend-E2E:        python3 -m prozesscode.playwright-test [--filter X] [--verbose]",
    "Frontend-Mutation:   python3 -m prozesscode.stryker-frontend [--mutate src/..] [--verbose]",
    "ESLint:              python3 -m prozesscode.eslint-run [--verbose]",
    "Python-Linter:       python3 -m prozesscode.ruff-run [--fix] [--verbose]",
    "Python-Coverage:     python3 -m prozesscode.coverage-run [--verbose]  (Metrik, kein Gate)",
    "Python-Mutation:     python3 -m prozesscode.mutmut-run --mutate prozesscode.anchors "
    "[--ratchet]  (Sichtung, kein Gate)",
    "Duplikate (jscpd):   python3 -m prozesscode.jscpd-run [--verbose]",
]

# Lesewege, die einen Ausschnitt liefern statt der ganzen Datei. Anders als oben ist der
# Direktaufruf hier nicht geblockt – ein `Read` auf die Volldatei bleibt erlaubt und ist
# manchmal richtig. Sie stehen trotzdem hier, weil genau das die Wirksamkeitsfrage ist:
# `docs/guidelines` und `docs/process` sind zusammen 20,4 % des Read-Volumens bei 6 %
# gezielten Zugriffen (OBS-S114-2), und eine Anleitung, die nur in AGENTS.md steht, erreicht
# einen kalt gestarteten Subagenten nicht. Gegenbeleg im selben Datensatz: `docs/history`
# liegt bei 72 % gezielt – dort war der Abrufweg schon da.
_TARGETED_READ_SCRIPTS: list[str] = [
    "Doku-Abschnitt:  python3 -m prozesscode.doc toc <datei> | get <ANKER>",
    "ADR:             python3 -m prozesscode.decisions list --tag X | get <ID>",
    "Testdatei:       python3 -m prozesscode.test-inventory <datei>",
    "Tracker-Eintrag: python3 -m prozesscode.tracker  (zeigt, welches Werkzeug welchen pflegt)",
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


_LISTE_EINLEITUNG = (
    "Diese Liste regelt das Bash-Tool. Befehle die hier nicht passen, werden vom\n"
    "PreToolUse-Hook automatisch geblockt (deny) – nicht nur \"unerwünscht\", sondern\n"
    "hart blockiert. '# --allow-once' anhängen erzwingt eine einmalige User-Freigabe\n"
    "(nur für echte Einzelfälle ohne regulären Weg).\n"
    "Tool-Vorrang: für Datei-Lesen/-Ändern sind Read/Edit meist besser als cat/sed.\n"
    "Gesucht wird per Bash mit grep / find – die Werkzeuge Grep und Glob fehlen unter\n"
    "Linux/WSL jeder Session mit Bash.\n"
)
_KOPF_TASKS = "Häufige Projekt-Tasks – immer via Wrapper-Script (Direktaufruf wird geblockt):"
_KOPF_LESEN = "Gezielt lesen statt Volldatei (Volldatei nur, wenn du fast alles brauchst):"
_KOPF_ERLAUBT = "Erlaubte Befehle (Allow-Liste):"
_ZUSAMMENSETZEN = (
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
_SCRATCHPAD_TEXT = (
    "Scratchpad (Wegwerf-Scripte, Zwischenergebnisse, Redirect-Ziel):\n"
    "  {pfad}/\n"
    "  Liegt außerhalb des Repos, verschwindet mit der Session – kein Aufräumen nötig.\n"
    "  Ablegen ist frei (Redirect, Write-Tool); .claude/tmp/ ist KEIN Schreibziel mehr.\n"
    "  AUSFÜHREN braucht eine Freigabe: python3 <scratchpad>/<name>.py {marker}\n"
    "  – ein Script führt beliebigen Code aus und umginge sonst diese Prüfung.\n"
    "  Vorher die Werkzeugfrage: Edit/Read, grep/find und die prozesscode-Werkzeuge\n"
    "  zuerst; ein Script lohnt nur, wenn es effizienter oder weniger fehleranfällig ist.\n"
)
_KOPF_SCHREIBEN = "Schreiben in Projektdokumente (User-Freigabe nötig, kein Marker):"
_SCHREIBEN_TEXT = (
    "  python3 -m prozesscode.obs add|set …       → docs/kaizen/observations.md\n"
    "  python3 -m prozesscode.lessons add …       → docs/kaizen/lessons_learned.md\n"
    "  python3 -m prozesscode.td add|set|remove … → docs/tech-debt.md (+ AGENT_MEMORY bei `jetzt`)\n"
    "  python3 -m prozesscode.oq add|set|remove … → docs/open-questions.md\n"
    "  Die Freigabe nennt Eintrag und Datei; die Änderung zeigt der Mod tracker-diff im Pane.\n"
    "  Überblick über alle Tracker: python3 -m prozesscode.tracker\n"
)
_KOPF_DESTRUKTIV = "Destruktive Befehle (nur mit # --allow-once, User-Freigabe nötig):"


def allow_list_text() -> str:
    """Die Allow-Liste als Text.

    Eine Quelle für zwei Abnehmer: das `--list`-Flag und den Session-Start-Block
    `bash-allowlist` (`session-agenda.py`), der sie als Funktion holt statt als
    Subprozess – ein Prozessstart weniger, und unter mutmut lädt ein Subprozess den
    instrumentierten Hook ohne dessen Laufzeit und reißt den Lauf mit.
    """
    zeilen: list[str] = []

    def schreib(text: str = "") -> None:
        zeilen.append(text)

    schreib(_LISTE_EINLEITUNG)

    schreib(_KOPF_TASKS)
    for line in _PROJECT_TASK_SCRIPTS:
        schreib(f"  {line}")
    schreib()
    schreib(_SCRIPT_USAGE_HINT)
    schreib()

    schreib(_KOPF_LESEN)
    for line in _TARGETED_READ_SCRIPTS:
        schreib(f"  {line}")
    schreib()

    schreib(_KOPF_ERLAUBT)

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
        schreib(line)

    if groups:
        schreib()
        for grp in sorted(groups, key=str.lower):
            items = sorted(groups[grp], key=str.lower)
            schreib(f"  [{grp}]")
            schreib(f"    {', '.join(items)}")

    schreib()
    schreib(_ZUSAMMENSETZEN)
    schreib()
    if _SCRATCHPAD:
        schreib(_SCRATCHPAD_TEXT.format(pfad=_SCRATCHPAD, marker=ONE_TIME_MARKER))
    schreib(_KOPF_SCHREIBEN)
    schreib(_SCHREIBEN_TEXT)
    schreib(_KOPF_DESTRUKTIV)
    for _pattern, _hint, label in sorted(
        ((pat, h, lb) for pat, h, lb in DESTRUCTIVE_PATTERNS if lb),
        key=lambda x: x[2].lower(),
    ):
        schreib(f"  {label}")

    return "\n".join(zeilen)


def _print_allow_list() -> None:
    """Gibt die Allow-Liste aus (--list-Flag)."""
    print(allow_list_text())


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
        # Nie in einem Befehl mit Heredoc: Dessen Text ist Daten, und Wrapper mit Filter
        # plus Heredoc lehnt check_command ohnehin ab.
        if strip_heredoc_bodies(rewritten) == rewritten:
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

    if inp.get("tool_name") != "Bash":
        sys.exit(0)

    command = inp.get("tool_input", {}).get("command")
    if not command:
        sys.exit(0)

    # Claude Code nennt bei Subagent-Aufrufen den Typ in `agent_type`, bei einem mit `name`
    # gestarteten allerdings den Namen – s. Grenze bei AUDITOREN.
    nur_lesend = inp.get("agent_type") in AUDITOREN
    decision, reason, log_type = check_command(command, nur_lesend)

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
            "permissionDecisionReason": _build_deny_message(reason, nur_lesend),
        }
    }))
    sys.exit(0)


if __name__ == "__main__":
    main()
