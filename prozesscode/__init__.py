"""Prozess-Code als importierbares Paket.

Der Inhalt steuert den Arbeitsprozess (Wrapper, Tracker-Logik, Hook-Bausteine). Er liegt
hier statt unter `.claude/`, weil ein Verzeichnis mit führendem Punkt kein gültiger
Python-Paketpfad ist – und ohne den lässt sich der Code weder sauber importieren noch
mit mutmut prüfen.
"""
