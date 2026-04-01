#!/bin/bash
REPO="/mnt/c/Users/kieritz/source/repos/mahl"
CHANGES=$(git -C "$REPO" status --porcelain --untracked-files=all 2>/dev/null | awk '{print $NF}' | grep -v "^docs/" | grep -c . || true)
LEARNED=$(git -C "$REPO" status --porcelain --untracked-files=all 2>/dev/null | awk '{print $NF}' | grep -c "lessons_learned" || true)
echo "CONTEXT COMPACTION steht bevor!"
if [ "$CHANGES" -gt 0 ]; then
  echo "  -> $CHANGES Code-Aenderung(en) offen."
  echo "  -> AGENT_MEMORY.md JETZT aktualisieren."
  if [ "$LEARNED" -eq 0 ]; then
    echo "  -> lessons_learned.md JETZT Eintrag erstellen."
  fi
else
  echo "  -> Keine offenen Aenderungen."
fi
