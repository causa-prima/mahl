"""PostToolUse-Check (nicht-blockierend): Warnung bei neuen Mengenangaben in Prosa.

„alle vier Agenten" veraltet still, sobald die gezählte Menge anderswo definiert ist und
wächst. Bis S133 wurde die Klasse nur stumm in ein Log geschrieben (Beschluss S124: erst messen,
dann scharf schalten oder streichen) – ausgewertet hat das Log niemand. Die Sichtung in S133
ergab 2 echte von 20 Treffern: für einen Block viel zu wenig, für einen Hinweis genug, denn
nur der Autor weiß im Moment des Schreibens billig, ob die Menge anderswo definiert ist.

Das Log bleibt: Jede Warnung wird mit Datum festgehalten. Einträge ohne Datum stammen aus der
stummen Phase davor. Ob Warnungen wirken, zeigt sich später daran, ob die gewarnte Formulierung
geändert wurde – dieselbe Frage, die `guard-stats` für die Auslösung beantwortet.
"""
import datetime
import subprocess
from pathlib import Path

from ... import anchors, ordinale
from .common import HookInput

LOG = anchors.REPO_ROOT / ".claude" / "tmp" / "mengenangaben.log"
_MAX_TREFFER = 5

# Zählungen sind dort Momentaufnahmen einer Retro oder eines Drains und stimmen per Natur –
# in S133 waren 13 der 20 Treffer genau solche Sätze. `docs/history/` und das Kaizen-Archiv
# schließt `anchors.wird_geprueft` bereits aus.
CHRONIKEN = frozenset({"docs/kaizen/countermeasures.md", "docs/kaizen/observations.md",
                       "docs/kaizen/lessons_learned.md"})


def _rel(file_path: str) -> str | None:
    try:
        return Path(file_path).resolve().relative_to(anchors.REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return None


def _zustaendig(rel: str | None) -> bool:
    return (rel is not None and rel not in CHRONIKEN and anchors.wird_geprueft(rel)
            and "ordinal" not in anchors.ausnahmen_fuer(rel))


def _stand_in_git(rel: str) -> str:
    """Vorher-Stand für Write, das die ganze Datei ersetzt. Unversioniert → leer (alles neu)."""
    try:
        lauf = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=anchors.REPO_ROOT,
                              capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return ""
    return lauf.stdout if lauf.returncode == 0 else ""


def _ausschnitt(zeile: str, fund: str, breite: int = 160) -> str:
    """Fenster um die Fundstelle: Doku-Zeilen sind länger als das Log-Fenster."""
    start = zeile.find(fund)
    if start < 0 or len(zeile) <= breite:
        return zeile[:breite]
    rand = max(0, (breite - len(fund)) // 2)
    links, rechts = max(0, start - rand), min(len(zeile), start + len(fund) + rand)
    return ("…" if links else "") + zeile[links:rechts] + ("…" if rechts < len(zeile) else "")


def _protokolliere(rel: str, funde: list[tuple[int, str, str]]) -> None:
    """Fail-open: Ein Schreibfehler darf die Warnung nie verschlucken."""
    heute = datetime.date.today().isoformat()
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with LOG.open("a", encoding="utf-8") as f:
            for _nr, zeile, fund in funde:
                f.write(f"{rel}\t{fund}\t{_ausschnitt(zeile, fund)}\t{heute}\n")
    except OSError:
        pass


def check(inp: HookInput) -> list[str]:
    rel = _rel(inp.file_path)
    if not _zustaendig(rel):
        return []
    vorher = inp.old_content if inp.tool == "Edit" else _stand_in_git(rel)
    funde = ordinale.neue_mengenangaben(vorher, inp.new_content)
    if not funde:
        return []
    _protokolliere(rel, funde)
    zeilen = "\n".join(f"  - „{fund}“ in: {_ausschnitt(zeile, fund, 90)}"
                       for _nr, zeile, fund in funde[:_MAX_TREFFER])
    return [f"ℹ️ Mengenangabe in {rel} – veraltet still, wenn die gezählte Menge anderswo "
            f"definiert ist und wächst:\n{zeilen}\n"
            f"  Steht die Menge im selben Satz oder ist die Zahl eine Momentaufnahme: nichts zu "
            f"tun. Ist sie anderswo definiert: Zahl weglassen („alle Agenten“) oder auf die "
            f"Quelle verweisen. Bewusst so gewollt: `ordinal-ok` in die Zeile."]
