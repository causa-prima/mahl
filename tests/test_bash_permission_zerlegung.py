"""Wie der Bash-Guard einen Befehl zerlegt, bevor er ihn prüft – Randfälle der Parser.

Jede Zerlegung entscheidet, **was** geprüft wird: Ein Escape, das der Splitter übersieht,
macht aus einem Argument einen zweiten Befehl (oder umgekehrt); ein Heredoc, der zu viel
ausblendet, versteckt den Konsumenten. Der Runner `test-bash-permission.py` prüft die
Entscheidungen; hier stehen die Ränder, an denen eine Zerlegung um ein Zeichen danebenliegt –
Backslash am Ende, Quote direkt hinter einem Operator, zwei Konstrukte hintereinander.

Erwartet wird jeweils das ganze Ergebnis, nicht ein Teil davon: Ein um eine Stelle
verschobener Bereich ist genau der Fehler, den diese Datei finden soll.
"""
import os
from importlib import import_module

import pytest

os.environ.setdefault("CLAUDE_CODE_SESSION_ID", "test-session-0000")
hook = import_module("prozesscode.hooks.check-bash-permission")

_WRAPPER = "python3 -m prozesscode.vitest-run"


# --- Heredoc-Ausblendung --------------------------------------------------------
@pytest.mark.parametrize("befehl, rest", [
    # Quotes vor dem Operator schließen sauber – auch direkt am Anfang und direkt davor.
    ("'a' <<'E'\nb\nE", "'a' "),
    ("echo 'a' <<'E'\nx\nE", "echo 'a' "),
    ("echo ''<<'E'\nx\nE", "echo ''"),
    # Ein Quote-Zeichen der jeweils anderen Art öffnet nichts.
    ("echo \"a'b\" <<'E'\nx\nE", "echo \"a'b\" "),
    ("echo 'a\"b' <<'E'\nx\nE", "echo 'a\"b' "),
    # Maskiert öffnet ein Quote nichts; das maskierte Zeichen zählt nicht doppelt.
    ("echo \\\"<<'E'\nx\nE", "echo \\\""),
    ("echo \\a<<'E'\nx\nE", "echo \\a"),
    # Klammern: `$(` hebt das umgebende "…" auf, `)` stellt es wieder her.
    ("echo $(<<'E'\nx\nE\n)", "echo $(\n)"),
    ("echo \"$(ls)\"<<'E'\nx\nE", "echo \"$(ls)\""),
    # Text zwischen Marker und Zeilenende ist Befehl: bleibt, auch wenn davor eine Zeile steht.
    ("echo a\ncat <<'E' | wc\nx\nE", "echo a\ncat  | wc"),
    # Ohne Body: nur der Operator geht – und es geht danach weiter.
    ("cat <<'E' | bash", "cat  | bash"),
    ("cat <<'E'; cat <<'F'", "cat ; cat "),
    # Der Endmarker wird erst hinter dem Operator gesucht.
    ("E\ncat <<'E'\nx\nE", "E\ncat "),
    # Ohne Endmarker bleibt der Body (fail-closed); ein späterer Heredoc wird trotzdem erkannt.
    ("cat <<'E' <<'F'\nx\nF", "cat <<'E' "),
    # Ein Here-String davor zählt als Ganzes – auch am Anfang und direkt vor einem Quote.
    ("cat <<<'a' <<'E'\nx\nE", "cat <<<'a' "),
    ("<<<'a' cat <<'E'\nx\nE", "<<<'a' cat "),
    # Zwei Heredocs hintereinander.
    ("cat <<'E'\nx\nE\ncat <<'F'\ny\nF", "cat \ncat "),
    # Ein ungequoteter Marker in Quotes (`<<"$V"`) bleibt stehen, das Quoting danach stimmt.
    ("cat <<\"$V\"\nx\n$V\n; cat <<'F'\ny\nF", "cat <<\"$V\"\nx\n$V\n; cat "),
])
def test_heredoc_body_faellt_weg_der_rest_bleibt(befehl, rest):
    assert hook.strip_heredoc_bodies(befehl) == rest


@pytest.mark.parametrize("befehl", [
    "echo \"<<'E'\"\nx\nE",                 # in "…"
    "echo '<<\"E\"'\nx\nE",                 # in '…'
    "echo \"$(ls) <<'E'\nx\nE\"",           # nach `$(…)` wieder in "…"
    "(\"<<'E'\"\nb\nE\n)",                  # in "…" direkt hinter `(`
    "cat <<E\nx\nE",                        # ungequotet: Body ist Code
    "cat <<< 'E'",                          # Here-String, kein Heredoc
    "cat <<< 'E'\nx\nE",
])
def test_kein_heredoc_bleibt_unveraendert(befehl):
    assert hook.strip_heredoc_bodies(befehl) == befehl


def test_here_string_versteckt_keine_folgezeilen():
    """Las die Ausblendung `<<< 'E'` ab dem zweiten `<` als Heredoc, verschwand die Zeile
    danach aus der Prüfung – die Shell führt sie aber aus."""
    assert hook.check_command("cat <<< 'E'\nrm -rf x\nE")[0] == "deny"


# --- Compound-Split ---------------------------------------------------------------
@pytest.mark.parametrize("befehl, segmente", [
    ("echo a\\;b", ["echo a\\;b"]),         # maskierter Trenner trennt nicht
    ("echo \\;", ["echo \\;"]),             # … auch als vorletztes Zeichen
    ("echo a\\", ["echo a\\"]),             # Backslash am Ende
    ("a\\;;b", ["a\\;", "b"]),              # das Zeichen nach dem maskierten zählt wieder
    ("a|b", ["a", "b"]),
    ("a||b", ["a", "b"]),
    ("a|b|c", ["a", "b", "c"]),
    ("a |", ["a"]),
    ("a&&b", ["a", "b"]),
    ("a &&", ["a"]),
    ("  ", ["  "]),                         # nichts zu trennen: der Befehl selbst
])
def test_split_an_den_raendern(befehl, segmente):
    assert hook.split_compound_command(befehl) == segmente


# --- Output-Redirect ---------------------------------------------------------------
@pytest.mark.parametrize("befehl, unsicher", [
    (">datei", True),                       # gleich am Anfang
    ("echo a\\>b", False),                  # maskiert
    ("echo \\>>x", True),                   # nach dem maskierten `>` folgt ein echtes
    ("echo \\a > x", True),                 # nach einem Escape geht die Suche weiter
    ("echo a >>/dev/null", False),
    ("echo a >", True),                     # ohne Ziel
    ("echo a 2>&1 > x", True),              # nach dem FD-Redirect geht die Suche weiter
    ("echo a >/dev/null >x", True),         # nach einem sicheren Ziel ebenso
    ("echo a >\\dev\\null", False),         # Windows-Schreibweise des Ziels
])
def test_redirect_an_den_raendern(befehl, unsicher):
    assert hook.has_unsafe_output_redirect(befehl) is unsicher


# --- Maskierung für die Wrapper-Analyse ---------------------------------------------
@pytest.mark.parametrize("befehl, maskiert", [
    ("x \"$('a')\"", "x \"$('_')\""),       # String direkt hinter `$(`
    ("echo \"$(echo X) x\"", "echo \"$(echo X)__\""),
    ("echo \"abc\\", "echo \"____"),        # Backslash am Ende eines offenen Strings
    ("echo \"\\\"", "echo \"__"),           # maskiertes " beendet den String nicht
    ("a \\\n'b'", "a __'_'"),               # Zeilenfortsetzung, direkt danach ein String
    ("\\a'b'", "\\a'_'"),                   # Escape außerhalb, direkt danach ein String
])
def test_maskierung_an_den_raendern(befehl, maskiert):
    assert hook._maskiere_strings(befehl) == maskiert


# --- Wörtliche Bereiche (keine Substitution) -----------------------------------------
@pytest.mark.parametrize("text, bereiche", [
    ("'a' b", [(0, 3)]),
    ("'a' 'b'", [(0, 3), (4, 7)]),
    ("'' x", [(0, 2)]),
    ("a 'b", [(2, 5)]),                     # offen bis zum Ende
    ("\\$(x) 'y'", [(0, 2), (6, 9)]),
    ("\\''a'", [(0, 2), (2, 5)]),
    ("\\a 'b'", [(0, 2), (3, 6)]),
    ("\"'\" 'a'", [(4, 7)]),                # ' in "…" öffnet nichts
])
def test_woertliche_bereiche(text, bereiche):
    assert hook._woertliche_bereiche(text) == bereiche


# --- Segment-Expansion -----------------------------------------------------------------
@pytest.mark.parametrize("segment, kommandos", [
    ("echo $(ls)", [("ls", False), ("echo WERT", False)]),
    ("grep '$(ls)' x", [("grep '$(ls)' x", False)]),
    # Direkt hinter einem wörtlichen Bereich wird wieder ausgeführt.
    ("echo 'a'$(rm -rf x)", [("rm -rf x", False), ("echo 'a'WERT", False)]),
])
def test_expansion_findet_was_ausgefuehrt_wird(segment, kommandos):
    assert hook.expand_segment(segment) == kommandos


@pytest.mark.parametrize("segment, getrennt", [
    ("find . -name x -exec cat {} \\;", ("find . -name x", "cat DATEI")),
    ("xargs -0 grep x {}", ("xargs -0", "grep x DATEI")),
])
def test_exec_argument_wird_abgetrennt(segment, getrennt):
    assert hook._split_exec_argument(segment) == getrennt


def test_datenstrings_werden_segmentweise_maskiert():
    assert hook.mask_data_strings('grep "npx vitest" x | wc -l') == "grep TEXT x ; wc -l"


# --- Verzeichniswechsel vor npm -----------------------------------------------------------
@pytest.mark.parametrize("segmente, konflikt", [
    (["cd .", "npm ci"], False),
    (["cd ./", "npm ci"], False),
    (["cd X", "npm ci"], True),
    (["cd ./X", "npm ci"], True),
    (["cd /", "npm ci"], True),             # Dateisystem-Wurzel, nicht Repo-Root
    ([f"cd {hook._NORMALIZE_ROOT}", "npm ci"], False),   # Repo-Root, absolut belassen
    ([f"cd {hook._NORMALIZE_ROOT}/", "npm ci"], False),
])
def test_cd_vor_npm(segmente, konflikt):
    assert hook.cd_npm_conflict(segmente) is konflikt


# --- Wrapper-Analyse ------------------------------------------------------------------------
@pytest.mark.parametrize("davor, umschliessung", [
    ("echo `", "`"),
    ("x $(", "("),
    ("{ ", "{"),
    ("head <(echo ", "<("),
    ("tee >(", ">("),
    ("( X ", "("),
    ("for f in a; do ", "block"),
    ("if true; then ", "block"),
    ("case x in a) ", "block"),
    ("if true; then x; fi; ", None),
    ("case x in a) y;; esac; ", None),
    ("echo X; ", None),
    ("", None),
])
def test_umschliessung(davor, umschliessung):
    assert hook._umschliessung(davor) == umschliessung


@pytest.mark.parametrize("stufen, urteil", [
    ([], "tee"),
    (["tee x"], "tee"),
    ([" grep x "], "filter"),
    (["wc -l"], "andere"),
    (["tee >(x)"], "andere"),
])
def test_stufen_urteil(stufen, urteil):
    assert hook._stufen_urteil(stufen) == urteil


@pytest.mark.parametrize("befehl, grund", [
    (f"echo x | tee >({_WRAPPER})", "_GRUND_PROZESS_SUBSTITUTION"),
    (f"{_WRAPPER} | wc -l", "_GRUND_STUFE"),
    (f"out=$({_WRAPPER}) | head", "_GRUND_WEITERGABE"),
])
def test_wrapper_ablehnung_nennt_den_grund(befehl, grund):
    assert hook.wrapper_filter_ablehnung(befehl) == hook._INDIRECT_FILTER_REASON.format(
        erkannt=getattr(hook, grund))


def test_wrapper_mit_filter_und_heredoc_nennt_den_heredoc():
    grund = hook.check_command(f"{_WRAPPER} <<'EOF' | tail -3\nx\nEOF")[1]
    assert grund == hook._INDIRECT_FILTER_REASON.format(erkannt=hook._GRUND_HEREDOC)


def test_filter_vor_dem_wrapper_bleibt_stehen():
    befehl = f"git log | head; {_WRAPPER} | tail -5"
    assert hook.strip_wrapper_filter(befehl) == (f"git log | head; {_WRAPPER}", True)
