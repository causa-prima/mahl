"""Test-Pattern-Check: Partielle Assertions statt Full-State-Check (BeEquivalentTo)."""
import re
from .common import HookInput

PARTIAL_ASSERTION_PATTERNS = [
    (re.compile(r'\.Should\(\)\.HaveCount\('), "`.Should().HaveCount(...)`"),
    (re.compile(r'\.Should\(\)\.ContainSingle\('), "`.Should().ContainSingle(...)`"),
    (re.compile(r'\.Should\(\)\.NotBeEmpty\('), "`.Should().NotBeEmpty()`"),
    (re.compile(r'\.Should\(\)\.NotContain\('), "`.Should().NotContain(...)`"),
]
CONTAIN_PATTERN = re.compile(r'\.Should\(\)\.Contain\(')
EXCLUDING_MISSING_MEMBERS_PATTERN = re.compile(r'ExcludingMissingMembers\(')

TEST_FILE_PATTERN = re.compile(
    r'[/\\]Server\.Tests[/\\].+\.cs$'
)


def _new_occurrences(pattern: re.Pattern, new: str, old: str) -> int:
    return max(0, len(pattern.findall(new)) - len(pattern.findall(old)))


def _is_new(pattern: re.Pattern, inp: HookInput) -> bool:
    if inp.tool == "Edit":
        return _new_occurrences(pattern, inp.new_content, inp.old_content) > 0
    return bool(pattern.search(inp.new_content))


def check(inp: HookInput) -> list[str]:
    if not TEST_FILE_PATTERN.search(inp.file_path):
        return []

    messages = []

    partial_hits = [label for pat, label in PARTIAL_ASSERTION_PATTERNS if _is_new(pat, inp)]
    if partial_hits:
        found = ", ".join(partial_hits)
        messages.append(
            f"Test-Pattern-Hinweis: {found} erkannt.\n"
            "Pruefe ob `.Should().BeEquivalentTo(expected)` die vollstaendigere Assertion waere\n"
            "(Full-State-Assertion statt partieller Zaehlung).\n"
            "Siehe ARCHITECTURE.md (Test-Patterns)."
        )

    if _is_new(CONTAIN_PATTERN, inp):
        messages.append(
            "`.Should().Contain(...)` ist eine partielle Assertion.\n"
            "Fuer exakte String-Werte: `.Should().Be(exactString)` verwenden.\n"
            "Fuer JSON-Response-Bodies: `ReadFromJsonAsync<T>()` + typisierte Assertion verwenden."
        )

    if _is_new(EXCLUDING_MISSING_MEMBERS_PATTERN, inp):
        messages.append(
            "ExcludingMissingMembers() ist verboten.\n"
            "In Integrationstests: ID aus DB holen (GetAllXxxFromDb()) und vollstaendig vergleichen.\n"
            "Falls eine Property genuinen Ignorierungsgrund hat: o.Excluding(x => x.PropName) verwenden."
        )

    return messages
