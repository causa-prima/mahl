"""Einheitliche Ausgabe-Politik der Wrapper-Scripts.

Regel: **Im Erfolgsfall genügt das Verdikt.** Im Fehlerfall nur das, was zur Analyse nötig ist.
Alles Weitere hinter `--verbose`.

Hintergrund (S109): In ~83 % von 517 protokollierten Wrapper-Läufen wurde die ohnehin schon
kuratierte Ausgabe nachträglich per `| tail`/`| grep` gekürzt. Der Reihenfolge-Test über die
Session-Transkripte zeigt, dass das kaum eine Reaktion auf zu langen Output ist – in 11 von 19
Kontexten wurde von Anfang an gefiltert, ohne je einen ungefilterten Lauf gesehen zu haben.
Die Konsequenz daraus ist trotzdem dieselbe: Je kürzer der Erfolgsfall, desto weniger geht
verloren, wenn jemand blind die letzten N Zeilen abschneidet – und desto sicherer steht das
Verdikt am Ende, wo `tail` es findet.

Fail-open-Prinzip: Erkennt ein Wrapper sein erwartetes Muster nicht, gibt er die bisherige,
längere Ausgabe aus. Ein Parser-Fehlgriff darf niemals Information verschlucken.
"""
import re

# npm-interne Zeilen ohne Informationswert für den Aufrufer.
NPM_NOISE = re.compile(r"^> mahl-client@|^> \S|^npm (warn|error notice)|^Using config from")

VERBOSE_HINT = "   (vollständiger Output: --verbose)"


def strip_noise(output: str, extra: re.Pattern[str] | None = None) -> list[str]:
    """Entfernt Tool-/npm-Rauschen und führende/abschließende Leerzeilen."""
    lines = [
        line for line in output.splitlines()
        if not NPM_NOISE.match(line) and not (extra and extra.search(line))
    ]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


# Zeilen, die bei einem fehlgeschlagenen Lauf tatsächlich zur Diagnose beitragen.
_ERROR_SIGNAL = re.compile(
    r"\b(error|fehler|exception|failed|failure|crash|unhandled|cannot|could not|"
    r"WRN|ERR|FAIL)\b", re.IGNORECASE
)


def error_lines(lines: list[str], *, verbose: bool = False, fallback_tail: int = 30,
                limit: int = 25) -> list[str]:
    """Wählt aus einem Roh-Log die diagnose-relevanten Zeilen aus.

    Findet sich kein einziges Fehlersignal, werden die letzten `fallback_tail` Zeilen
    zurückgegeben – fail-open: lieber zu viel als eine verschluckte Ursache.
    """
    if verbose:
        return lines
    hits = [line for line in lines if _ERROR_SIGNAL.search(line)]
    if not hits:
        return lines[-fallback_tail:]
    return hits[-limit:]


def emit(*, verbose: bool, output: str, verdict: str, details: list[str] | None = None) -> None:
    """Gibt die Wrapper-Ausgabe nach der oben beschriebenen Politik aus.

    verbose → der vollständige rohe Output. Sonst: `verdict`, danach optionale `details`
    (im Fehlerfall die analyse-relevanten Zeilen).
    """
    if verbose:
        print(output.rstrip())
        return
    if details:
        print("\n".join(details))
        print()
    print(verdict)
    print(VERBOSE_HINT)
