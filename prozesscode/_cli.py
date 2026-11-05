"""Gemeinsamer Parser der Prozess-Werkzeuge: abgekürzte Optionen werden abgewiesen.

argparse nimmt standardmäßig jedes eindeutige Präfix einer Option an. So lief `obs set
--beobachtung` still als `--beobachtung-anhängen` und hängte Text an, statt ihn zu ersetzen.
Mit `allow_abbrev=False` scheitert ein solcher Aufruf laut. Unterbefehl-Parser erzeugt argparse
mit der Klasse des Elternparsers, sie erben die Einstellung also. `tests/test_cli_konventionen.py`
verbietet direkte `ArgumentParser`-Aufrufe unter `prozesscode/`.
"""
import argparse


class Parser(argparse.ArgumentParser):
    def __init__(self, **kwargs):
        kwargs.setdefault("allow_abbrev", False)
        super().__init__(**kwargs)
