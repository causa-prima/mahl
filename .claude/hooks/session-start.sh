#\!/bin/bash
REPO="/mnt/c/Users/kieritz/source/repos/mahl"
MEMORY="$REPO/docs/AGENT_MEMORY.md"
if [ -f "$MEMORY" ]; then
  echo "=== AGENT_MEMORY.md ==="
  cat "$MEMORY"
  echo "======================="
fi
