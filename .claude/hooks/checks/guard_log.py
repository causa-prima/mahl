"""Auslöse-Protokoll der Guards – wer hat wann angeschlagen?

**Wozu.** Ein Guard, der nicht mehr prüft, was er prüfen soll, fällt lautlos aus: Sein Ausfall
löst per Definition nichts aus. Kein Test findet das, denn Tests prüfen, was jemand als
Fehlerfall vorhergesehen hat. Die Frage „hat dieser Guard je gefeuert?" braucht dieses
Vorwissen nicht – und ein Guard ohne jede Auslösung ist entweder kaputt oder überflüssig.
Beides will man wissen.

**Warum selbst protokollieren und nicht rückwirkend aus den Session-Logs lesen.** Geprüft und
verworfen (S128): Die Attachment-Records erfassen blockierende PreToolUse-Meldungen gar nicht –
Bash-Denies kamen 155-mal in den Logs vor und 0-mal in den Attachments. Eine Textsuche über
alle Records bräuchte je Guard eine Signatur, die man raten müsste; die naheliegenden Wörter
treffen Fließtext statt Auslösungen („ADR" 5.207-mal). Der Guard selbst dagegen kennt seine
Identität sicher.

**Fail-open, zwingend.** Das Protokoll ist Beiwerk. Ein Schreibfehler darf niemals einen
blockierenden Guard mitreißen – sonst beschädigt die Messung den Mechanismus, den sie
überwachen soll.
"""
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

# Neben `allowed-commands.log` / `denied-commands.log`, die der Bash-Hook seit S085 führt –
# derselbe Ort, dieselbe Aufgabe. Nicht versioniert: Das Protokoll wächst und beschreibt die
# Maschine, nicht das Projekt.
LOG = Path(__file__).resolve().parents[3] / ".claude" / "tmp" / "guard-triggers.jsonl"


def protokolliere(guard: str) -> None:
    """Eine Auslösung anhängen. Schluckt jeden Fehler – siehe Modul-Docstring."""
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        zeile = json.dumps({"ts": datetime.now().isoformat(timespec="seconds"),
                            "guard": guard}, ensure_ascii=False)
        with LOG.open("a", encoding="utf-8") as f:
            f.write(zeile + "\n")
    except Exception:  # noqa: BLE001 – Beiwerk darf den Guard nie mitreißen
        pass


def _eintraege() -> list[dict]:
    """Alle lesbaren Einträge. Eine kaputte Zeile (abgebrochener Schreibvorgang) darf den
    übrigen Bestand nicht unlesbar machen."""
    if not LOG.is_file():
        return []
    treffer = []
    for zeile in LOG.read_text(encoding="utf-8").splitlines():
        try:
            rec = json.loads(zeile)
        except Exception:  # noqa: BLE001
            continue
        if isinstance(rec, dict) and rec.get("guard"):
            treffer.append(rec)
    return treffer


def zaehlstand() -> dict[str, int]:
    """Auslösungen je Guard."""
    return dict(Counter(rec["guard"] for rec in _eintraege()))


def beobachtet_seit() -> str | None:
    """Zeitstempel des ältesten Eintrags – ohne ihn ist „nie gefeuert" wertlos.

    Am ersten Tag hat kein Guard gefeuert; ein Report, der das nicht dazusagt, meldet die
    eigene Jugend als Befund über die Guards.
    """
    stempel = sorted(rec.get("ts", "") for rec in _eintraege() if rec.get("ts"))
    return stempel[0] if stempel else None
