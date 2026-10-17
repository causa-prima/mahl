#!/usr/bin/env python3
"""PreToolUse-Poka-Yoke (blockierend): kein toter Abschnitts-Verweis, kein gelöschter Anker
mit verbliebenen Verweisen.

Warum (OBS-S112-7): Verweise zwischen Projektdokumenten standen als Prosa – „§2",
„Sektion Security", „Schritt 4". Kein Werkzeug konnte prüfen, ob das Ziel existiert, und weil
sie auf Nummern zeigten, mussten die Nummern stabil bleiben (daher Einschübe wie `4b`/`4c`).
Das Anker-Schema löst Identität von Position; dieser Hook hält es aufrecht.

Zwei Richtungen, beide nötig – eine allein wäre ein stummes Opt-out:
  1. **Vorwärts:** Ein Verweis `CGT-xyz` ohne definierten Anker wird beim Schreiben geblockt.
  2. **Rückwärts:** Verschwindet ein Anker, auf den noch verwiesen wird, wird das geblockt.
Dieselbe Überlegung wie in `check-dangling-refs.py` für volatile Tracker-IDs, und dieselbe
Bauform wie `check-ref-direction.py`: Regel in `principles.md`, Durchsetzung hier.

Scope: Markdown im Repo, ausgenommen `docs/history/` und `docs/kaizen/archive/` – dort ist ein
Verweis auf einen Zustand von damals korrekt und soll stehen bleiben. Ohne diese Ausnahme
erzeugte allein die Historie über hundert Falschmeldungen und der Hook wäre unbenutzbar.

Zeilen-Ausnahme: `anchor-ok` in der betreffenden Zeile (bewusst offener Verweis, z.B. ein
Beispiel im Fließtext, das kein reales Ziel hat).

Mechanik: PreToolUse läuft VOR der Anwendung; der Hook simuliert den Post-Edit-Inhalt.
Fail-open: ein Hook-eigener Fehler blockt nie einen Edit.
"""
from pathlib import Path


from ._hook_io import edit_zustand
from .. import anchors

_ANCHOR_OK = "anchor-ok"
_MAX_HITS = 25


def betrifft(file_path: str) -> bool:
    """Dieselbe Regel, die auch die CLI anwendet – bewusst nicht nachgebaut."""
    try:
        rel = Path(file_path).resolve().relative_to(anchors.REPO_ROOT).as_posix()
    except ValueError:
        return False
    return anchors.wird_geprueft(rel)


def _ohne_ausnahmen(text: str) -> str:
    """Zeilen mit `anchor-ok` leeren, damit ihre Verweise nicht mitgeprüft werden – geleert,
    nicht entfernt: Sonst nennte die Meldung für jeden späteren Verweis eine falsche Zeile."""
    return "\n".join("" if _ANCHOR_OK in z else z for z in text.splitlines())


def check(data: dict) -> str | None:
    """Dispatcher-Einstieg: Blockier-Grund oder None. Siehe dispatch-edit-write.py."""
    zustand = edit_zustand(data, betrifft)
    if zustand is None:
        return None
    file_path, pre, post = zustand

    rel = Path(file_path).resolve().relative_to(anchors.REPO_ROOT).as_posix()
    bestand = anchors.lies_bestand()
    andere = {d: t for d, t in bestand.items() if d != rel}

    # Rückwärts zuerst: Das Löschen eines Ankers ist der teurere Fehler – der Verweis steht
    # dann in einer FREMDEN Datei und fällt erst auf, wenn ihm jemand folgt.
    verwaist = anchors.verwaiste(pre, _ohne_ausnahmen(post), andere)
    if verwaist:
        zeilen = "\n".join(
            f"  - `{anker}` ← " + ", ".join(f"{d}:{n}" for d, n in stellen[:_MAX_HITS])
            for anker, stellen in verwaist)
        return f"{_KOPF_VERWAIST}{zeilen}\n{_HINWEIS_VERWAIST}"

    # Vorwärts: Verweise dieser Datei, deren Ziel nirgends definiert ist.
    geprueft = {**andere, rel: _ohne_ausnahmen(post)}
    bekannt = set(anchors.index(geprueft))
    tot = [(ziel, nr) for ziel, nr, _p in anchors.verweise_aus(rel, _ohne_ausnahmen(post))
           if ziel not in bekannt]
    if tot:
        zeilen = "\n".join(f"  - Zeile {nr}: `{ziel}`" for ziel, nr in tot[:_MAX_HITS])
        mehr = _MEHR.format(n=len(tot) - _MAX_HITS) if len(tot) > _MAX_HITS else ""
        return f"{_KOPF_TOT.format(n=len(tot))}{zeilen}{mehr}\n{_HINWEIS_TOT}"

    # Pfad: Der Anker existiert, aber nicht in der verlinkten Datei. Ohne diese Prüfung
    # meldete der Hook „alles gut", während der Klick ins Leere ginge – und Klickbarkeit ist
    # der Grund für das Link-Format.
    falsch = [f for f in anchors.falsche_pfade(geprueft) if f[0] == rel]
    if not falsch:
        return None
    zeilen = "\n".join(
        f"  - Zeile {nr}: `{ziel}` verlinkt {gemeint}, liegt aber in {echt}"
        for _d, nr, ziel, gemeint, echt in falsch[:_MAX_HITS])
    return f"{_KOPF_FALSCH.format(n=len(falsch))}{zeilen}\n{_HINWEIS_FALSCH}"


_KOPF_VERWAIST = ("❌ Anker-Verweise (Poka-Yoke): Ein Anker soll verschwinden, auf den noch "
                  "verwiesen wird:\n")
_HINWEIS_VERWAIST = (
    "  Der Anker trägt die Identität des Abschnitts – ohne ihn ist der Verweis von "
    "außen nicht mehr auflösbar.\n"
    "  Pass zuerst die Fundstellen an (auf den neuen Anker umhängen oder den Verweis "
    "auflösen), dann den Anker entfernen.\n"
    f"  Bewusst offener Verweis → `{_ANCHOR_OK}` in die betreffende Zeile."
)
_KOPF_TOT = "❌ Anker-Verweise (Poka-Yoke): {n} Verweis(e) ohne Ziel:\n"
_MEHR = "\n  … und {n} weitere"
_HINWEIS_TOT = (
    '  Ein Anker wird als `<a id="ANKER"></a>` über der Überschrift definiert und als '
    "`[ANKER](pfad/datei.md#ANKER)` referenziert; Bestand: "
    "`python3 -m prozesscode.anchors list`.\n"
    "  Entweder ist der Zielabschnitt noch nicht mit einem Anker versehen, oder der "
    "Verweis ist vertippt.\n"
    f"  Bewusst offener Verweis (Beispiel im Fließtext) → `{_ANCHOR_OK}` in die Zeile."
)
_KOPF_FALSCH = "❌ Anker-Verweise (Poka-Yoke): {n} Link(s) auf die falsche Datei:\n"
_HINWEIS_FALSCH = (
    "  Der Anker existiert, aber nicht dort – der Klick geht ins Leere, obwohl der "
    "Verweis auflösbar aussieht.\n"
    "  Pfad ist relativ zur verweisenden Datei. Fundort: "
    "`python3 -m prozesscode.anchors list`."
)
