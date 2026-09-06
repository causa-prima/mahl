"""Geteilte Konstanten für Kaizen-Scripts (jenga_score.py, retro_report.py)."""

# Impact-Gewichte – identisch mit den Jenga-Score-Abzügen.
# Änderungen hier wirken auf beide Scripts.
IMPACT_WEIGHTS: dict[str, int] = {
    "KRITISCH": 25,
    "HOCH":     10,
    "MITTEL":    3,
    "GERING":    1,
}
