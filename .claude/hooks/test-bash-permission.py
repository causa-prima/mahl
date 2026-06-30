#!/usr/bin/env python3
"""Tests für check-bash-permission.py – verifiziert deny/allow/ask (WSL-native Toolchain)."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from importlib import import_module

hook = import_module("check-bash-permission")
check_command = hook.check_command
split_compound_command = hook.split_compound_command
has_unsafe_output_redirect = hook.has_unsafe_output_redirect
normalize_repo_paths = hook.normalize_repo_paths
build_allow_output = hook._build_allow_output

# Repo-Root wie der Hook ihn auf dieser Maschine auflöst (für Pfad-Normalisierungs-Tests).
REPO_ROOT = hook._NORMALIZE_ROOT


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def assert_decision(command: str, expected: str, description: str = "") -> bool:
    decision, reason, log_type = check_command(command)
    label = description or command
    if decision == expected:
        print(f"  {Colors.GREEN}PASS{Colors.RESET} [{expected:12s}] {label}")
        return True
    else:
        print(f"  {Colors.RED}FAIL{Colors.RESET} [{expected:12s}] {label}")
        print(f"       Got: {decision!r} (log_type={log_type!r}) | reason: {reason[:80] if reason else ''}")
        return False


# ---------------------------------------------------------------------------

def test_compound_detection() -> int:
    print(f"\n{Colors.BOLD}=== Compound-Command-Erkennung & Splitting ==={Colors.RESET}")
    failures = 0

    compound_cases = [
        ("ls -la", False, "Einfacher Befehl"),
        ("ls | grep foo", True, "Pipe"),
        ("ls && echo done", True, "AND"),
        ("echo hello; echo world", True, "Semikolon"),
        ("echo 'hello | world'", False, "Pipe in Single-Quotes"),
        ('echo "hello && world"', False, "AND in Double-Quotes"),
        ('echo "a | b"', False, "Pipe in Double-Quotes"),
    ]
    for command, expected, desc in compound_cases:
        result = len(split_compound_command(command)) > 1
        if result == expected:
            print(f"  {Colors.GREEN}PASS{Colors.RESET} [compound={str(expected):5s}] {desc}")
        else:
            print(f"  {Colors.RED}FAIL{Colors.RESET} [compound={str(expected):5s}] {desc}: {command}")
            print(f"       Got: {result}")
            failures += 1

    split_cases = [
        ("ls | grep foo", ["ls", "grep foo"], "| → 2 Segmente"),
        ("ls -la && echo done", ["ls -la", "echo done"], "&& → 2 Segmente"),
        ("a; b; c", ["a", "b", "c"], "; → 3 Segmente"),
        ("a || b", ["a", "b"], "|| → 2 Segmente"),
        ('echo "a && b" 2>&1 | tail -60', ['echo "a && b" 2>&1', 'tail -60'], "&& in Quotes bleibt Segment, dann Pipe-Split"),
        ("grep foo file | wc -l", ["grep foo file", "wc -l"], "grep | wc"),
    ]
    for command, expected_segs, desc in split_cases:
        result = split_compound_command(command)
        if result == expected_segs:
            print(f"  {Colors.GREEN}PASS{Colors.RESET} [split      ] {desc}")
        else:
            print(f"  {Colors.RED}FAIL{Colors.RESET} [split      ] {desc}: {command}")
            print(f"       Expected: {expected_segs}")
            print(f"       Got:      {result}")
            failures += 1

    return failures


def test_redirect_detection() -> int:
    print(f"\n{Colors.BOLD}=== Redirect-Detektion ==={Colors.RESET}")
    failures = 0

    # (command, expected_has_unsafe_redirect, description)
    cases = [
        # Sicher: kein Redirect
        ("ls -la", False, "kein Redirect"),
        ("grep pattern file", False, "kein Redirect"),
        ("grep '>' file", False, "Pipe in Single-Quote ist kein Redirect"),
        # Sicher: erlaubte Ziele
        ("echo text > /dev/null", False, "/dev/null"),
        ("cat file > /dev/null", False, "cat > /dev/null"),
        ("echo text > .claude/tmp/output.txt", False, ".claude/tmp/"),
        ("grep foo file >> .claude/tmp/results.txt", False, "append zu .claude/tmp/"),
        ("cat file > /dev/stderr", False, "/dev/stderr"),
        # Sicher: File-Descriptor-Redirect (2>&1 etc.)
        ("dotnet build 2>&1", False, "2>&1 kein Datei-Redirect"),
        ("some-cmd >&2", False, ">&2 kein Datei-Redirect"),
        # Unsicher: Redirect zu Produktionsdateien
        ("echo '' > CLAUDE.md", True, "Redirect auf CLAUDE.md"),
        ("cat /dev/null > Server/Program.cs", True, "cat > .cs-Datei"),
        ("sort output.txt > important_file.cs", True, "sort > .cs"),
        ("grep -v test file > file", True, "grep > gleiche Datei"),
        ("echo bad > .claude/settings.json", True, "Redirect auf settings.json"),
        ("echo text >> .claude/hooks/check-bash-permission.py", True, "Append auf Hook"),
        ("echo text > /tmp/file", True, "/tmp/ ist kein erlaubtes Verzeichnis"),
    ]

    for command, expected, desc in cases:
        result = has_unsafe_output_redirect(command)
        if result == expected:
            print(f"  {Colors.GREEN}PASS{Colors.RESET} [unsafe={str(expected):5s}] {desc}")
        else:
            print(f"  {Colors.RED}FAIL{Colors.RESET} [unsafe={str(expected):5s}] {desc}: {command}")
            print(f"       Got: {result}")
            failures += 1

    return failures


def test_deny_patterns() -> int:
    print(f"\n{Colors.BOLD}=== Wrong-Approach-Patterns (kein Override ohne Marker) ==={Colors.RESET}")
    failures = 0

    deny_cases = [
        # dotnet test: immer via Script
        ("dotnet test", "dotnet test direkt"),
        ("dotnet test --filter FooTest", "dotnet test mit Filter"),
        ("dotnet test | tail -60", "dotnet test mit Pipe"),
        # Stryker: immer via Script, nie direkt
        ("dotnet stryker", "Stryker allein"),
        ("dotnet stryker --mutate src/Foo.cs", "Stryker --mutate allein"),
        # python3 mit absolutem Pfad
        ("python3 /tmp/script.py", "python3 /tmp/"),
        ("python3 /absolute/path/script.py", "python3 absoluter Pfad"),
        ("python3 ~/scripts/foo.py", "python3 ~/..."),
        # Hinweis: absoluter Repo-Pfad zu .claude-Script wird seit OBS-1 normalisiert → allow
        # (s. test_path_normalization). Fremde absolute Pfade bleiben deny.
        # git add -f: Secrets-Risiko, kein Override
        ("git add -f .env", "git add -f"),
        ("git add secrets.json --force", "git add --force am Ende"),
        ("git add -f .", "git add -f ."),
        # Unsafe Output-Redirects (außerhalb .claude/tmp/, /dev/null etc.)
        ("echo '' > CLAUDE.md", "echo > CLAUDE.md"),
        ("cat /dev/null > Server/Program.cs", "cat > .cs-Datei"),
        ("grep foo file > output.cs", "grep > .cs"),
        ("sort input.txt > sorted.cs", "sort > .cs"),
        # Frontend Tests: immer via Python-Script, nie direkt
        ("npm run test", "npm run test direkt"),
        ("npm run test -- run", "npm run test -- run direkt"),
        ("npm run test:e2e", "npm run test:e2e direkt"),
        ("npx vitest run", "npx vitest run"),
        ("npx playwright test e2e/ingredients.spec.ts", "npx playwright test"),
        ("npx stryker run", "npx stryker run"),
        # Lint/Mutation: immer via Wrapper
        ("npm run lint", "npm run lint direkt"),
        ("npm run lint:duplicates", "npm run lint:duplicates direkt"),
        ("npx eslint .", "npx eslint direkt"),
        ("npx jscpd src/", "npx jscpd direkt"),
    ]

    for command, desc in deny_cases:
        if not assert_decision(command, "deny", f"{desc}: {command}"):
            failures += 1

    return failures


def test_allow_patterns() -> int:
    print(f"\n{Colors.BOLD}=== Allow-Patterns ==={Colors.RESET}")
    failures = 0

    allow_cases = [
        # dotnet build (nativ)
        ("dotnet build", "dotnet build"),
        ("dotnet build --no-restore", "dotnet build --no-restore"),
        ("dotnet build | grep -E 'error|warning CS'", "dotnet build | grep (Compound)"),
        # dotnet run (nativ)
        ("dotnet run --project Server", "dotnet run --project Server"),
        ("dotnet run --project Server &", "dotnet run im Hintergrund"),
        # dotnet ef (sichere Subcommands)
        ("dotnet ef migrations add InitialCreate", "dotnet ef migrations add"),
        ("dotnet ef migrations remove", "dotnet ef migrations remove"),
        ("dotnet ef migrations list", "dotnet ef migrations list"),
        ("dotnet ef database update", "dotnet ef database update"),
        # dotnet tool (lokales Manifest)
        ("dotnet tool restore", "dotnet tool restore"),
        ("dotnet tool list", "dotnet tool list"),
        # npm run / audit / outdated / update / ci (nativ)
        ("npm run build", "npm run build"),
        ("npm run dev", "npm run dev"),
        ("npm run test:coverage", "npm run test:coverage (kein Wrapper)"),
        ("npm audit", "npm audit"),
        ("npm outdated", "npm outdated"),
        ("npm update", "npm update"),
        ("npm ci", "npm ci (reproduzierbarer Lock-Install)"),
        # kill per PID (gezielt)
        ("kill 1234", "kill PID"),
        ("kill -9 99999", "kill -9 PID"),
        # python3 -m pytest auf .claude/
        ("python3 -m pytest .claude/hooks/tests/ -p no:cacheprovider -s -q", "pytest .claude/hooks/"),
        ("python3 -m pytest .claude/ -q", "pytest .claude/ kurz"),
        # Projekt-Scripts
        ("python3 .claude/scripts/dotnet-test.py --filter TestName", "dotnet-test.py"),
        ("python3 .claude/scripts/dotnet-stryker.py --mutate Domain/Foo.cs --verbose", "dotnet-stryker.py"),
        # Docker v2-Plugin (nativ in WSL); v1 docker-compose → deny (s. test_deny)
        ("docker compose up -d", "docker compose up"),
        ("docker compose down", "docker compose down"),
        # Lese-Befehle
        ("ls", "ls solo"),
        ("ls -la", "ls -la"),
        ("ls -la /home/user/.claude/", "ls mit Pfad"),
        ("cat README.md", "cat"),
        ("tail -20 some.log", "tail"),
        ("head -5 file.txt", "head"),
        ("wc -l file.txt", "wc"),
        ("grep -r 'pattern' src/", "grep"),
        ("find . -name '*.cs'", "find ohne destruktive Flags"),
        ("echo hello", "echo"),
        ("pwd", "pwd"),
        ("date", "date"),
        ("which dotnet", "which"),
        ("diff file1 file2", "diff"),
        ("jq '.' .claude/settings.json", "jq read"),
        ("jq '.permissions' .claude/settings.json", "jq mit Filter"),
        # Datei-/Verzeichnis-Verwaltung
        ("mkdir -p Server/Domain", "mkdir -p"),
        ("mkdir .claude/tmp", "mkdir"),
        ("touch Server/Domain/NewType.cs", "touch"),
        ("chmod +x .claude/hooks/new-hook.sh", "chmod +x"),
        ("chmod +x script.sh", "chmod +x solo"),
        # rm: einzelne Dateien (ohne -r/-R)
        ("rm Client/src/services/ingredientsApi.test.ts", "rm einzelne Datei"),
        ("rm -f some-file.ts", "rm -f (kein -r)"),
        ("rm file1.ts file2.ts", "rm mehrere Dateien"),
        # mv: Dateien verschieben/umbenennen (kaizen-Archivierung)
        ("mv docs/kaizen/lessons_learned.md docs/kaizen/archive/session_056_to_063.md", "mv kaizen archivieren"),
        ("mv some-file.ts other-file.ts", "mv umbenennen"),
        # cp: Dateien kopieren (ohne -r/-R)
        ("cp .claude/skills/kaizen/references/lessons_learned_template.md docs/kaizen/lessons_learned.md", "cp template"),
        ("cp some-file.ts backup-file.ts", "cp einfach"),
        ("cp -p source.txt dest.txt", "cp -p (preserve, kein -r)"),
        # Python: nur .claude/
        ("python3 .claude/scripts/stryker-summary.py", "python3 .claude/scripts/"),
        ("python3 .claude/scripts/jenga_score.py", "jenga_score.py"),
        ("python3 .claude/scripts/jenga_score.py --file docs/kaizen/lessons_learned.md", "jenga_score.py mit --file"),
        ("python3 .claude/hooks/check-code-quality-blocking.py", "python3 .claude/hooks/"),
        # Globales session-recall-Script (read-only, außerhalb des Repos → absoluter Pfad erlaubt)
        ("python3 /home/kieritz/.claude/skills/session-recall/scripts/recall.py sessions --limit 5",
         "recall.py (absoluter Pfad)"),
        ('python3 ~/.claude/skills/session-recall/scripts/recall.py search "review"',
         "recall.py (~-Pfad)"),
        ("python3 /home/kieritz/.claude/skills/session-recall/scripts/recall.py extract --session last | head -50",
         "recall.py | head (Compound, read-only)"),
        # Redirects auf erlaubte Ziele
        ("echo 'output' > .claude/tmp/debug.txt", "echo > .claude/tmp/"),
        ("grep errors log > .claude/tmp/errors.txt", "grep > .claude/tmp/"),
        ("cat file > /dev/null", "cat > /dev/null"),
        # git read-only
        ("git status", "git status"),
        ("git log --oneline -5", "git log"),
        ("git diff HEAD", "git diff"),
        ("git branch -a", "git branch"),
        ("git show HEAD", "git show"),
        ("git stash list", "git stash list"),
        ("git remote -v", "git remote"),
        ("git rev-parse HEAD", "git rev-parse"),
        ("git ls-files", "git ls-files"),
        # git safe write
        ("git add src/Foo.cs", "git add (ohne -f)"),
        ("git add .", "git add ."),
        ("git add -A", "git add -A"),
        ("git add -p", "git add -p (interaktiv)"),
        ("git stash push -m 'save'", "git stash push"),
        ("git stash pop", "git stash pop"),
        # Frontend-Wrapper-Scripts
        ("python3 .claude/scripts/vitest-run.py", "vitest-run.py"),
        ("python3 .claude/scripts/vitest-run.py --filter IngredientsPage", "vitest-run.py --filter"),
        ("python3 .claude/scripts/vitest-run.py --verbose", "vitest-run.py --verbose"),
        ("python3 .claude/scripts/playwright-test.py", "playwright-test.py"),
        ("python3 .claude/scripts/playwright-test.py --filter ingredients", "playwright-test.py --filter"),
        ("python3 .claude/scripts/stryker-frontend.py", "stryker-frontend.py"),
        ("python3 .claude/scripts/stryker-frontend.py --mutate src/pages/IngredientsPage.tsx", "stryker-frontend.py --mutate"),
        ("python3 .claude/scripts/stryker-frontend.py --verbose", "stryker-frontend.py --verbose"),
        # Compound aus erlaubten Segmenten
        ("ls -la && echo done", "Compound: ls && echo"),
        ("grep foo file | wc -l", "Compound: grep | wc"),
        ("find . -name '*.cs' | grep Endpoint", "Compound: find | grep"),
        ("cat file.txt | tail -20", "Compound: cat | tail"),
        ("git status && git diff", "Compound: git status && git diff"),
        ("ls -la | grep .cs | wc -l", "Compound: ls | grep | wc (3 Segmente)"),
        # cd-Navigation (harmlos – gefährliche Kombis bleiben via WRONG_APPROACH/DESTRUCTIVE gedeckt)
        ("cd Client", "cd solo"),
        ("cd .claude/hooks && ls -la", "cd && ls"),
        ("cd Client && git status", "cd && git status"),
        ("cd docs/kaizen/archive && wc -l *.md", "cd && wc"),
        # sed read-only (kein -i) → erlaubt
        ("sed -n '1,40p' docs/process/e2e-testing.md", "sed -n Zeilenbereich"),
        ("cat foo | sed 's/x/y/'", "sed im Pipe (read-only, kein -i)"),
        # find | xargs <safe-readonly> → erlaubt
        ("find . -name '*.feature' | xargs grep -l Zutat", "find | xargs grep"),
        ("find . -name '*.md' | xargs wc -l", "find | xargs wc"),
        ("find . -type f | xargs -I {} grep foo {}", "find | xargs -I grep"),
        # git -C <pfad> read-only → erlaubt
        ("git -C Client log --oneline -3", "git -C log"),
        ("git -C Client diff --stat HEAD", "git -C diff"),
    ]

    for command, desc in allow_cases:
        if not assert_decision(command, "allow", f"{desc}: {command}"):
            failures += 1

    return failures


def test_deny() -> int:
    print(f"\n{Colors.BOLD}=== Deny (kein Match / destruktiv) ==={Colors.RESET}")
    failures = 0

    deny_cases = [
        # Word-Boundary korrekt
        ("lsof", "lsof (NICHT ls)"),
        ("lsblk", "lsblk (NICHT ls)"),
        ("catalog something", "catalog (NICHT cat)"),
        # python3 außerhalb .claude/ (relativ → deny)
        ("python3 ./one_off_analysis.py", "python3 relative path (nicht .claude/)"),
        ("python3 -c 'print(1)'", "python3 -c"),
        ("python3 -c 'import os; os.system(\"rm -rf /\")'", "python3 -c mit rm -rf (Obfuskation → deny)"),
        # recall.py-Ausnahme greift NUR exakt diesen Pfad – andere absolute python3-Pfade bleiben deny
        ("python3 /home/kieritz/.claude/skills/other/scripts/recall.py", "absoluter python3-Pfad ≠ session-recall → deny"),
        ("python3 /home/kieritz/evil.py", "fremder absoluter python3-Pfad → deny"),
        # recall.py read-only, aber destruktives Segment im Compound bleibt deny (Per-Segment-Check)
        ("python3 /home/kieritz/.claude/skills/session-recall/scripts/recall.py search x | rm -rf foo",
         "recall.py | rm -rf (destruktives Segment → deny)"),
        # dotnet ef database drop → deny
        ("dotnet ef database drop", "dotnet ef database drop"),
        # dotnet: andere Subcommands nicht erlaubt
        ("dotnet publish", "dotnet publish"),
        ("dotnet format", "dotnet format"),
        # docker-compose (v1) nicht verfügbar in dieser WSL-Distro → deny mit Smart-Hint auf docker compose
        ("docker-compose up -d", "docker-compose v1 → deny (nutze docker compose)"),
        ("docker-compose down", "docker-compose down v1 → deny"),
        # cp -r: rekursives Kopieren → deny
        ("cp -r docs/ backup/", "cp -r (rekursiv)"),
        ("cp -R src/ dest/", "cp -R (rekursiv, Großbuchstabe)"),
        ("cp -rp src/ dest/", "cp -rp (rekursiv + preserve)"),
        # chmod: nur +x erlaubt
        ("chmod 755 file", "chmod 755 (nicht +x)"),
        ("chmod -R 777 .", "chmod -R"),
        ("chmod a-x file", "chmod a-x"),
        # git: nicht auto-allowed
        ("git push origin main", "git push (nicht force)"),
        ("git commit -m 'test'", "git commit"),
        ("git merge feature-branch", "git merge"),
        ("git rebase main", "git rebase"),
        ("git checkout feature-branch", "git checkout Branch"),
        # Unbekannte Befehle
        ("curl https://example.com", "curl"),
        ("wget https://example.com", "wget"),
        ("npm install", "npm install (Dependency-Prozess)"),
        ("npm install left-pad", "npm install <pkg>"),
        ("apt-get install foo", "apt-get"),
        ("whoami", "whoami"),
        # Compound mit unbekanntem Segment
        ("ls -la && curl https://example.com", "Compound: ls && curl"),
        ("grep foo file | apt-get install foo", "Compound: grep | apt-get"),
        # Destruktive Befehle ohne --allow-once → deny (freigabefähig per Marker)
        ("rm -rf /tmp/build", "rm -rf"),
        ("rm -r some-directory", "rm -r"),
        ("rm -fR dir", "rm -fR"),
        ("find . -delete", "find -delete"),
        ("find . -name '*.cs' -delete", "find -name -delete"),
        ("find . -exec rm -rf {} +", "find -exec rm"),
        ("find . -execdir rm {} ;", "find -execdir rm"),
        ("find . -exec sh -c 'rm -rf {}' \\;", "find -exec sh -c rm"),
        ("find . -execdir sh -c 'echo hi' \\;", "find -execdir sh (auch ohne rm destruktiv)"),
        ("find . -exec bash -c 'rm -rf {}' \\;", "find -exec bash"),
        ("find . -exec dash -c 'rm {}' \\;", "find -exec dash"),
        ("git push --force origin main", "git push --force"),
        ("git reset --hard HEAD~1", "git reset --hard"),
        ("git clean -fd", "git clean -fd"),
        ("git clean -xfd", "git clean -xfd"),
        ("git checkout .", "git checkout ."),
        ("git restore .", "git restore ."),
        # Prozess-Kill nach Name ist destruktiv (in DESTRUCTIVE_PATTERNS)
        ("pkill -f dotnet", "pkill ohne Marker"),
        ("killall node", "killall ohne Marker"),
        # cd erlaubt – aber gefährliche Folge-Segmente bleiben deny
        ("cd Client && rm -rf dist", "cd && rm -rf → deny (DESTRUCTIVE-Segment)"),
        ("cd Client && npx vitest run", "cd && npx → deny (WRONG_APPROACH)"),
        ("cd Server && dotnet publish", "cd && dotnet publish → deny (unbekanntes Segment)"),
        # sed mit -i bleibt deny – Edit-Tool verwenden (auch s/\r// – kein NTFS-Sonderfall mehr auf ext4)
        ("sed -i 's/foo/bar/' file.txt", "sed -i Edit → deny"),
        ("sed -i 's/\\r//' some-file.sh", "sed -i s/\\r// → deny (ext4: kein CRLF)"),
        ("cat x | sed -i 's/a/b/' y.txt", "sed -i im Pipe → deny"),
        # xargs mit nicht-read-only Child bleibt deny
        ("find . -name '*.tmp' | xargs rm", "find | xargs rm → deny"),
        ("find . | xargs -I {} mv {} /tmp", "find | xargs mv → deny"),
        ("echo x | xargs bash -c 'rm -rf /'", "xargs bash → deny"),
    ]

    for command, desc in deny_cases:
        if not assert_decision(command, "deny", f"{desc}: {command}"):
            failures += 1

    return failures


def test_one_time_marker() -> int:
    print(f"\n{Colors.BOLD}=== One-Time-Marker (# --allow-once) ==={Colors.RESET}")
    failures = 0

    ask_cases = [
        # Unbekannte / seltene Befehle
        ('pkill -f dotnet # --allow-once', "pkill mit Marker"),
        ('some-unknown-command --args # --allow-once', "unbekannter Befehl mit Marker"),
        ('npm install # --allow-once', "npm install mit Marker"),
        ('curl https://example.com/dotnet-install.sh # --allow-once', "curl mit Marker"),
        # Destruktive Befehle: Marker macht sie freigabefähig
        ('rm -rf Client/dist/ # --allow-once', "rm -rf mit Marker → ask"),
        ('rm -r some-directory # --allow-once', "rm -r mit Marker → ask"),
        ('git push --force origin main # --allow-once', "git push --force mit Marker → ask"),
        ('git reset --hard HEAD~1 # --allow-once', "git reset --hard mit Marker → ask"),
        ('git clean -fd # --allow-once', "git clean -fd mit Marker → ask"),
        ('find . -delete # --allow-once', "find -delete mit Marker → ask"),
        ("find . -exec sh -c 'rm -rf {}' \\; # --allow-once", "find -exec sh mit Marker → ask"),
        # WRONG_APPROACH: Marker übersteuert jetzt auch diese
        ('dotnet test # --allow-once', "dotnet test + Marker → ask"),
        ('git add -f .env # --allow-once', "git add -f + Marker → ask"),
        ('python3 /tmp/script.py # --allow-once', "python3 absoluter Pfad + Marker → ask"),
    ]
    for command, desc in ask_cases:
        if not assert_decision(command, "ask", f"{desc}: {command}"):
            failures += 1

    # (a) Marker UNNÖTIG: nackter Befehl ist ohnehin erlaubt → allow (kein sinnloser Prompt).
    allow_cases = [
        ('git status # --allow-once', "git status (allow-listed) + Marker → allow"),
        ('python3 .claude/scripts/x.py # --allow-once', "erlaubtes Script + Marker → allow"),
    ]
    for command, desc in allow_cases:
        if not assert_decision(command, "allow", f"{desc}: {command}"):
            failures += 1

    # (a) der allow-Fall trägt den 'unnötig'-Hinweis + eigenen log_type (für den Agent-Nudge).
    _, r_unneeded, lt_unneeded = check_command('git status # --allow-once')
    if "nicht nötig" not in r_unneeded or lt_unneeded != "ONE_TIME_UNNEEDED":
        print(f"  FAIL: --allow-once-unnötig-Hinweis fehlt (reason={r_unneeded!r}, log_type={lt_unneeded!r})")
        failures += 1

    # (b) legitimer Override (nackter Befehl deny): ask trägt den Deny-Grund/die Gefahr als Reason
    #     (sonst bekäme der User-Freigabe-Prompt keinen Kontext).
    _, r_danger, _ = check_command('rm -rf Client/dist/ # --allow-once')
    if not r_danger:
        print("  FAIL: ask-Reason (Gefahr) ist leer – User-Prompt ohne Kontext")
        failures += 1

    return failures


def test_deny_overrides_allow() -> int:
    print(f"\n{Colors.BOLD}=== Prioritäten: WRONG_APPROACH / DESTRUCTIVE vs. ALLOW ==={Colors.RESET}")
    failures = 0

    cases = [
        # dotnet test MIT Pipe → deny (WRONG_APPROACH schlägt allow)
        ("dotnet test | tail -60", "deny", "dotnet test | tail → deny"),
        # git add -f schlägt git-add-Allow
        ("git add -f .env", "deny", "git add -f schlägt git-add-allow"),
        # Stryker immer deny → Script verwenden
        ("dotnet stryker", "deny", "Stryker direkt → deny"),
        # npm run lint / lint:duplicates → immer Wrapper-Script (WRONG_APPROACH)
        ("npm run lint", "deny", "npm run lint → deny (eslint-run.py verwenden)"),
        ("npm run lint:duplicates", "deny", "npm run lint:duplicates → deny (jscpd-run.py verwenden)"),
        # npm run test → Wrapper; npm run build → allow
        ("npm run test", "deny", "npm run test → deny (vitest-run.py)"),
        ("npm run build", "allow", "npm run build → allow (kein Wrapper nötig)"),
        # find ohne destruktive Flags → allow; destruktive find-Varianten → deny
        ("find . -name '*.cs'", "allow", "find ohne destruktive Flags → allow"),
        ("find . -delete", "deny", "find -delete → deny (freigabefähig)"),
        ("find . -exec sh -c 'rm -rf {}' \\;", "deny", "find -exec sh → deny"),
        # rm einzelne Datei → allow; rm -rf → deny (nicht allow)
        ("rm file.ts", "allow", "rm einzelne Datei → allow"),
        ("rm -rf /tmp", "deny", "rm -rf → deny (freigabefähig)"),
        # kill per PID → allow; pkill/killall by-name → deny
        ("kill 1234", "allow", "kill PID → allow"),
        ("pkill -f dotnet", "deny", "pkill → deny (freigabefähig)"),
        # git add ohne -f → allow (negativfilter explizit im Pattern)
        ("git add src/Foo.cs", "allow", "git add ohne -f → allow"),
    ]

    for command, expected, desc in cases:
        if not assert_decision(command, expected, f"{desc}: {command}"):
            failures += 1

    return failures


def test_edge_cases() -> int:
    print(f"\n{Colors.BOLD}=== Randfälle ==={Colors.RESET}")
    failures = 0

    cases = [
        ("", "deny", "Leerer Befehl"),
        ("  ", "deny", "Nur Whitespace"),
        ("git add .", "allow", "git add . (erlaubt)"),
        ("git add -A", "allow", "git add -A (erlaubt)"),
        ("sed -i 's/foo/bar/g' file.txt", "deny", "sed allgemein (nicht \\r-Spezialfall)"),
        # chmod +x ist erlaubt, andere Modes nicht
        ("chmod +x .claude/hooks/script.sh", "allow", "chmod +x erlaubt"),
        ("chmod 644 file", "deny", "chmod 644 nicht erlaubt"),
        # jq ist erlaubt
        ("jq '.' file.json", "allow", "jq erlaubt"),
        ("jq -r '.name' package.json", "allow", "jq -r erlaubt"),
        # mkdir erlaubt
        ("mkdir -p src/Components", "allow", "mkdir -p erlaubt"),
        # touch erlaubt
        ("touch new_file.cs", "allow", "touch erlaubt"),
    ]

    for command, expected, desc in cases:
        if not assert_decision(command, expected, f"{desc}: '{command}'"):
            failures += 1

    return failures


def test_path_normalization() -> int:
    print(f"\n{Colors.BOLD}=== Repo-Pfad-Normalisierung (OBS-1) ==={Colors.RESET}")
    failures = 0

    R = REPO_ROOT  # absoluter Repo-Root wie vom Hook aufgelöst

    # (command, expected_normalized, expected_changed, description)
    norm_cases = [
        # Präfix mit Pfad-Fortsetzung → relativ (Hauptfall: python3 absoluter Pfad)
        (f"python3 {R}/.claude/scripts/dotnet-test.py",
         "python3 .claude/scripts/dotnet-test.py", True, "python3 absoluter Repo-Pfad"),
        (f"cat {R}/.claude/tmp/out.txt",
         "cat .claude/tmp/out.txt", True, "cat absoluter Repo-Pfad"),
        (f"ls {R}/docs",
         "ls docs", True, "ls Unterverzeichnis"),
        # Bare-Root (kein Folge-Pfad) → '.'
        (f"cd {R} && git status",
         "cd . && git status", True, "cd bare-root vor &&"),
        (f"git -C {R} diff --stat HEAD",
         "git -C . diff --stat HEAD", True, "git -C bare-root"),
        (f"cd {R}/",
         "cd .", True, "bare-root mit Trailing-Slash → ."),
        # Mehrere Vorkommen (breit)
        (f"diff {R}/a.txt {R}/b.txt",
         "diff a.txt b.txt", True, "zwei Vorkommen"),
        # Kein Repo-Pfad → unverändert
        ("python3 /tmp/script.py", "python3 /tmp/script.py", False, "fremder absoluter Pfad unverändert"),
        ("ls docs", "ls docs", False, "bereits relativ"),
    ]
    for command, expected, expected_changed, desc in norm_cases:
        result, changed = normalize_repo_paths(command)
        ok = result == expected and changed == expected_changed
        if ok:
            print(f"  {Colors.GREEN}PASS{Colors.RESET} [normalize  ] {desc}")
        else:
            print(f"  {Colors.RED}FAIL{Colors.RESET} [normalize  ] {desc}: {command}")
            print(f"       Expected: {expected!r} (changed={expected_changed})")
            print(f"       Got:      {result!r} (changed={changed})")
            failures += 1

    # check_command normalisiert vor der Prüfung → absoluter Repo-Pfad zu .claude-Script wird allow
    flip_cases = [
        (f"python3 {R}/.claude/scripts/dotnet-test.py", "allow",
         "absoluter Repo-Pfad zu .claude-Script → allow (vorher deny)"),
        (f"python3 {R}/.claude/hooks/check-code-quality-blocking.py", "allow",
         "absoluter Repo-Pfad zu .claude-Hook → allow"),
    ]
    for command, expected, desc in flip_cases:
        if not assert_decision(command, expected, desc):
            failures += 1

    # # --allow-once auf einem ohnehin erlaubten Befehl (absoluter Repo-Pfad → normalisiert allow):
    # Marker war unnötig → allow (kein sinnloser Prompt), nicht ask.
    if not assert_decision(f"python3 {R}/.claude/scripts/x.py # --allow-once", "allow",
                           "# --allow-once unnötig (Befehl ohnehin erlaubt) → allow"):
        failures += 1

    # _build_allow_output: bei Änderung updatedInput + additionalContext, sonst nicht
    changed_cmd = f"python3 {R}/.claude/scripts/dotnet-test.py"
    out = build_allow_output(changed_cmd)
    if (out.get("updatedInput", {}).get("command") == "python3 .claude/scripts/dotnet-test.py"
            and out.get("permissionDecision") == "allow"
            and out.get("additionalContext")):
        print(f"  {Colors.GREEN}PASS{Colors.RESET} [output     ] updatedInput + additionalContext bei Normalisierung")
    else:
        print(f"  {Colors.RED}FAIL{Colors.RESET} [output     ] updatedInput fehlt/falsch: {out}")
        failures += 1

    out_plain = build_allow_output("ls docs")
    if "updatedInput" not in out_plain and "additionalContext" not in out_plain:
        print(f"  {Colors.GREEN}PASS{Colors.RESET} [output     ] kein updatedInput ohne Pfad-Änderung")
    else:
        print(f"  {Colors.RED}FAIL{Colors.RESET} [output     ] unerwartetes updatedInput: {out_plain}")
        failures += 1

    return failures


def test_allowed_logging() -> int:
    print(f"\n{Colors.BOLD}=== Allowed-Command-Logging (OBS-3 D) ==={Colors.RESET}")
    import tempfile
    failures = 0

    # Erlaubte Befehle gehen in ein SEPARATES Log (nicht ins Deny-Log).
    if hook._ALLOWED_LOG_FILE != hook._LOG_FILE:
        print(f"  {Colors.GREEN}PASS{Colors.RESET} [log        ] allowed-Log ≠ denied-Log")
    else:
        print(f"  {Colors.RED}FAIL{Colors.RESET} [log        ] allowed- und denied-Log sind identisch")
        failures += 1

    # _log_command schreibt [log_type] + Befehl in die angegebene Datei.
    with tempfile.TemporaryDirectory() as d:
        target = os.path.join(d, "sub", "allowed.log")  # Verzeichnis wird angelegt
        hook._log_command("ls -la && echo done", "ALLOW", target)
        content = open(target, encoding="utf-8").read()
        if "[ALLOW] ls -la && echo done" in content:
            print(f"  {Colors.GREEN}PASS{Colors.RESET} [log        ] _log_command schreibt in Zieldatei")
        else:
            print(f"  {Colors.RED}FAIL{Colors.RESET} [log        ] Inhalt unerwartet: {content!r}")
            failures += 1

    return failures


def main() -> None:
    total_failures = 0

    total_failures += test_compound_detection()
    total_failures += test_redirect_detection()
    total_failures += test_deny_patterns()
    total_failures += test_allow_patterns()
    total_failures += test_deny()
    total_failures += test_one_time_marker()
    total_failures += test_deny_overrides_allow()
    total_failures += test_edge_cases()
    total_failures += test_path_normalization()
    total_failures += test_allowed_logging()

    print(f"\n{'=' * 60}")
    if total_failures == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}Alle Tests bestanden!{Colors.RESET}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}{total_failures} Test(s) fehlgeschlagen!{Colors.RESET}")
    sys.exit(1 if total_failures > 0 else 0)


if __name__ == "__main__":
    main()
