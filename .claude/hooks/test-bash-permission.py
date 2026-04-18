#!/usr/bin/env python3
"""Tests für check-bash-permission.py – verifiziert deny/allow/ask."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from importlib import import_module

hook = import_module("check-bash-permission")
check_command = hook.check_command
split_compound_command = hook.split_compound_command
has_unsafe_output_redirect = hook.has_unsafe_output_redirect


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
        ('cmd.exe /c "cd /d C:\\mahl && dotnet build"', False, "cmd.exe: && in Quotes"),
        ('cmd.exe /c "dotnet test | tee log.txt"', False, "cmd.exe: Pipe in Quotes"),
        ("echo 'hello | world'", False, "Pipe in Single-Quotes"),
        ('echo "hello && world"', False, "AND in Double-Quotes"),
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
        ('cmd.exe /c "a && b" 2>&1 | tail -60', ['cmd.exe /c "a && b" 2>&1', 'tail -60'], "cmd.exe: && in Quotes bleibt Segment"),
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
        ('cmd.exe /c "..." 2>&1', False, "2>&1 kein Datei-Redirect"),
        ("some-cmd >&2", False, ">&2 kein Datei-Redirect"),
        # cmd.exe: Redirect innerhalb der Anführungszeichen
        ('cmd.exe /c "dotnet test > C:\\Windows\\Temp\\out.txt"', True, "cmd.exe: unsafe Redirect in Quotes"),
        ('cmd.exe /c "dotnet test > C:\\Users\\kieritz\\AppData\\Local\\Temp\\test_out.txt 2>&1"', True, "cmd.exe: unsafe Redirect in Quotes mit 2>&1"),
        ('cmd.exe /c "dotnet test > /dev/null"', False, "cmd.exe: safe Redirect (/dev/null) in Quotes"),
        ('cmd.exe /c "dotnet build > .claude/tmp/build.txt"', False, "cmd.exe: safe Redirect (.claude/tmp/) in Quotes"),
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
        ('cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl && dotnet test"', "dotnet test direkt"),
        ('cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl && dotnet test > C:\\Users\\kieritz\\AppData\\Local\\Temp\\test_out.txt 2>&1"', "dotnet test mit unsafe Redirect"),
        (
            'output=$(cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl && dotnet test")\necho "$output" | grep -E "(Failed|Passed)"',
            "Variable-Capture dotnet test",
        ),
        # Stryker: immer via Script, nie direkt
        ('cmd.exe /c "cd /d C:\\mahl && dotnet stryker"', "Stryker allein"),
        ('cmd.exe /c "cd /d C:\\mahl && dotnet stryker --mutate src/Foo.cs"', "Stryker --mutate allein"),
        # WSL: Pipe in cmd.exe
        ('cmd.exe /c "cd /d C:\\mahl && dotnet test" | tail -60', "Pipe nach cmd.exe"),
        # python3 mit absolutem Pfad
        ("python3 /tmp/script.py", "python3 /tmp/"),
        ("python3 /absolute/path/script.py", "python3 absoluter Pfad"),
        ("python3 ~/scripts/foo.py", "python3 ~/..."),
        ("python3 /mnt/c/Users/kieritz/source/repos/mahl/.claude/scripts/dotnet-test.py", "python3 absoluter Pfad zu .claude-Script"),
        # git add -f: Secrets-Risiko, kein Override
        ("git add -f .env", "git add -f"),
        ("git add secrets.json --force", "git add --force am Ende"),
        ("git add -f .", "git add -f ."),
        # Unsafe Output-Redirects (außerhalb .claude/tmp/, /dev/null etc.)
        ("echo '' > CLAUDE.md", "echo > CLAUDE.md"),
        ("cat /dev/null > Server/Program.cs", "cat > .cs-Datei"),
        ("grep foo file > output.cs", "grep > .cs"),
        ("sort input.txt > sorted.cs", "sort > .cs"),
        # cmd.exe type → Read-Tool verwenden
        ('cmd.exe /c "type C:\\Users\\kieritz\\source\\repos\\mahl\\docs\\GLOSSARY.md"', "cmd.exe type"),
        ('output=$(cmd.exe /c "type C:\\Users\\kieritz\\source\\repos\\mahl\\docs\\GLOSSARY.md")', "output=$(cmd.exe type)"),
        # Frontend Tests: immer via Python-Script, nie direkt
        ('cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl\\Client && npm run test"', "npm run test direkt"),
        ('cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl\\Client && npm run test -- run"', "npm run test -- run direkt"),
        ('cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl\\Client && npm run test:e2e"', "npm run test:e2e direkt"),
        ('cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl\\Client && npx vitest run"', "npx vitest run via cmd.exe"),
        ('cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl\\Client && npx playwright test"', "npx playwright test via cmd.exe"),
        ('cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl\\Client && npx stryker run"', "npx stryker run via cmd.exe"),
        ("npx vitest run", "npx vitest run (WSL direkt)"),
        ("npx playwright test e2e/ingredients.spec.ts", "npx playwright test (WSL direkt)"),
        ("npx stryker run", "npx stryker run (WSL direkt)"),
        ("npm run test", "npm run test (WSL direkt)"),
        ("npm run test:e2e", "npm run test:e2e (WSL direkt)"),
    ]

    for command, desc in deny_cases:
        if not assert_decision(command, "deny", f"{desc}: {command}"):
            failures += 1

    return failures


def test_allow_patterns() -> int:
    print(f"\n{Colors.BOLD}=== Allow-Patterns ==={Colors.RESET}")
    failures = 0

    allow_cases = [
        # dotnet build über cmd.exe
        ('cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl && dotnet build"', "dotnet build"),
        ('cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl && dotnet build --no-restore"', "dotnet build --no-restore"),
        # dotnet ef (sichere Subcommands)
        ('cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl && dotnet ef migrations add InitialCreate"', "dotnet ef migrations add"),
        ('cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl && dotnet ef migrations remove"', "dotnet ef migrations remove"),
        ('cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl && dotnet ef migrations list"', "dotnet ef migrations list"),
        ('cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl && dotnet ef database update"', "dotnet ef database update"),
        # npm run / npm audit
        ('cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl\\Client && npm run build"', "npm run build"),
        ('cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl\\Client && npm audit"', "npm audit"),
        # python3 -m pytest auf .claude/
        ("python3 -m pytest .claude/hooks/tests/ -p no:cacheprovider -s -q", "pytest .claude/hooks/"),
        ("python3 -m pytest .claude/ -q", "pytest .claude/ kurz"),
        # Projekt-Scripts
        ("python3 .claude/scripts/dotnet-test.py --filter TestName", "dotnet-test.py"),
        ("python3 .claude/scripts/dotnet-stryker.py --mutate Domain/Foo.cs --detail", "dotnet-stryker.py"),
        # Docker
        ("docker-compose up -d", "docker-compose up"),
        ("docker-compose down", "docker-compose down"),
        ("docker compose up -d", "docker compose up"),
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
        ("mv docs/kaizen/lessons_learned.md docs/kaizen/archive/session_064_to_070.md", "mv kaizen archivieren 2"),
        ("mv some-file.ts other-file.ts", "mv umbenennen"),
        # cp: Dateien kopieren (ohne -r/-R)
        ("cp .claude/skills/kaizen/references/lessons_learned_template.md docs/kaizen/lessons_learned.md", "cp template"),
        ("cp some-file.ts backup-file.ts", "cp einfach"),
        ("cp -p source.txt dest.txt", "cp -p (preserve, kein -r)"),
        # Python: nur .claude/
        ("python3 .claude/scripts/stryker-summary.py", "python3 .claude/scripts/"),
        ("python3 .claude/scripts/jenga_score.py", "jenga_score.py"),
        ("python3 .claude/scripts/jenga_score.py --file docs/kaizen/lessons_learned.md", "jenga_score.py mit --file"),
        ("python3 .claude/scripts/retro_report.py", "retro_report.py"),
        ("python3 .claude/scripts/retro_report.py --current docs/kaizen/lessons_learned.md", "retro_report.py mit --current"),
        ("python3 .claude/hooks/check-code-quality-blocking.py", "python3 .claude/hooks/"),
        # sed \r-Bereinigung
        ("sed -i 's/\\r//' some-file.sh", "sed \\r"),
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
        # Variable-Capture-Pattern für dotnet build (nicht test – dafür Script nutzen)
        (
            'output=$(cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl && dotnet build Server.Tests 2>&1")\necho "$output" | grep -E "(error|warning CS|Build succeeded)" | head -30',
            "Variable-Capture dotnet build + grep | head",
        ),
        # dotnet run via cmd.exe
        ('cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl && dotnet run --project Server"', "dotnet run --project Server"),
        ('cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl && dotnet run --project Server" &', "dotnet run im Hintergrund"),
        ('cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl && set ASPNETCORE_URLS=http://localhost:5059 && dotnet run --project Server"', "dotnet run mit Env-Var"),
        # docker-compose via cmd.exe
        ('cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl && docker-compose up -d"', "docker-compose up via cmd.exe"),
        # npm run build/dev/lint/preview via cmd.exe (kein Wrapper nötig)
        ('cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl\\Client && npm run dev"', "npm run dev"),
        ('cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl\\Client && npm run build"', "npm run build"),
        ('cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl\\Client && npm run lint"', "npm run lint"),
        ('cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl\\Client && npm run test:coverage"', "npm run test:coverage (kein Wrapper)"),
        # Frontend-Wrapper-Scripts
        ("python3 .claude/scripts/vitest-run.py", "vitest-run.py"),
        ("python3 .claude/scripts/vitest-run.py --filter IngredientsPage", "vitest-run.py --filter"),
        ("python3 .claude/scripts/vitest-run.py --verbose", "vitest-run.py --verbose"),
        ("python3 .claude/scripts/playwright-test.py", "playwright-test.py"),
        ("python3 .claude/scripts/playwright-test.py --filter ingredients", "playwright-test.py --filter"),
        ("python3 .claude/scripts/stryker-frontend.py", "stryker-frontend.py"),
        ("python3 .claude/scripts/stryker-frontend.py --mutate src/pages/IngredientsPage.tsx", "stryker-frontend.py --mutate"),
        ("python3 .claude/scripts/stryker-frontend.py --detail", "stryker-frontend.py --detail"),
        # Compound aus erlaubten Segmenten
        ("ls -la && echo done", "Compound: ls && echo"),
        ("grep foo file | wc -l", "Compound: grep | wc"),
        ("find . -name '*.cs' | grep Endpoint", "Compound: find | grep"),
        ("cat file.txt | tail -20", "Compound: cat | tail"),
        ("git status && git diff", "Compound: git status && git diff"),
        ("ls -la | grep .cs | wc -l", "Compound: ls | grep | wc (3 Segmente)"),
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
        # dotnet ef database drop → deny
        ('cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl && dotnet ef database drop"', "dotnet ef database drop"),
        # dotnet: andere Subcommands nicht erlaubt
        ('cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl && dotnet publish"', "dotnet publish"),
        ('cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl && dotnet format"', "dotnet format"),
        # Falsche Variable → kein Auto-Allow
        (
            'result=$(cmd.exe /c "cd /d C:\\Users\\kieritz\\source\\repos\\mahl && dotnet build")\necho "$result"',
            "Variable-Capture falsche Variable (result statt output)",
        ),
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
        ("npm install", "npm install (nicht über cmd.exe)"),
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
        # taskkill ist destruktiv (in DESTRUCTIVE_PATTERNS)
        ('cmd.exe /c "taskkill /f /im dotnet.exe"', "taskkill ohne Marker"),
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
        ('cmd.exe /c "taskkill /f /im dotnet.exe" # --allow-once', "taskkill mit Marker"),
        ('some-unknown-command --args # --allow-once', "unbekannter Befehl mit Marker"),
        ('npm install # --allow-once', "npm install mit Marker"),
        # Destruktive Befehle: Marker macht sie freigabefähig
        ('rm -rf Client/dist/ # --allow-once', "rm -rf mit Marker → ask"),
        ('rm -r some-directory # --allow-once', "rm -r mit Marker → ask"),
        ('git push --force origin main # --allow-once', "git push --force mit Marker → ask"),
        ('git reset --hard HEAD~1 # --allow-once', "git reset --hard mit Marker → ask"),
        ('git clean -fd # --allow-once', "git clean -fd mit Marker → ask"),
        ('find . -delete # --allow-once', "find -delete mit Marker → ask"),
        ("find . -exec sh -c 'rm -rf {}' \\; # --allow-once", "find -exec sh mit Marker → ask"),
        # WRONG_APPROACH: Marker übersteuert jetzt auch diese
        ('cmd.exe /c "cd /d C:\\mahl && dotnet test" # --allow-once', "dotnet test + Marker → ask"),
        ('git add -f .env # --allow-once', "git add -f + Marker → ask"),
        ('python3 /tmp/script.py # --allow-once', "python3 absoluter Pfad + Marker → ask"),
    ]
    for command, desc in ask_cases:
        if not assert_decision(command, "ask", f"{desc}: {command}"):
            failures += 1

    return failures


def test_deny_overrides_allow() -> int:
    print(f"\n{Colors.BOLD}=== Prioritäten: WRONG_APPROACH / DESTRUCTIVE vs. ALLOW ==={Colors.RESET}")
    failures = 0

    cases = [
        # cmd.exe+dotnet MIT Pipe → deny (nicht allow)
        ('cmd.exe /c "cd /d C:\\mahl && dotnet test" | tail -60', "deny",
         "cmd.exe MIT Pipe → deny"),
        # git add -f schlägt git-add-Allow
        ("git add -f .env", "deny", "git add -f schlägt git-add-allow"),
        # Stryker immer deny → Script verwenden
        ('cmd.exe /c "cd /d C:\\mahl && dotnet stryker"', "deny", "Stryker direkt → deny"),
        # find ohne destruktive Flags → allow; destruktive find-Varianten → deny
        ("find . -name '*.cs'", "allow", "find ohne destruktive Flags → allow"),
        ("find . -delete", "deny", "find -delete → deny (freigabefähig)"),
        ("find . -exec sh -c 'rm -rf {}' \\;", "deny", "find -exec sh → deny"),
        # rm einzelne Datei → allow; rm -rf → deny (nicht allow)
        ("rm file.ts", "allow", "rm einzelne Datei → allow"),
        ("rm -rf /tmp", "deny", "rm -rf → deny (freigabefähig)"),
        # git add ohne -f → allow (negativfilter explizit im Pattern)
        ("git add src/Foo.cs", "allow", "git add ohne -f → allow"),
        ("git add -f .env", "deny", "git add -f → deny (WRONG_APPROACH)"),
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

    print(f"\n{'=' * 60}")
    if total_failures == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}Alle Tests bestanden!{Colors.RESET}")
    else:
        print(f"{Colors.RED}{Colors.BOLD}{total_failures} Test(s) fehlgeschlagen!{Colors.RESET}")
    sys.exit(1 if total_failures > 0 else 0)


if __name__ == "__main__":
    main()
