# Session 061 – 2026-04-17

## Thema
Refactoring `check-bash-permission.py`: Architektur-Review, Diskussion, Umsetzung + Permission-System-Recherche.

## Implementiertes

### Code Review via Subagent
- 8 Findings identifiziert (HOCH/MITTEL/NIEDRIG)
- Kernfinding: strukturelle Duplikation `check_command` vs. `check_simple_command`, `^`-Anker in WRONG_APPROACH, `taskkill` falsch platziert

### Architektur-Diskussion (schrittweise erarbeitet)
- `check_simple_command` kann nicht durch Rekursion ersetzt werden → bleibt als benannter Helper (ALLOW → DESTRUCTIVE → deny)
- `check_command`: ONE_TIME_MARKER → WRONG_APPROACH (Gesamtbefehl) → Compound-Split → `check_simple_command` je Segment
- ONE_TIME_MARKER übersteuert jetzt auch WRONG_APPROACH (bewusste Policy-Änderung)
- `^`-Anker aus WRONG_APPROACH entfernt (matcht jetzt auch in Subshells/späteren Segmenten)
- Compound-Check muss VOR ALLOW kommen (sonst `ls && rm -rf` → allow via `^ls\b`)
- WRONG_APPROACH muss VOR Compound-Split laufen (cmd.exe-Pipe-Erkennung auf Gesamtbefehl)

### Unified Deny-Architektur
- `auto-deny` komplett entfernt → nur noch `deny`/`allow`/`ask`
- Rückgabetyp: `tuple[str, str, str]` = (decision, reason, log_type)
- Logging mit Kategorien: `WRONG_APPROACH`, `DESTRUCTIVE`, `UNKNOWN`, `UNSAFE_REDIRECT`, `COMPOUND_*`, `ONE_TIME`
- Neue Deny-Message-Struktur: mit Hint → Hint + `--allow-once`-Footer; ohne Hint → Checkliste mit CLAUDE.md-Verweis + Wrapper-Script-Frage
- `taskkill` → `DESTRUCTIVE_PATTERNS`

### Tests
- `test-bash-permission.py` aktualisiert: 3-Tuple-Unpack, `auto-deny` → `deny`, neue `ask`-Fälle für WRONG_APPROACH+Marker
- Alle Tests grün (200+ Fälle)

### Log-Bereinigung
- `denied-commands.log` gelöscht (5 veraltete Einträge, altes Format)

## Permission-System-Recherche

Ausgiebige Untersuchung warum `rm` trotz Hook-`allow` promptet:

- **Ursache:** `.claude/tmp/` ist ein protected path in Claude Code → immer Prompt unabhängig von Hook und settings.json
- **Nicht die Ursache:** settings.json `allow: []`, fehlende permissions.allow-Einträge
- `"Bash(*)"` in settings.json kurz eingetragen und wieder zurückgenommen (kein Nutzen für diesen Fall)
- Erkenntnisse zu Claude Codes Permission-System:
  - Built-in Read-Only-Liste (ls, cat, grep, etc.) → immer ohne Prompt
  - Hook-`allow` reicht für normale Befehle (jq läuft ohne Prompt)
  - Protected paths (`.claude/`) → immer Prompt, nicht übersteuerbar

## Offene Review-Findings

Vom Subagenten-Review identifiziert, noch nicht umgesetzt. Reihenfolge: #3 zuerst (Sicherheitslücke), dann #1/#4 (schnell), #5/#7 optional.

---

### #1 – sed-Patterns konsolidieren (MITTEL)

**Reviewer-Finding (wörtlich):**

> Zeilen 267–269 enthalten drei nahezu identische sed-Patterns:
> ```python
> re.compile(r"^sed\s+-i\s+'s/\\\\r//'"),
> re.compile(r'^sed\s+-i\s+"s/\\\\r//"'),
> re.compile(r"^sed\s+-i\s+'s/\\r//'"),
> ```
> Diese matchen alle das gleiche Ziel (Carriage-Return-Entfernung), nur mit unterschiedlichen Escape-Sequenzen und Anführungszeichen.

**Konsolidierungsvorschlag des Reviewers:**
```python
re.compile(r"^sed\s+-i\s+['\"]s/\\\\?r//['\"]"),  # \\r oder \\\\r
```
Alternativ (robuster gegen Quote-Mischung):
```python
re.compile(r"^sed\s+-i\s+(?:'|\")\s*s/\\+r//(?:'|\")"),
```

**Achtung:** Regex vor Einchecken gegen alle drei aktuellen Testfälle in `test-bash-permission.py` prüfen (`sed -i 's/\r//'`, `sed -i "s/\\r//"`, etc.).

---

### #3 – find-Lücke (bash/dash/ksh nicht erkannt) + Lookahead-Vereinfachung (MITTEL)

**Reviewer-Finding (wörtlich):**

> **Probleme:**
> 1. Die Negativ-Lookahead sind schwer zu lesen und zu debuggen
> 2. `find -exec bash -c 'rm ...'` (statt `sh`) wird NICHT erkannt → **Lücke**
> 3. `find -exec ... rm` und `find -exec ... sh` sind beide destruktiv, aber die sh-Pattern ist zu breit

**Aktueller Stand in `DESTRUCTIVE_PATTERNS`:**
```python
re.compile(r'\bfind\b.*\s-exec(?:dir)?\b.*\bsh\b'),   # nur sh!
```

**Aktueller Stand in `ALLOW_PATTERNS`:**
```python
re.compile(r'^find\b(?!.*\s-delete\b)(?!.*\s-exec(?:dir)?\b.*\b(?:rm|sh)\b)'),
```

**Vorgeschlagener Fix:**
```python
# DESTRUCTIVE_PATTERNS: beide find-exec-Zeilen durch eine ersetzen:
(re.compile(r'\bfind\b.*\s-exec(?:dir)?\s+(?:rm|bash|sh|dash|ksh)\b'), "Destruktiver Befehl."),

# ALLOW_PATTERNS: Negativ-Lookahead vereinfachen:
re.compile(r'^find\b(?!.*\s(?:-delete|-exec))'),
```

**Testfälle ergänzen** (aktuell fehlen in `test-bash-permission.py`):
- `find . -exec bash -c 'rm -rf {}' \;` → `deny`
- `find . -exec dash -c 'rm {}' \;` → `deny`

---

### #4 – npm run test Lookahead zu simpel (MITTEL)

**Reviewer-Finding (wörtlich):**

> Zeile 105 hat ein negatives Lookahead: `npm\s+run\s+test(?![\w:])` um `test:e2e` und `test:coverage` auszuschließen. Die Lookahead `[\w:]` ist zu simpel – sie matcht nicht `test\n` (Zeilenumbruch) oder Tabulatoren.

**Aktueller Stand:**
```python
re.compile(r'\bnpm\s+run\s+test(?![\w:])'),
```

**Vorschlag des Reviewers (Option A – explizitere Bedingung):**
```python
re.compile(r'\bnpm\s+run\s+test(?:\s|$)'),  # nur wenn Leerzeichen oder Zeilenende folgt
```

**Vorschlag des Reviewers (Option B – getrennte Patterns):**
```python
(re.compile(r'\bnpm\s+run\s+test:e2e\b'), 'E2E-Tests immer via Script...'),   # bleibt wie gehabt
(re.compile(r'\bnpm\s+run\s+test(?:\s|$)'), 'Frontend-Tests immer via Script...'),  # ersetzt altes Pattern
```

**Achtung:** Sicherstellen dass `npm run test:coverage` weiterhin NICHT gematcht wird (soll allow bleiben). Testfall in `test-bash-permission.py` existiert bereits.

---

### #5 – Backticks in split_compound_command undokumentiert (NIEDRIG, als HOCH eingestuft)

**Reviewer-Finding (wörtlich):**

> `split_compound_command` behandelt nur `'` und `"`. Backticks können verschachtelt sein:
> ```bash
> grep "$(echo hello)" file  # $(...) wird nicht als Quote-Kontext erkannt
> ```
> Backtick-Handling:
> ```python
> if c == '`' and not in_double_quote:
>     in_backtick = not in_backtick
> ```
> **Aber:** Die meisten kritischen Befehle (WRONG_APPROACH, DESTRUCTIVE) verwenden `.search()` und würden in Subshells trotzdem matchen – praktisch unkritisch.

**Empfehlung des Reviewers:** Dokumentieren oder fixen.

**Beschluss aus Session-Diskussion:** Mindestens Kommentar in `split_compound_command` ergänzen der die Einschränkung dokumentiert. Fix (Backtick-Tracking) ist optional, da `.search()`-basierte Patterns den Inhalt von Subshells trotzdem matchen.

**Konkreter Kommentar (in `split_compound_command` einfügen):**
```python
# Hinweis: Backtick-Command-Substitution (`...`) und $(...) werden nicht als
# Quote-Kontext behandelt. Praktisch unkritisch, weil WRONG_APPROACH- und
# DESTRUCTIVE_PATTERNS via .search() auch innerhalb von Subshells matchen.
```

---

### #7 – cmd.exe Redirect-Kommentar (NIEDRIG)

**Reviewer-Finding (wörtlich):**

> `if rest.startswith('>&')` erlaubt Redirects wie `>&1`, `>&2`. Das ist korrekt für bash, aber bei `cmd.exe /c "..."` wird der innere Befehl re-geprüft – dort ist `2>&1` syntax error in cmd.exe (Syntax wäre `1>&2`). Praktisch harmlos, aber Kommentar fehlt.

**Fix:** In `has_unsafe_output_redirect`, beim `if rest.startswith('&'):` Block ergänzen:
```python
if rest.startswith('&'):
    # File-Descriptor-Redirect (2>&1, >&2 etc.) – immer erlaubt.
    # Hinweis: cmd.exe kennt andere Redirect-Syntax (1>&2 statt 2>&1),
    # aber wir prüfen hier bash-style. Ungültige cmd.exe-Syntax wird
    # von cmd.exe selbst zur Laufzeit abgefangen.
    i += 1
    continue
```

---

## Offene Punkte (sonstige)
- `"Bash(*)"` in `settings.json` eingetragen (Reason: `.claude/tmp/` ist protected path, Hook reicht für rm nicht aus)
- `denied-commands.log` gelöscht (5 veraltete Einträge, altes Format)

## Ergebnis
Refactoring vollständig, alle Tests grün, sauberere Architektur, besseres Logging, klarere Deny-Messages.
