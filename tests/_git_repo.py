"""Wegwerf-git-Repos für Tests, die Werkzeuge gegen echte `git`-Ausgabe prüfen.

Kein Testmodul (kein `test_`-Präfix), damit pytest es nicht sammelt; importierbar, weil pytest
das Verzeichnis `tests/` beim Sammeln in den Suchpfad legt.
"""
import subprocess


def init_repo(path):
    """Legt ein leeres git-Repo in path an und gibt eine git-Aufruf-Closure zurück."""
    def g(*a):
        return subprocess.run(["git"] + list(a), cwd=path, capture_output=True, text=True)
    g("init", "-q")
    g("config", "user.email", "t@t")
    g("config", "user.name", "t")
    return g


def write_file(path, rel, content):
    """Schreibt content nach path/rel, legt fehlende Verzeichnisse an und gibt den Pfad zurück."""
    fp = path / rel
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content, encoding="utf-8")
    return fp
