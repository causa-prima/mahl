#!/usr/bin/env python3
"""
Guard-Auslösungen: Welcher Prüfmechanismus hat je angeschlagen?

Verwendung:
  python3 .claude/scripts/guard-stats.py

**Wozu.** Ein Guard ohne jede Auslösung ist entweder kaputt oder überflüssig – von außen nicht
zu unterscheiden, weshalb dieser Report den Befund meldet, statt ihn zu deuten. Warum die Frage
„hat er je gefeuert?" die einzige ist, die ohne Vorwissen über die Fehlerart auskommt: siehe
`checks/guard_log.py`.

**Was er NICHT abdeckt.** Der Bash-Hook führt sein eigenes Protokoll seit S085
(`allowed-commands.log` / `denied-commands.log`); dessen Auswertung ist `tool-usage.py`. Hier
stehen die Guards der beiden Edit/Write-Dispatcher.

**Die Liste der Guards wird gelesen, nicht gepflegt** – aus den Dispatchern selbst. Eine
gepflegte Kopie driftet, und zwar in die gefährliche Richtung: Sie sähe weiterhin vollständig
aus, während ein neuer Guard fehlt.
"""
import os
import sys
from importlib import import_module
from pathlib import Path

HOOKS = Path(__file__).resolve().parent.parent / "hooks"
sys.path.insert(0, str(HOOKS))
sys.path.insert(0, os.path.dirname(__file__))

# noqa E402: Der Import kann nicht nach oben – `checks` liegt unter `.claude/hooks`, und der
# Pfad dorthin wird eine Zeile darüber gesetzt. Dasselbe Muster wie in den Hooks selbst.
from checks import guard_log  # noqa: E402

MARKE_STUMM = "← nie gefeuert"
MARKE_UNBEKANNT = "(nicht mehr definiert)"

# Unterhalb dieser Zahl sagt „nie gefeuert" nichts über den Guard, sondern nur über das Alter
# des Protokolls. Die Schwelle ist eine Setzung, kein gemessener Wert – sie soll verhindern,
# dass der Report am ersten Tag einen Fehlbefund produziert, nicht eine Signifikanz behaupten.
GENUG_AUSLOESUNGEN = 100

HINWEIS_DUENN = ("Noch zu wenige Auslösungen: 'nie gefeuert' ist hier eine Aussage über das "
                 "Alter des Protokolls, nicht über den Guard.")


def definierte_guards() -> dict[str, str]:
    """{Guard-Name: Dispatcher} – aus den Dispatchern gelesen."""
    namen: dict[str, str] = {}

    blockierend = import_module("dispatch-edit-write")
    for name in blockierend.CHECKS:
        namen[name] = "blockierend (dispatch-edit-write)"

    nichtblockierend = import_module("check-code-quality-nonblocking")
    for fn in nichtblockierend.CHECKS:
        namen[fn.__module__.rsplit(".", 1)[-1]] = "Hinweis (check-code-quality-nonblocking)"

    return namen


def bericht(zaehlstand: dict[str, int], seit: str | None) -> list[str]:
    definiert = definierte_guards()
    gesamt = sum(zaehlstand.values())

    if not zaehlstand:
        return ["Guard-Auslösungen: noch keine protokolliert.",
                f"  {len(definiert)} Guards sind registriert; das Protokoll beginnt mit der "
                f"ersten Auslösung."]

    zeilen = [f"Guard-Auslösungen – beobachtet seit {seit} ({gesamt} Auslösungen)", ""]

    nach_gruppe: dict[str, list[str]] = {}
    for name, gruppe in sorted(definiert.items()):
        nach_gruppe.setdefault(gruppe, []).append(name)

    stumme = 0
    for gruppe, namen in sorted(nach_gruppe.items()):
        zeilen.append(f"{gruppe}:")
        for name in namen:
            n = zaehlstand.get(name, 0)
            marke = f"  {MARKE_STUMM}" if n == 0 else ""
            if n == 0:
                stumme += 1
            zeilen.append(f"  {n:6}  {name}{marke}")
        zeilen.append("")

    # Auslösungen ohne zugehörigen Guard: umbenannt oder gelöscht. Nicht verschlucken – sonst
    # zählt der Report Ereignisse, die er niemandem zuordnet, und die Summe stimmt scheinbar.
    verwaist = sorted(set(zaehlstand) - set(definiert))
    if verwaist:
        zeilen.append(f"Im Protokoll, aber {MARKE_UNBEKANNT}:")
        zeilen += [f"  {zaehlstand[name]:6}  {name}" for name in verwaist]
        zeilen.append("")

    if stumme:
        zeilen.append(f"{stumme} Guard(s) ohne Auslösung.")
        if gesamt < GENUG_AUSLOESUNGEN:
            zeilen.append(f"  {HINWEIS_DUENN}")
        else:
            zeilen.append("  Jeder davon ist entweder kaputt oder überflüssig – beides gehört "
                          "geprüft, nicht angenommen.")
    return zeilen


def main() -> int:
    for zeile in bericht(guard_log.zaehlstand(), guard_log.beobachtet_seit()):
        print(zeile)
    return 0


if __name__ == "__main__":
    sys.exit(main())
