"""Felder mit festem Wertebereich, die mehrere Tracker teilen – eine Prüfung statt einer je Datei.

Hier liegt, was Erfassungs-Scripte UND Capture-Hooks gleich prüfen müssen. Beide Wege führen
in dieselbe Datei; prüfte nur einer, wäre die Regel über den anderen umgehbar.

**Aufschubgrund** (OBS, TD, OQ): Ein Eintrag verschiebt Arbeit in die Zukunft. Der Normalfall
ist das Gegenteil – ein verstandener Befund, dessen Behebung der Agent selbst entscheiden kann,
wird sofort behoben (LL-S128-3, LL-S129-3: zweimal erfasst, beide Male in Minuten erledigt,
nachdem der User nachfragte). Das Feld erzwingt die Frage im Moment der Erfassung, weil nur
dort jede Erfassung vorbeikommt – mitten in der Session wie beim Abschluss. Zulässig sind
genau drei Gründe; „die Entscheidung steht mir nicht zu" gehört bewusst nicht dazu, denn dann
wird der User gefragt – und erst sein „später" ist ein Grund (`User`).

**Quelle** (OBS, LL): Freitext ließ „Agent" durch, ein Wert ohne definierte Bedeutung.
"""
import re

AUFSCHUB_FELD = "Aufschubgrund"
AUFSCHUB_WERTE = {
    "User": "der User hat „später“ entschieden (vorher gefragt, nicht angenommen)",
    "Umfang": "die Behebung sprengt den Fokus der Session",
    "Recherche": "den Befund zu verstehen braucht viele Schritte oder viel Zeit",
}
AUFSCHUB_HILFE = (
    "PFLICHT: warum erfasst statt sofort behoben – '<Wert> – <konkreter Grund>'. Werte: "
    + "; ".join(f"{k} ({v})" for k, v in AUFSCHUB_WERTE.items())
    + ". Trifft keiner zu: beheben. Steht die Behebung dir nicht zu: den User fragen.")
_AUFSCHUB_RE = re.compile(rf"^({'|'.join(AUFSCHUB_WERTE)})\s+[–—-]\s+(\S.*)$")

QUELLE_WERTE = ("User", "Orchestrator", "Subagent")
# Ein Klammerzusatz trägt Information ("Subagent (security-auditor)") und bleibt erlaubt.
_QUELLE_TEIL_RE = re.compile(rf"^({'|'.join(QUELLE_WERTE)})( \([^()]+\))?$")

# Schlüsselwörter, nach denen obs-drain, obs_parse und obs-archive filtern. `IN BEOBACHTUNG`
# braucht den Termin: ohne ihn meldet obs_parse nur eine Warnung, und die Wiedervorlage fällt aus.
_OBS_STATUS_RE = re.compile(r"^(NEU|UMGESETZT|VERWORFEN|IN BEOBACHTUNG bis S\d+)\b")


def pruefe_aufschubgrund(wert: str) -> str:
    wert = (wert or "").strip()
    if _AUFSCHUB_RE.match(wert):
        return wert
    gruende = "\n".join(f"  {k} – {v}" for k, v in AUFSCHUB_WERTE.items())
    raise ValueError(
        f"{AUFSCHUB_FELD}: '{wert}' trägt nicht. Form: '<Wert> – <konkreter Grund>'. "
        f"Zulässige Werte:\n{gruende}\n"
        f"Trifft keiner zu, wird nicht erfasst, sondern behoben – ist die Behebung nicht deine "
        f"Entscheidung, frag den User.")


def fett_feldwert(block: str, feld: str) -> str | None:
    """Wert einer `**Feld:**`-Zeile (TD, OQ) – None, wenn das Feld fehlt.

    Eine Stelle für beide Capture-Hooks: Zwei Kopien desselben Musters liefen bei einer
    Formatänderung auseinander, und die vergessene prüfte still das Falsche.
    """
    treffer = re.search(rf"^\*\*{re.escape(feld)}:\*\*(.*)$", block, re.M)
    return treffer.group(1).strip() if treffer else None


def aufschub_verstoss(wert: str | None) -> str | None:
    """Für die Capture-Hooks: Begründung als Text statt Ausnahme (None = trägt)."""
    if wert is None:
        return f"Pflichtfeld `{AUFSCHUB_FELD}` fehlt – warum erfasst statt behoben?"
    try:
        pruefe_aufschubgrund(wert)
    except ValueError as fehler:
        return str(fehler)
    return None


def pruefe_quelle(wert: str, kombinierbar: bool) -> str:
    wert = (wert or "").strip()
    teile = [t.strip() for t in wert.split(" + ")] if kombinierbar else [wert]
    if all(_QUELLE_TEIL_RE.match(t) for t in teile):
        return wert
    form = " (kombinierbar mit ' + ')" if kombinierbar else ""
    raise ValueError(f"Quelle: '{wert}' ist nicht zulässig. Erlaubt: "
                     f"{' | '.join(QUELLE_WERTE)}{form}, optional mit Zusatz in Klammern.")


def pruefe_obs_status(wert: str) -> str:
    wert = (wert or "").strip()
    if _OBS_STATUS_RE.match(wert):
        return wert
    raise ValueError(
        f"Status: '{wert}' beginnt mit keinem bekannten Schlüsselwort. Erlaubt: NEU | "
        f"UMGESETZT (…) | VERWORFEN (…) | IN BEOBACHTUNG bis S<NNN> – Drain und Archiv "
        f"filtern danach, ein anderer Wert fiele dort still heraus.")
