#!/bin/bash
REPO="/mnt/c/Users/kieritz/source/repos/mahl"
CHANGES=$(git -C "$REPO" diff HEAD --name-only 2>/dev/null | grep -v "^docs/" | wc -l)
if [ "$CHANGES" -eq 0 ]; then exit 0; fi
echo "💡 $CHANGES Code-Datei(en) mit uncommitted changes – AGENT_MEMORY.md noch aktuell?"
