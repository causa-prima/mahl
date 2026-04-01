#!/bin/bash
REPO="/mnt/c/Users/kieritz/source/repos/mahl"
LEARNED=$(git -C "$REPO" status --porcelain --untracked-files=all 2>/dev/null | awk '{print $NF}' | grep -c "lessons_learned" || true)
if [ "$LEARNED" -eq 0 ]; then
  echo "Task abgeschlossen, aber lessons_learned.md hat noch keinen Eintrag."
  echo "Schritt 6 aus /feature ist Pflicht bevor das Feature als Done gilt."
fi
