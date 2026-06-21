#!/bin/bash
# Repo-Wurzel dynamisch (CLAUDE_PROJECT_DIR, sonst aus Skript-Pfad) – nach WSL-/ext4-Migration.
REPO="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
CHANGES=$(git -C "$REPO" status --porcelain --untracked-files=all 2>/dev/null | awk '{print $NF}' | grep -v "^docs/" | grep -c . || true)
LEARNED=$(git -C "$REPO" status --porcelain --untracked-files=all 2>/dev/null | awk '{print $NF}' | grep -c "lessons_learned" || true)
if [ "$CHANGES" -gt 0 ] || [ "$LEARNED" -eq 0 ]; then
  echo "SESSION ENDET - offene Punkte:"
  [ "$CHANGES" -gt 0 ] && echo "  -> $CHANGES Code-Aenderung(en) noch nicht committed."
  [ "$LEARNED" -eq 0 ] && [ "$CHANGES" -gt 0 ] && echo "  -> lessons_learned.md hat keinen Eintrag."
  echo "  Neue Session starten und /close-session ausfuehren."
fi
