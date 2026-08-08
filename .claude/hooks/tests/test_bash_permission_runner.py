"""Holt `test-bash-permission.py` ins Tooling-Test-Gate.

Warum dieser Umweg: Die Permission-Regeln sind der Mechanismus, der jeden anderen Gate-
Bypass verhindert – aber ihre Suite liegt als `.claude/hooks/test-bash-permission.py` mit
eigenem Runner neben `tests/`, und das Gate (`checks/tooling_tests.py`) fährt ausschließlich
`pytest .claude/hooks/tests/`. Eine gebrochene Regel wurde damit von keinem Gate bemerkt;
in S115 fiel das bei einer Änderung an genau dieser Datei auf.

Gewählt wurde der Subprozess-Aufruf statt einer Portierung der ~800 Zeilen auf pytest: Die
Portierung wäre eine große Umschreibung mit eigenem Regressionsrisiko an der
sicherheitsrelevantesten Stelle, während dieser Wrapper das Gate sofort schließt. Die
Ausgabe des Runners wird bei Rot vollständig durchgereicht, damit die Ursache sichtbar
bleibt und nicht auf „Exit-Code 1“ zusammenschrumpft.
"""
import os
import re
import subprocess
import sys

_HOOKS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_RUNNER = os.path.join(_HOOKS_DIR, "test-bash-permission.py")
_TIMEOUT_S = 60

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def test_bash_permission_suite_is_green():
    """Der eigene Runner muss grün sein – er ist die einzige Absicherung der Deny-Regeln."""
    proc = subprocess.run(
        [sys.executable, _RUNNER],
        capture_output=True, text=True, timeout=_TIMEOUT_S,
    )
    if proc.returncode != 0:
        plain = _ANSI_RE.sub("", proc.stdout + proc.stderr)
        failures = [line.strip() for line in plain.splitlines() if "FAIL" in line]
        detail = "\n".join(failures) if failures else plain[-2000:]
        raise AssertionError(
            "test-bash-permission.py ist rot (Permission-Regeln nicht abgesichert):\n"
            + detail
            + "\n  Vollständig: python3 .claude/hooks/test-bash-permission.py"
        )


def test_runner_exists_where_the_gate_expects_it():
    """Wird der Runner umbenannt oder verschoben, muss dieser Wrapper mitgezogen werden –
    sonst wäre er still wirkungslos, also genau der Zustand, den er behebt."""
    assert os.path.isfile(_RUNNER), f"Runner fehlt: {_RUNNER}"
