"""Holt `test-bash-permission.py` ins Tooling-Test-Gate.

Warum dieser Umweg: Die Permission-Regeln sind der Mechanismus, der jeden anderen Gate-
Bypass verhindert – aber ihre Suite bringt einen eigenen Runner mit und heißt
`test-bash-permission.py`, mit Bindestrichen. pytest sammelt nur `test_*.py`, das Gate
(`checks/tooling_tests.py`) fährt also an ihr vorbei. Eine gebrochene Regel wurde damit von
keinem Gate bemerkt; in S115 fiel das bei einer Änderung an genau dieser Datei auf.

Gewählt wurde der Aufruf des vorhandenen `main()` statt einer Portierung der ~800 Zeilen auf
pytest: Die Portierung wäre eine große Umschreibung mit eigenem Regressionsrisiko an der
sicherheitsrelevantesten Stelle, während dieser Wrapper das Gate sofort schließt. Die
Ausgabe des Runners wird bei Rot vollständig durchgereicht, damit die Ursache sichtbar
bleibt und nicht auf „Exit-Code 1" zusammenschrumpft.

Bewusst **im selben Prozess**, nicht als Subprozess: Unter mutmut läuft die Suite gegen einen
instrumentierten Baum, und ein Subprozess lädt den mutierten Hook ohne die mutmut-Laufzeit –
der Lauf brach dort mit `'NoneType' object has no attribute 'max_stack_depth'` ab, noch bevor
ein einziger Mutant bewertet war. In-process gilt die Instrumentierung, und der Lauf misst
tatsächlich den geladenen Code.
"""
import importlib.util
import io
import os
import re
from contextlib import redirect_stdout

_RUNNER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test-bash-permission.py")

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _lade_runner():
    """Lädt den Runner als Modul – der Bindestrich im Dateinamen schließt `import` aus."""
    spec = importlib.util.spec_from_file_location("_bash_permission_runner", _RUNNER)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def test_bash_permission_suite_is_green():
    """Der eigene Runner muss grün sein – er ist die einzige Absicherung der Deny-Regeln."""
    runner = _lade_runner()
    puffer = io.StringIO()
    try:
        with redirect_stdout(puffer):
            runner.main()
    except SystemExit as ende:
        code = ende.code or 0
    else:
        code = 0

    if code:
        plain = _ANSI_RE.sub("", puffer.getvalue())
        failures = [line.strip() for line in plain.splitlines() if "FAIL" in line]
        detail = "\n".join(failures) if failures else plain[-2000:]
        raise AssertionError(
            "test-bash-permission.py ist rot (Permission-Regeln nicht abgesichert):\n"
            + detail
            + "\n  Vollständig: python3 tests/test-bash-permission.py"
        )


def test_runner_exists_where_the_gate_expects_it():
    """Wird der Runner umbenannt oder verschoben, muss dieser Wrapper mitgezogen werden –
    sonst wäre er still wirkungslos, also genau der Zustand, den er behebt."""
    assert os.path.isfile(_RUNNER), f"Runner fehlt: {_RUNNER}"
