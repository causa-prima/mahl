#!/usr/bin/env python3
"""Extrahiert Survivors aus dem Stryker HTML-Report."""
import re
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
report_path = REPO_ROOT / 'Client/reports/mutation/mutation.html'

with open(report_path, encoding='utf-8') as f:
    html = f.read()

# Stryker (neuere Versionen) bettet JSON als JS-Zuweisung ein:
# app.report = {"files": ..., "schemaVersion": ...}
# Stryker HTML-escaped JS: `<` wird zu `<"+"` um frühzeitiges </script> zu verhindern
# Erst die Escape-Sequenz reparieren, dann JSON parsen
html_fixed = html.replace('<"+"', '<')
match = re.search(r'app\.report\s*=\s*(\{.*\})\s*;?\s*$', html_fixed, re.MULTILINE)
if not match:
    # Fallback: ältere Versionen mit HTML-Attribut
    match = re.search(r"mutation-test-report='([^']+)'", html_fixed)
if not match:
    match = re.search(r'mutation-test-report="([^"]+)"', html_fixed)
if not match:
    print("JSON nicht gefunden", file=sys.stderr)
    sys.exit(1)

data = json.loads(match.group(1))

survivors_found = 0
for filename, file_data in data.get('files', {}).items():
    for mutant in file_data.get('mutants', []):
        if mutant.get('status') == 'Survived':
            survivors_found += 1
            print(f"\n[Survived] {mutant['mutatorName']}")
            print(f"  {filename}:{mutant['location']['start']['line']}:{mutant['location']['start']['column']}")
            if 'replacement' in mutant:
                original = mutant.get('description', mutant.get('original', '(n/a)'))
                print(f"  original : {original}")
                print(f"  replaced : {mutant['replacement']}")

if survivors_found == 0:
    print("Keine Survivors gefunden – 100% Mutation Score!")
else:
    print(f"\n=== Gesamt: {survivors_found} Survivor(s) ===")
