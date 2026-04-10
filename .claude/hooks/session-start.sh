#!/bin/bash
REPO="/mnt/c/Users/kieritz/source/repos/mahl"
MEMORY="$REPO/docs/AGENT_MEMORY.md"
if [ -f "$MEMORY" ]; then
  echo "=== AGENT_MEMORY.md ==="
  cat "$MEMORY"
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
