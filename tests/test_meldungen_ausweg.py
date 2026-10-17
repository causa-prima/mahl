"""Jede Blockier-Meldung eines Guards nennt ihren Ausweg (CGP-meldungen).

Die Tests der einzelnen Guards vergleichen ihre Meldung mit den Modulkonstanten – richtig, weil
ein wörtlicher Vergleich bei jeder Umformulierung bräche. Nur bliebe dann auch eine geleerte
Konstante grün: Erwartung und Ergebnis wären beide leer. Hier steht deshalb je Meldung das
Schlüsselwort, an dem der Ausweg hängt – der Marker für den Einzelfall oder der Befehl, der
weiterhilft –, nicht der ganze Satz.
"""
from importlib import import_module

import pytest

_PAKET = "prozesscode.hooks."


@pytest.mark.parametrize("modul, konstante, ausweg", [
    ("check-bash-permission", "_ALLOW_ONCE_WITH_HINT_FOOTER", "# --allow-once"),
    ("check-bash-permission", "_NO_HINT_MESSAGE", "--list"),
    ("check-dependency-allowlist", "DENY_MESSAGE", "docs/reference/dependencies.md"),
    ("check-dependency-allowlist", "DENY_MESSAGE_DIRECTORY_BUILD", "Directory.Packages.props"),
    ("check-td-capture", "_VORLAGE", "**Fällig:**"),
    ("check-td-capture", "_JETZT_OHNE_MEMORY", "Nächste Prioritäten"),
    ("check-oq-capture", "_VORLAGE", "**Aufschubgrund:**"),
    ("check-obs-capture", "_VORLAGE", "obs-ok"),
    ("check-adr-capture", "_HINWEIS_SESSION", "adr-ok"),
    ("check-adr-capture", "_HINWEIS_AUFSCHUB", "docs/tech-debt.md"),
    ("check-dangling-refs", "_HINWEIS", "dangling-ok"),
    ("check-anchors", "_HINWEIS_VERWAIST", "anchor-ok"),
    ("check-anchors", "_HINWEIS_TOT", "python3 -m prozesscode.anchors list"),
    ("check-anchors", "_HINWEIS_FALSCH", "python3 -m prozesscode.anchors list"),
    ("check-ordinale", "_HINWEIS", "ordinal-ok"),
    ("check-ref-direction", "_HINWEIS", "ref-ok"),
    ("check-feature-plan", "_HINWEIS", "python3 -m prozesscode.next_run --check"),
    ("check-e2e-scenario-ref", "_HINWEIS", "/gherkin-workshop"),
])
def test_meldung_nennt_den_ausweg(modul, konstante, ausweg):
    assert ausweg in getattr(import_module(_PAKET + modul), konstante)
