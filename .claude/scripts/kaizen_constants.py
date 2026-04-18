"""Geteilte Konstanten für Kaizen-Scripts (jenga_score.py, retro_report.py)."""

# Schwere-Gewichte – identisch mit den Jenga-Score-Abzügen.
# Änderungen hier wirken auf beide Scripts.
SCHWERE_WEIGHTS: dict[str, int] = {
    "KRITISCH": 25,
    "HOCH":     10,
    "MITTEL":    3,
    "GERING":    1,
}
