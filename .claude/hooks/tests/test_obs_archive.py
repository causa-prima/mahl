"""Tests für obs-archive.py – mechanisches Verschieben aufgelöster OBS (UMGESETZT/VERWORFEN) ins Archiv."""
import importlib.util
import os

_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "obs-archive.py")
_spec = importlib.util.spec_from_file_location("obs_archive", _path)
oa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(oa)

PRE = "# Observations\n\n<!-- header -->\n\n"


def make(oid, status="NEU", title="T"):
    return f"""## {oid} – {title}
- Status: {status}
- Impact: MITTEL    Häufigkeit: gelegentlich
- Beobachtung: irgendwas
- Bezug:

"""


def test_split_blocks_roundtrip():
    # Exakte Rekonstruktion: Präambel + alle Roh-Blöcke == Original (kein Zeichen verloren).
    text = PRE + make("OBS-S090-1") + make("OBS-S090-2", status="UMGESETZT (S091)")
    preamble, blocks = oa.split_blocks(text)
    assert preamble == PRE
    assert [oid for oid, _ in blocks] == ["OBS-S090-1", "OBS-S090-2"]
    assert preamble + "".join(b for _, b in blocks) == text


def test_archive_moves_only_resolved():
    obs = (PRE + make("OBS-S090-1")
           + make("OBS-S090-2", status="UMGESETZT (S091)")
           + make("OBS-S090-3", status="VERWORFEN (Grund)"))
    new_obs, new_arch, moved = oa.archive_resolved(obs, "# Archiv\n")
    assert moved == ["OBS-S090-2", "OBS-S090-3"]
    assert "OBS-S090-1" in new_obs
    assert "OBS-S090-2" not in new_obs and "OBS-S090-3" not in new_obs
    assert "OBS-S090-2" in new_arch and "OBS-S090-3" in new_arch
    assert new_obs.startswith(PRE)  # Präambel/Header bleibt erhalten


def test_archive_preserves_full_block_content():
    # Titel mit eigenem Gedankenstrich + Statuszeile landen unverändert im Archiv.
    obs = PRE + make("OBS-S088-1", status="UMGESETZT (S090)", title="Spezial – mit Details")
    _, new_arch, _ = oa.archive_resolved(obs, "# Archiv\n")
    assert "## OBS-S088-1 – Spezial – mit Details" in new_arch
    assert "- Status: UMGESETZT (S090)" in new_arch


def test_archive_noop_when_nothing_resolved():
    obs = PRE + make("OBS-S090-1") + make("OBS-S090-2", status="IN BEOBACHTUNG bis S099")
    new_obs, new_arch, moved = oa.archive_resolved(obs, "# Archiv\n")
    assert moved == [] and new_obs == obs and new_arch == "# Archiv\n"


def test_archive_idempotent():
    # Zweiter Lauf auf dem Ergebnis verschiebt nichts mehr und ändert nichts.
    obs = PRE + make("OBS-S090-1") + make("OBS-S090-2", status="UMGESETZT (S091)")
    new_obs, new_arch, _ = oa.archive_resolved(obs, "# Archiv\n")
    new_obs2, new_arch2, moved2 = oa.archive_resolved(new_obs, new_arch)
    assert moved2 == [] and new_obs2 == new_obs and new_arch2 == new_arch


def test_archive_separates_with_blank_line():
    # Genau eine Leerzeile zwischen Bestand und angehängtem Block (keine Verklebung).
    obs = PRE + make("OBS-S090-2", status="UMGESETZT (S091)")
    _, new_arch, _ = oa.archive_resolved(obs, "# Archiv\n- letzte Zeile\n")
    assert "letzte Zeile\n\n## OBS-S090-2" in new_arch
