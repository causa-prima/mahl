"""Der Aufrufpfad der Erfassungs-Scripte – nicht die Funktion dahinter (LL-S128-1).

Die Modul-Tests prüfen `add()`; ob die CLI das Pflichtfeld überhaupt verlangt, sehen sie nicht.
Aufgerufen wird bewusst OHNE Argumente: argparse bricht dann ab, bevor irgendetwas geschrieben
wird, und nennt alle fehlenden Pflichtargumente – ein Lauf kann die echten Tracker so nie
verändern, auch nicht in einer RED-Phase.
"""
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent


@pytest.mark.aufrufpfad("obs", "td", "oq")
@pytest.mark.parametrize("modul", ["obs", "td", "oq"])
def test_add_verlangt_den_aufschubgrund(modul):
    lauf = subprocess.run([sys.executable, "-m", f"prozesscode.{modul}", "add"],
                          cwd=REPO, capture_output=True, text=True, timeout=30)
    assert lauf.returncode == 2
    assert "--aufschubgrund" in lauf.stderr
