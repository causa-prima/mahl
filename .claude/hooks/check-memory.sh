#!/bin/bash
# Repo-Wurzel dynamisch (CLAUDE_PROJECT_DIR, sonst aus Skript-Pfad) – nach WSL-/ext4-Migration.
REPO="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
CHANGES=$(git -C "$REPO" diff HEAD --name-only 2>/dev/null | grep -v "^docs/" | wc -l)
if [ "$CHANGES" -eq 0 ]; then exit 0; fi
echo "💡 $CHANGES Code-Datei(en) mit uncommitted changes – AGENT_MEMORY.md noch aktuell?"
