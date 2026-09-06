"""Die Hooks, die Claude Code vor und nach einem Tool-Aufruf ausführt.

Warum hier und nicht unter `.claude/hooks/`: `.claude` ist wegen des führenden Punkts kein
gültiger Python-Paketname, und mutmut adressiert Mutanten über den Modulpfad
(`MUTANT_UNDER_TEST=prozesscode.hooks.check-td-capture.x_pruefe__mutmut_3`). Solange die Hooks
dort lagen, konnte kein Mutationstest sie erreichen – ausgerechnet den Code, dessen stummer
Ausfall am teuersten ist: Ein Guard, der nichts mehr prüft, löst per Definition nichts aus.

Registriert werden sie weiterhin in `.claude/settings.json`, jetzt als Modulaufruf
(`cd "$CLAUDE_PROJECT_DIR" && python3 -m prozesscode.hooks.<name>`) statt als Dateipfad – der
`-m`-Start ist nötig, weil die Module relative Importe nutzen und ohne Paketkontext nicht
laden. Bindestriche im Modulnamen stören dabei nicht: `-m` löst über den Paketpfad auf, nicht
über einen Bezeichner.
"""
