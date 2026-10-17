"""Die Mods unter `.claude/mods/` – ihre eigenen Tests und die statische Prüfung von Claude Code.

Mods sind JavaScript und haben kein eigenes Gate; ohne diese Anbindung liefen ihre Tests nur, wenn
jemand daran denkt. `claude plugin test` braucht weder Session noch Netz (rund eine Sekunde).
Ohne `claude` auf dem PATH wird übersprungen – dann fehlt die Laufzeit, gegen die geprüft würde.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

MODS = Path(__file__).resolve().parent.parent / ".claude" / "mods"
MOD_ORDNER = sorted(p.parent.parent for p in MODS.glob("*/.claude-plugin/plugin.json"))

pytestmark = pytest.mark.skipif(shutil.which("claude") is None, reason="claude nicht auf dem PATH")


def _claude(*argumente: str) -> subprocess.CompletedProcess:
    return subprocess.run(["claude", "plugin", *argumente], capture_output=True, text=True,
                          timeout=120)


def test_es_gibt_mods_zu_pruefen():
    """Gegenprobe zur Suche: Fände das Muster keinen Mod, liefen die Tests unten ins Leere."""
    assert MOD_ORDNER


@pytest.mark.parametrize("mod", MOD_ORDNER, ids=lambda p: p.name)
def test_mod_tests_sind_gruen(mod):
    lauf = _claude("test", str(mod))
    assert lauf.returncode == 0, lauf.stdout + lauf.stderr


@pytest.mark.parametrize("ordner", [MODS, *MOD_ORDNER], ids=lambda p: p.name)
def test_claude_code_liest_mod_und_marktplatz_ohne_fehler(ordner):
    lauf = _claude("validate", str(ordner))
    assert lauf.returncode == 0 and "Validation passed" in lauf.stdout, lauf.stdout + lauf.stderr
