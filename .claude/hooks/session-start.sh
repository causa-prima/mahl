#!/bin/bash
# Repo-Wurzel: CLAUDE_PROJECT_DIR (vom Harness gesetzt), sonst aus dem Skript-Pfad ableiten.
# (Früher hartkodiert auf den alten /mnt/c-Windows-Pfad – nach der WSL-/ext4-Migration falsch.)
REPO="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
MEMORY="$REPO/docs/AGENT_MEMORY.md"
if [ -f "$MEMORY" ]; then
  echo "=== AGENT_MEMORY.md ==="
  # {{NEXT_SCENARIO}} wird zum nächsten Szenario laut Feature-Datei aufgelöst (next_scenario.py);
  # bei Fehler gibt das Script den Text unverändert aus, daher || cat als harter Fallback.
  python3 "$REPO/.claude/scripts/next_scenario.py" --render "$MEMORY" || cat "$MEMORY"
  echo "======================="
else
  echo "WARNUNG: docs/AGENT_MEMORY.md wurde nicht gefunden. Informiere den Nutzer: Die Datei fehlt oder wurde verschoben – bitte prüfen ob das beabsichtigt war und ggf. session-start.sh anpassen."
fi
PRINCIPLES="$REPO/docs/kaizen/principles.md"
if [ -f "$PRINCIPLES" ]; then
  echo "=== principles.md ==="
  cat "$PRINCIPLES"
  echo "===================="
else
  echo "WARNUNG: docs/kaizen/principles.md wurde nicht gefunden. Informiere den Nutzer: Die Datei fehlt oder wurde verschoben – bitte prüfen ob das beabsichtigt war und ggf. session-start.sh anpassen."
fi
# Bash-Allow-Liste in den Kontext geben → Agent kennt erlaubte Befehle ab Zeile 1,
# statt sie via wiederholtem Deny "zu lernen" (Friktion-Quelle, S078-Analyse).
BASHHOOK="$REPO/.claude/hooks/check-bash-permission.py"
if [ -f "$BASHHOOK" ]; then
  echo "=== Bash-Allow-Liste (check-bash-permission.py --list) ==="
  python3 "$BASHHOOK" --list
  echo "========================================================="
else
  echo "WARNUNG: .claude/hooks/check-bash-permission.py wurde nicht gefunden – Bash-Allow-Liste konnte nicht geladen werden."
fi
