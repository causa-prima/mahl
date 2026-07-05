"""Kaizen-Retro-Bericht aus lessons_learned.md + Archiv.

Aufruf:
  python .claude/scripts/retro_report.py [--current <pfad>] [--archive <dir>] [--cm <pfad>] [--verbose]

Standard-Output (Agenten-Modus, retro-relevant):
  1. Aktuelle Periode – Aggregationstabelle
  2. Sonstiges-Einträge (Tag-Pflege)
  6. Pattern-Kandidaten (aktuelle Periode + letzte 3 Archiv-Sessions)
  9. Eskalierte Maßnahmen

Nur mit --verbose (visuell / für Menschen):
  3. Zeitreihen – Gesamt-Chart (logarithmische Zeitachse, blau)
  4. Kategorie-Stack – farbiger gestapelter Chart (gleiche Zeitachse)
  5. Heatmap (Session × Kontext)
  7. Semantisches Clustering (sklearn optional, alle offenen Einträge)
  8. Trendanalyse per Kategorie
"""

import argparse
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kaizen_constants import IMPACT_WEIGHTS
from _util import REPO_ROOT

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.cluster import KMeans
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# ---------------------------------------------------------------------------
# ANSI
# ---------------------------------------------------------------------------
RST   = '\033[0m'
BOLD  = '\033[1m'
BLUE  = '\033[34m'
RED   = '\033[31m'
GREEN = '\033[32m'
YLLOW = '\033[33m'

GRAY = '\033[90m'

CAT_COLOR = {'PROZESS': BLUE, 'AGENT': RED, 'QUALITÄT': GREEN, 'TOOLING': YLLOW}
CAT_CHAR  = {'PROZESS': '█',  'AGENT': '▓', 'QUALITÄT': '▒',  'TOOLING': '░'}
CATS      = list(CAT_CHAR.keys())   # stacking order: PROZESS=bottom, TOOLING=top

def cat_block(cat: str) -> str:
    return CAT_COLOR.get(cat, '') + CAT_CHAR.get(cat, '?') + RST

def b(text: str) -> str:
    return BOLD + text + RST

def clr(text: str, color: str) -> str:
    return color + text + RST

# ---------------------------------------------------------------------------
# Konstanten
# ---------------------------------------------------------------------------
DEFAULT_CURRENT = os.path.join(REPO_ROOT, "docs", "kaizen", "lessons_learned.md")
DEFAULT_ARCHIVE = os.path.join(REPO_ROOT, "docs", "kaizen", "archive")
DEFAULT_CM      = os.path.join(REPO_ROOT, "docs", "kaizen", "countermeasures.md")

IMPACT_ORDER  = ["KRITISCH", "HOCH", "MITTEL", "GERING"]
BAND_WIDTH     = 35    # Spalten pro Band
N_BANDS        = 4
MIN_HEIGHT     = 4
PATTERN_WINDOW  = 3     # zusätzliche Archiv-Perioden (Dateien) für Pattern-Kandidaten
TREND_VALUE_W   = 7     # visuelle Spaltenbreite pro Band in der Trendanalyse
MIN_CLUSTER    = 50

HSEP = '═' * 64


# ---------------------------------------------------------------------------
# Datenmodell
# ---------------------------------------------------------------------------
@dataclass
class Finding:
    session_num: int
    impact: str
    kategorie: str
    kontext: str
    titel: str
    was: str = ""
    warum: str = ""


@dataclass
class SessionData:
    num: int
    date: str
    findings: list = field(default_factory=list)


@dataclass
class Countermeasure:
    problem: str
    impact: str
    kategorie: str
    kontexte: list          # leer = Wildcard
    status: str             # OFFEN | AKTIV | BEWÄHRT | IN UMSETZUNG
    seit_session: int = 0
    cm_id: str = ""


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------
SESSION_RE = re.compile(r"^##\s+Session\s+(\d+)\s+[–\-]\s+(\d{4}-\d{2}-\d{2})")
FINDING_RE = re.compile(
    r"^\s*-\s+\*\*\[(?P<impact>KRITISCH|HOCH|MITTEL|GERING)\]\s*"
    r"\[(?P<kategorie>[\w-]+)\]\s*"
    r"\[(?P<kontext>[\w/-]+)\]\s*(?P<titel>.+?)\*\*\s*$"
)
WAS_RE   = re.compile(r"^\s+Was:\s+(.+)")
WARUM_RE = re.compile(r"^\s+Warum:\s+(.+)")

# --- Countermeasure-Parser (Fließtext-Format, OBS-S085-14) ---
# Header:    ### CM-S<NNN>-<n> – Kurztitel
# Metadaten: **Impact:** … | **Kategorie:** … | **Kontext:** … | **Status:** … | **Seit:** S<NNN>
# Problem:   **Problem:** <Text>
CM_HEADER_RE = re.compile(r"^###\s+(?P<id>CM-S\d+-\d+)\s+[–\-]\s+(?P<titel>.+?)\s*$")
CM_META_RE = re.compile(
    r"^\*\*Impact:\*\*\s*(?P<impact>KRITISCH|HOCH|MITTEL|GERING)\s*\|\s*"
    r"\*\*Kategorie:\*\*\s*(?P<kategorie>[\w-]+)\s*\|\s*"
    r"\*\*Kontext:\*\*\s*(?P<kontext>.*?)\s*\|\s*"
    r"\*\*Status:\*\*\s*(?P<status>OFFEN|IN UMSETZUNG|AKTIV|BEWÄHRT)\s*\|\s*"
    r"\*\*Seit:\*\*\s*S?(?P<seit>\d+)"
)
CM_PROBLEM_RE = re.compile(r"^\*\*Problem:\*\*\s*(?P<problem>.+)")


def parse_file(path: str) -> list[SessionData]:
    sessions: list[SessionData] = []
    cur: SessionData | None = None
    cur_f: Finding | None = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = SESSION_RE.match(line)
            if m:
                cur = SessionData(num=int(m.group(1)), date=m.group(2))
                sessions.append(cur)
                cur_f = None
                continue
            if cur is None:
                continue
            m = FINDING_RE.match(line)
            if m:
                cur_f = Finding(
                    session_num=cur.num, impact=m.group("impact"),
                    kategorie=m.group("kategorie"), kontext=m.group("kontext"),
                    titel=m.group("titel").strip(),
                )
                cur.findings.append(cur_f)
                continue
            if cur_f:
                m = WAS_RE.match(line)
                if m: cur_f.was = m.group(1).strip(); continue
                m = WARUM_RE.match(line)
                if m: cur_f.warum = m.group(1).strip()
    return sessions


def load_all(current: str, archive_dir: str) -> list[SessionData]:
    sessions: list[SessionData] = []
    if os.path.exists(current):
        sessions.extend(parse_file(current))
    if os.path.isdir(archive_dir):
        for fname in sorted(os.listdir(archive_dir)):
            if fname.endswith(".md"):
                sessions.extend(parse_file(os.path.join(archive_dir, fname)))
    sessions.sort(key=lambda s: s.num)
    return sessions


def load_archive_periods(archive_dir: str) -> list[list[SessionData]]:
    """Lädt jede Archiv-Datei als eigene Periode (Liste von Sessions), älteste zuerst."""
    periods: list[list[SessionData]] = []
    if os.path.isdir(archive_dir):
        for fname in sorted(f for f in os.listdir(archive_dir) if f.endswith(".md")):
            sessions = parse_file(os.path.join(archive_dir, fname))
            if sessions:
                periods.append(sessions)
    return periods


def total_sessions_from_range(archive_dir: str, current_sessions: list[SessionData]) -> int | None:
    """Berechnet Gesamtanzahl Sessions aus Dateinamen-Range + aktuelle Periode.
    Setzt fortlaufende Session-Nummern voraus. Gibt None zurück wenn kein Archiv-Pattern gefunden."""
    min_num: int | None = None
    if os.path.isdir(archive_dir):
        for fname in os.listdir(archive_dir):
            m = re.match(r"session_(\d+)_to_\d+\.md$", fname)
            if m:
                n = int(m.group(1))
                if min_num is None or n < min_num:
                    min_num = n
    if not current_sessions:
        return None
    max_num = max(s.num for s in current_sessions)
    if min_num is None:
        return len(current_sessions)
    return max_num - min_num + 1


def load_cm(path: str) -> list[Countermeasure]:
    """Parst countermeasures.md im Fließtext-Format (OBS-S085-14).

    Pro Maßnahme: Header (CM-ID + Titel) → Metadaten-Zeile → **Problem:**-Zeile.
    Der Titel dient als Fallback-`problem`, bis die **Problem:**-Zeile ihn überschreibt.
    """
    cms: list[Countermeasure] = []
    if not os.path.exists(path):
        return cms
    cur_id = ""
    cur_titel = ""
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = CM_HEADER_RE.match(line)
            if m:
                cur_id = m.group("id")
                cur_titel = m.group("titel").strip()
                continue
            m = CM_META_RE.match(line)
            if m and cur_id:
                kontext_raw = m.group("kontext").strip()
                kontexte = [] if kontext_raw in ('', '–', '-') else [
                    k.strip() for k in kontext_raw.split(',') if k.strip()
                ]
                cms.append(Countermeasure(
                    cm_id=cur_id, problem=cur_titel,
                    impact=m.group("impact"), kategorie=m.group("kategorie"),
                    kontexte=kontexte, status=m.group("status"),
                    seit_session=int(m.group("seit")),
                ))
                continue
            m = CM_PROBLEM_RE.match(line)
            if m and cms and cms[-1].cm_id == cur_id:
                cms[-1].problem = m.group("problem").strip()
    return cms


# ---------------------------------------------------------------------------
# Countermeasure-Matching
# ---------------------------------------------------------------------------
def cm_matches(cm: Countermeasure, impact: str, kategorie: str, kontext: str) -> bool:
    if cm.impact != impact or cm.kategorie != kategorie:
        return False
    return not cm.kontexte or kontext in cm.kontexte


def is_bewährt(f: Finding, cms: list[Countermeasure]) -> bool:
    return any(cm.status == 'BEWÄHRT' and cm_matches(cm, f.impact, f.kategorie, f.kontext) for cm in cms)


def has_cm(impact: str, kategorie: str, kontext: str, cms: list[Countermeasure]) -> bool:
    return any(cm_matches(cm, impact, kategorie, kontext) for cm in cms)


# ---------------------------------------------------------------------------
# Chart-Hilfsfunktionen
# ---------------------------------------------------------------------------
def compute_bands(n: int) -> list[tuple[int, int]]:
    """Logarithmische Bänder (start, end), ältestes zuerst. Jedes Band = 2× mehr Sessions als das rechts daneben."""
    if n == 0:
        return []
    nb = min(N_BANDS, n)
    total_units = (2 ** nb) - 1
    sizes: list[int] = []
    remaining = n
    for i in range(nb):
        if i == nb - 1:
            sizes.append(remaining)
        else:
            s = max(1, round(n / total_units * (2 ** i)))
            s = min(s, remaining - (nb - 1 - i))
            sizes.append(s)
            remaining -= s
    # sizes[0]=neuestes, sizes[-1]=ältestes; aufbauen von rechts
    bands: list[tuple[int, int]] = []
    end = n
    for s in sizes:
        bands.append((end - s, end))
        end -= s
    bands.reverse()
    return bands


def col_avgs(values: list[float], bands: list[tuple[int, int]]) -> list[list[float]]:
    result = []
    for start, end in bands:
        n = end - start
        cols = []
        for col in range(BAND_WIDTH):
            lo = int(start + col * n / BAND_WIDTH)
            hi = min(int(start + (col + 1) * n / BAND_WIDTH) + 1, end)
            sub = values[lo:hi]
            cols.append(sum(sub) / len(sub) if sub else 0.0)
        result.append(cols)
    return result


def col_cat_avgs(cat_counts: list[dict], bands: list[tuple[int, int]]) -> list[list[dict]]:
    result = []
    for start, end in bands:
        n = end - start
        cols = []
        for col in range(BAND_WIDTH):
            lo = int(start + col * n / BAND_WIDTH)
            hi = min(int(start + (col + 1) * n / BAND_WIDTH) + 1, end)
            sub = cat_counts[lo:hi]
            if sub:
                d = {c: sum(s.get(c, 0) for s in sub) / len(sub) for c in CATS}
            else:
                d = {c: 0.0 for c in CATS}
            cols.append(d)
        result.append(cols)
    return result


def axis_lines(sessions: list[SessionData], bands: list[tuple[int, int]]) -> list[str]:
    nb = len(bands)
    sep = "  └" + ("─" * BAND_WIDTH + "┴") * (nb - 1) + "─" * BAND_WIDTH
    parts = []
    for start, end in bands:
        n = end - start
        s0, se = sessions[start].num, sessions[end - 1].num
        rng = f"S{s0}" if s0 == se else f"S{s0}-{se}"
        count = f"{n} Session" if n == 1 else f"{n} Sessions"
        label = f"{rng} ({count})"
        parts.append(label[:BAND_WIDTH].ljust(BAND_WIDTH))
    return [sep, "   " + "│".join(parts)]


def render_gesamt_chart(
    sessions: list[SessionData],
    bands: list[tuple[int, int]],
    title: str,
) -> list[str]:
    totals = [float(sum(IMPACT_WEIGHTS.get(f.impact, 0) for f in s.findings)) for s in sessions]
    band_data = col_avgs(totals, bands)
    max_h = max(MIN_HEIGHT, int(max((v for cols in band_data for v in cols), default=0)) + 1)
    lines = [b(f"  {title}"), ""]
    for row in range(max_h, 0, -1):
        line = f"{row:2d}│"
        for bi, cols in enumerate(band_data):
            if bi > 0:
                line += '│'
            for avg in cols:
                line += (BLUE + '█' + RST) if avg >= row - 0.5 else ' '
        lines.append(line)
    lines += axis_lines(sessions, bands)
    return lines


def render_stack_chart(
    sessions: list[SessionData],
    bands: list[tuple[int, int]],
    title: str,
) -> list[str]:
    cat_counts = [
        {c: sum(IMPACT_WEIGHTS.get(f.impact, 0) for f in s.findings if f.kategorie == c) for c in CATS}
        for s in sessions
    ]
    band_data = col_cat_avgs(cat_counts, bands)
    max_h = max(
        MIN_HEIGHT,
        int(max((sum(d.values()) for cols in band_data for d in cols), default=0)) + 1,
    )
    legend = "  " + "  ".join(f"{clr(CAT_CHAR[c], CAT_COLOR[c])}={c}" for c in CATS)
    lines = [b(f"  {title}"), legend, ""]
    for row in range(max_h, 0, -1):
        line = f"{row:2d}│"
        for bi, cols in enumerate(band_data):
            if bi > 0:
                line += '│'
            for d in cols:
                total = sum(d[c] for c in CATS)
                if row > total:
                    line += ' '
                else:
                    cumul = 0.0
                    char = ' '
                    for c in CATS:
                        cumul += d[c]
                        if row <= cumul:
                            char = cat_block(c)
                            break
                    line += char
        lines.append(line)
    lines += axis_lines(sessions, bands)
    return lines


def linear_regression(xs: list[float], ys: list[float]) -> tuple[float, float]:
    n = len(xs)
    if n < 2:
        return 0.0, ys[0] if ys else 0.0
    sx, sy = sum(xs), sum(ys)
    sxy = sum(x * y for x, y in zip(xs, ys))
    sxx = sum(x * x for x in xs)
    d = n * sxx - sx * sx
    if d == 0:
        return 0.0, sy / n
    slope = (n * sxy - sx * sy) / d
    return slope, (sy - slope * sx) / n


# ---------------------------------------------------------------------------
# Report-Abschnitte
# ---------------------------------------------------------------------------
def section(title: str) -> str:
    return f"\n{HSEP}\n{b(title)}\n{HSEP}"


def render_aggregation(sessions: list[SessionData]) -> str:
    findings = [f for s in sessions for f in s.findings]
    lines = [section("1. Aktuelle Periode")]
    if not findings:
        lines.append("  (keine strukturierten Findings)")
        return "\n".join(lines)

    by_s: dict[str, int] = defaultdict(int)
    by_k: dict[str, int] = defaultdict(int)
    by_c: dict[str, int] = defaultdict(int)
    for f in findings:
        by_s[f.impact] += 1
        by_k[f.kategorie] += 1
        by_c[f.kontext] += 1

    lines.append(f"  Sessions: {len(sessions)}  |  Findings: {len(findings)}")
    lines.append("  Impact:    " + "  |  ".join(f"{s}: {by_s[s]}" for s in IMPACT_ORDER if by_s[s]))
    lines.append("  Kategorie: " + "  |  ".join(f"{k}: {v}" for k, v in sorted(by_k.items(), key=lambda x: -x[1])))
    lines.append("  Kontext:   " + "  |  ".join(f"{k}: {v}" for k, v in sorted(by_c.items(), key=lambda x: -x[1])))
    return "\n".join(lines)


def render_sonstiges(sessions: list[SessionData]) -> str:
    hits = [f for s in sessions for f in s.findings if f.kontext == "Sonstiges"]
    lines = [section("2. Sonstiges-Einträge (Tag-Pflege)")]
    if not hits:
        lines.append("  Keine Einträge mit Kontext 'Sonstiges'.")
        return "\n".join(lines)
    lines.append(f"  {len(hits)} Einträge – fehlende Tags ableiten:\n")
    for f in hits:
        lines.append(f"  [{f.impact}] S{f.session_num}: {f.titel}")
        if f.was:   lines.append(f"    Was:   {f.was}")
        if f.warum: lines.append(f"    Warum: {f.warum}")
        lines.append("")
    return "\n".join(lines)


def render_zeitreihen(all_sessions: list[SessionData]) -> str:
    lines = [section("3. Zeitreihen – Gesamt")]
    if len(all_sessions) < 2:
        lines.append(f"  Zu wenig Sessions ({len(all_sessions)}). Minimum: 2.")
        return "\n".join(lines)
    bands = compute_bands(len(all_sessions))
    lines += render_gesamt_chart(all_sessions, bands, "Impact-Score/Session (Gesamt)")
    return "\n".join(lines)


def render_stack(all_sessions: list[SessionData]) -> str:
    lines = [section("4. Kategorie-Stack")]
    if len(all_sessions) < 2:
        lines.append(f"  Zu wenig Sessions ({len(all_sessions)}). Minimum: 2.")
        return "\n".join(lines)
    bands = compute_bands(len(all_sessions))
    lines += render_stack_chart(all_sessions, bands, "Impact-Score/Session (nach Kategorie)")
    return "\n".join(lines)


def render_heatmap(all_sessions: list[SessionData]) -> str:
    lines = [section("5. Heatmap: Session × Kontext")]
    if len(all_sessions) < 2:
        lines.append(f"  Zu wenig Sessions ({len(all_sessions)}). Minimum: 2.")
        return "\n".join(lines)
    kontexte = sorted({f.kontext for s in all_sessions for f in s.findings})
    if not kontexte:
        lines.append("  Keine Findings.")
        return "\n".join(lines)
    col_w = max(len(k) for k in kontexte) + 2
    header = "  " + "Sess.".ljust(8) + "".join(k.ljust(col_w) for k in kontexte)
    lines.append(header)
    lines.append("  " + "─" * (len(header) - 2))
    for s in all_sessions:
        cnt: dict[str, int] = defaultdict(int)
        for f in s.findings:
            cnt[f.kontext] += 1
        row = "  " + str(s.num).ljust(8) + "".join(
            (str(cnt[k]) if cnt[k] else "·").ljust(col_w) for k in kontexte
        )
        lines.append(row)
    return "\n".join(lines)


def render_pattern(current_sessions: list[SessionData], archive_periods: list[list[SessionData]], cms: list[Countermeasure]) -> str:
    tail_sessions = [s for period in archive_periods[-PATTERN_WINDOW:] for s in period]
    window = tail_sessions + current_sessions

    lines = [section("6. Pattern-Kandidaten")]
    n_periods = min(PATTERN_WINDOW, len(archive_periods))
    lines.append(f"  Fenster: aktuelle Periode + letzte {n_periods} Archiv-Perioden ({len(window)} Sessions gesamt)\n")

    findings = [f for s in window for f in s.findings]
    if not findings:
        lines.append("  Keine Findings im Fenster.")
        return "\n".join(lines)

    triplet_count: dict[tuple, int] = defaultdict(int)
    triplet_ex: dict[tuple, list[str]] = defaultdict(list)
    for f in findings:
        key = (f.impact, f.kategorie, f.kontext)
        triplet_count[key] += 1
        if len(triplet_ex[key]) < 2:
            triplet_ex[key].append(f"S{f.session_num}: {f.titel}")

    candidates = [(k, v) for k, v in triplet_count.items() if v >= 2]
    candidates.sort(key=lambda x: -x[1])

    if not candidates:
        lines.append("  Keine Kombination tritt ≥2× auf.")
        return "\n".join(lines)

    new_found = False
    for (impact, kategorie, kontext), count in candidates:
        covered = has_cm(impact, kategorie, kontext, cms)
        if not covered:
            new_found = True
            lines.append(f"  {clr('NEU', RED+BOLD)} [{impact}] [{kategorie}] [{kontext}] – {count}×")
            for ex in triplet_ex[(impact, kategorie, kontext)]:
                lines.append(f"    · {ex}")
            lines.append("")

    if not new_found:
        lines.append("  Alle Muster haben bereits eine Countermeasure.\n")

    covered_list = [(k, v) for k, v in candidates if has_cm(k[0], k[1], k[2], cms)]
    if covered_list:
        lines.append("  Bereits abgedeckt:")
        for (impact, kategorie, kontext), count in covered_list:
            lines.append(f"    [{impact}] [{kategorie}] [{kontext}] – {count}×")

    return "\n".join(lines)


def render_clustering(all_sessions: list[SessionData], cms: list[Countermeasure]) -> str:
    open_findings = [f for s in all_sessions for f in s.findings if not is_bewährt(f, cms)]
    lines = [section("7. Semantisches Clustering (Was/Warum)")]

    if len(open_findings) < MIN_CLUSTER:
        lines.append(f"  Zu wenig offene Einträge ({len(open_findings)} / {MIN_CLUSTER} Minimum).")
        lines.append(f"  Aktiviert ab {MIN_CLUSTER} Einträgen.")
        return "\n".join(lines)

    if not HAS_SKLEARN:
        lines.append("  sklearn nicht verfügbar: pip install scikit-learn")
        return "\n".join(lines)

    texts = [f"{f.was} {f.warum}".strip() for f in open_findings]
    n_clusters = max(3, len(open_findings) // 10)
    try:
        X = TfidfVectorizer(max_features=200, min_df=2).fit_transform(texts)
    except ValueError:
        lines.append("  Zu wenig Vokabular für TF-IDF.")
        return "\n".join(lines)

    labels = KMeans(n_clusters=n_clusters, random_state=42, n_init=10).fit_predict(X)
    clusters: dict[int, list[Finding]] = defaultdict(list)
    for i, f in enumerate(open_findings):
        clusters[int(labels[i])].append(f)

    for cid, members in sorted(clusters.items(), key=lambda x: -len(x[1])):
        lines.append(f"  Cluster {cid + 1} ({len(members)} Findings):")
        for f in members[:5]:
            lines.append(f"    S{f.session_num} [{f.impact}] {f.titel}")
        if len(members) > 5:
            lines.append(f"    … +{len(members) - 5} weitere")
        lines.append("")

    return "\n".join(lines)


def render_trend(all_sessions: list[SessionData]) -> str:
    LABEL_W = 20
    lines = [section("8. Trendanalyse per Kategorie")]
    if len(all_sessions) < 2:
        lines.append(f"  Zu wenig Sessions ({len(all_sessions)}). Minimum: 2.")
        return "\n".join(lines)

    bands = compute_bands(len(all_sessions))
    band_labels = []
    for start, end in bands:
        s0, se = all_sessions[start].num, all_sessions[end - 1].num
        band_labels.append(f"S{s0}" if s0 == se else f"S{s0}-{se}")

    def band_avg(ys: list[float], start: int, end: int) -> float:
        sub = ys[start:end]
        return sum(sub) / len(sub) if sub else 0.0

    def fmt_val(avg: float, prev: float | None) -> str:
        s = f"{avg:.1f}".rjust(TREND_VALUE_W)
        if prev is None:
            return s
        if avg < prev - 0.05:
            return clr(s, GREEN)
        elif avg > prev + 0.05:
            return clr(s, RED)
        return GRAY + s + RST

    def fmt_delta(last: float, prev: float) -> str:
        raw = f"{(last - prev) / prev * 100:+.0f}%" if prev else ("+∞%" if last > 0 else "0%")
        raw_padded = raw.rjust(6)
        arrow = "↓" if last < prev - 0.05 else ("↑" if last > prev + 0.05 else "→")
        if last < prev - 0.05:
            return clr(raw_padded, GREEN) + " " + clr(arrow, GREEN)
        elif last > prev + 0.05:
            return clr(raw_padded, RED) + " " + clr(arrow, RED)
        return GRAY + raw_padded + " " + arrow + RST

    def trend_line(label: str, ys: list[float], color: str = "") -> str:
        avgs = [band_avg(ys, s, e) for s, e in bands]
        vals = "".join(fmt_val(avgs[i], avgs[i - 1] if i > 0 else None) for i in range(len(avgs)))
        delta = ("  " + fmt_delta(avgs[-1], avgs[-2])) if len(avgs) >= 2 else ""
        return f"  {color}{label:<{LABEL_W}}{RST}  {vals}{delta}"

    indent = "  " + " " * (LABEL_W + 2)
    header = indent + "".join(lbl.rjust(TREND_VALUE_W) for lbl in band_labels) + "  Δ zuletzt"
    sep    = "  " + "─" * (LABEL_W + 2 + TREND_VALUE_W * len(bands) + 11)

    lines.append("  Ø Impact-Score/Session pro Band (logarithmisch).")
    lines.append("  Score = Summe der Gewichte (KRITISCH=25, HOCH=10, MITTEL=3, GERING=1).")
    lines.append("  Farbe: grün = weniger als Vorband (besser), rot = mehr (schlechter).")
    lines.append("  Δ zuletzt = Änderung letztes Band vs. vorletztes Band.\n")
    lines.append(header)
    lines.append(sep)

    ys_total = [float(sum(IMPACT_WEIGHTS.get(f.impact, 0) for f in s.findings)) for s in all_sessions]
    lines.append(trend_line("GESAMT", ys_total))
    lines.append("")

    kategorien = sorted({f.kategorie for s in all_sessions for f in s.findings})
    for kat in kategorien:
        ys = [float(sum(IMPACT_WEIGHTS.get(f.impact, 0) for f in s.findings if f.kategorie == kat)) for s in all_sessions]
        lines.append(trend_line(kat, ys, CAT_COLOR.get(kat, "")))

    return "\n".join(lines)


def archive_start_sessions(archive_dir: str) -> list[int]:
    """Start-Session-Nummern aller Retro-Archive (session_<X>_to_<Y>.md → X).
    Anzahl Starts > Bezugs-Session = wie viele Retros seitdem stattfanden."""
    starts: list[int] = []
    if os.path.isdir(archive_dir):
        for fname in os.listdir(archive_dir):
            m = re.match(r"session_(\d+)_to_\d+\.md$", fname)
            if m:
                starts.append(int(m.group(1)))
    return starts


def render_escalated(cms: list[Countermeasure], archive_dir: str) -> str:
    lines = [section("9. Eskalierte Maßnahmen (≥ 2 Retros OFFEN)")]
    archive_starts = archive_start_sessions(archive_dir)

    offen = [cm for cm in cms if cm.status == 'OFFEN']
    if not offen:
        lines.append("  Keine offenen Maßnahmen.")
        return "\n".join(lines)

    escalated = [(cm, sum(1 for s in archive_starts if s > cm.seit_session)) for cm in offen]
    escalated = [(cm, n) for cm, n in escalated if n >= 2]

    if not escalated:
        lines.append("  Keine Maßnahme seit ≥ 2 Retros OFFEN.")
        return "\n".join(lines)

    for cm, retros in escalated:
        cm_label = f"{cm.cm_id} " if cm.cm_id else ""
        lines.append(f"  {clr('ESKALIERT', RED+BOLD)} {cm_label}[seit S{cm.seit_session}, {retros} Retro(s) ohne Umsetzung]")
        lines.append(f"  Problem: {cm.problem}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="Kaizen-Retro-Bericht.")
    parser.add_argument("--current",  default=DEFAULT_CURRENT)
    parser.add_argument("--archive",  default=DEFAULT_ARCHIVE)
    parser.add_argument("--cm",       default=DEFAULT_CM)
    parser.add_argument("--verbose",  action="store_true",
                        help="Zeigt alle Abschnitte inkl. Charts (Standard: nur retro-relevante)")
    args = parser.parse_args()

    if not os.path.exists(args.current):
        print(f"Fehler: {args.current} nicht gefunden.", file=sys.stderr)
        return 1

    current_sessions = parse_file(args.current)
    all_sessions     = load_all(args.current, args.archive)
    archive_periods  = load_archive_periods(args.archive)
    cms              = load_cm(args.cm)

    n_findings = sum(len(s.findings) for s in all_sessions)
    total = total_sessions_from_range(args.archive, current_sessions)
    total_str = str(total) if total is not None else str(len(all_sessions))

    # Letzte Retro aus Archiv-Dateinamen ableiten (session_X_to_Y.md → Y)
    last_retro_session = None
    if os.path.isdir(args.archive):
        archive_files = sorted(f for f in os.listdir(args.archive) if f.endswith(".md"))
        if archive_files:
            m = re.search(r"session_\d+_to_(\d+)\.md", archive_files[-1])
            if m:
                last_retro_session = int(m.group(1))

    print(f"\n{'═'*64}")
    print(f"  {b('KAIZEN RETRO-BERICHT')}")
    print(f"  Sessions gesamt: {total_str}  |  Strukturierte Findings: {n_findings}")
    if last_retro_session is not None:
        print(f"  Letzte Retro: nach Session {last_retro_session}  |  Neue Sessions ab: {last_retro_session + 1}")
    else:
        print(f"  Letzte Retro: keine (erster Lauf)")
    print(f"{'═'*64}")

    print(render_aggregation(current_sessions))
    print(render_sonstiges(current_sessions))
    if args.verbose:
        print(render_zeitreihen(all_sessions))
        print(render_stack(all_sessions))
        print(render_heatmap(all_sessions))
    print(render_pattern(current_sessions, archive_periods, cms))
    if args.verbose:
        print(render_clustering(all_sessions, cms))
        print(render_trend(all_sessions))
    print(render_escalated(cms, args.archive))
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
