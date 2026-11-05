"""Tests für checks/eslint_lint.py – PostToolUse-Linter über die geänderte TypeScript-Datei.

Dieselben Zusagen wie der ruff-Check (tests/test_ruff_lint.py): Er greift nur bei TypeScript des
Clients, er lintet die GEÄNDERTE Datei, und er meldet sich, wenn ESLint fehlt oder abstürzt,
statt still zu verschwinden. Dazu: Er meldet Fehler, keine Warnungen – warum, steht im
Modul-Docstring.

Die JSON-Ausgaben sind echt (`eslint --format json <datei>` im Client, Probedateien).
"""
import subprocess
from importlib import import_module
from pathlib import Path

from prozesscode.hooks.checks import eslint_lint as el
from conftest import make_input

_FIXTURES = Path(__file__).parent / "fixtures"
_DATEI = "/home/kieritz/repos/mahl/Client/src/pages/RecipesPage.tsx"


def _json(name: str) -> str:
    return (_FIXTURES / f"eslint_json_{name}.json").read_text()


def _lauf(stdout: str, returncode: int = 1, stderr: str = "") -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


def _mit_lauf(monkeypatch, lauf: subprocess.CompletedProcess) -> list:
    befehle = []
    monkeypatch.setattr(el, "_eslint_vorhanden", lambda: True)
    monkeypatch.setattr(el, "_laufe", lambda *befehl: befehle.append(befehl) or lauf)
    return befehle


# --- Relevanz ----------------------------------------------------------------
def test_prueft_typescript_des_clients():
    assert el._is_watched(_DATEI)
    assert el._is_watched("Client/src/App.test.tsx")
    assert el._is_watched("Client/e2e/recipes.spec.ts")
    assert el._is_watched("Client/playwright.config.ts")


def test_ignoriert_anderes_und_fremde_pfade():
    assert not el._is_watched("Client/eslint.config.js")
    assert not el._is_watched("Client/src/index.css")
    assert not el._is_watched("prozesscode/qa-check.py")
    assert not el._is_watched(".claude/mods/naechste-aufgabe/hooks/register.tsx")
    assert not el._is_watched("Client/node_modules/foo/index.ts")


def test_der_check_haengt_am_hinweis_dispatcher():
    """Ein Check, den kein Dispatcher ruft, läuft nie – seine Tests blieben trotzdem grün."""
    dispatcher = import_module("prozesscode.hooks.check-code-quality-nonblocking")
    assert el.check in dispatcher.CHECKS


def test_ausserhalb_des_clients_laeuft_kein_eslint(monkeypatch):
    befehle = _mit_lauf(monkeypatch, _lauf(_json("sauber"), 0))
    assert el.check(make_input("prozesscode/qa-check.py", "x = 1\n")) == []
    assert befehle == []


# --- Verhalten ---------------------------------------------------------------
def test_saubere_datei_erzeugt_keine_warnung(monkeypatch):
    """Die echte Ausgabe trägt eine per Direktive unterdrückte Meldung – die zählt nicht."""
    _mit_lauf(monkeypatch, _lauf(_json("sauber"), 0))
    assert el.check(make_input(_DATEI, "")) == []


def test_fehler_erscheinen_mit_position_und_regel_warnungen_nicht(monkeypatch):
    _mit_lauf(monkeypatch, _lauf(_json("fehler_und_warnung"), 1))
    assert el.check(make_input(_DATEI, "")) == [
        "⚠️ ESLint meldet in dieser Datei 1 Fehler:\n"
        "  2:3 no-var: Unexpected var, use let or const instead.\n"
        "  Vollständig: python3 -m prozesscode.eslint-run"]


def test_nur_warnungen_erzeugen_keine_meldung(monkeypatch):
    """ESLint endet bei reinen Warnungen mit 0 – gemeldet wird trotzdem nur nach Schweregrad."""
    nur_warnung = _json("fehler_und_warnung").replace('"severity":2', '"severity":1')
    _mit_lauf(monkeypatch, _lauf(nur_warnung, 0))
    assert el.check(make_input(_DATEI, "")) == []


def test_syntaxfehler_ohne_regel(monkeypatch):
    _mit_lauf(monkeypatch, _lauf(_json("syntaxfehler"), 1))
    assert el.check(make_input(_DATEI, "")) == [
        "⚠️ ESLint meldet in dieser Datei 1 Fehler:\n"
        "  1:13 Parsing error: Variable declaration expected.\n"
        "  Vollständig: python3 -m prozesscode.eslint-run"]


def test_datei_ausserhalb_jeder_tsconfig_zeigt_die_erste_zeile_der_meldung(monkeypatch):
    """Ohne Position und mit mehrzeiliger Meldung – die erste Zeile sagt, was los ist."""
    _mit_lauf(monkeypatch, _lauf(_json("ausserhalb_tsconfig"), 1))
    assert el.check(make_input(_DATEI, "")) == [
        "⚠️ ESLint meldet in dieser Datei 1 Fehler:\n"
        "  Parsing error: /home/kieritz/repos/mahl/Client/lintprobe_frei_tmp.ts was not found "
        "by the project service. Consider either including it in the tsconfig.json or "
        "including it in allowDefaultProject.\n"
        "  Vollständig: python3 -m prozesscode.eslint-run"]


def test_viele_fehler_werden_gekuerzt(monkeypatch):
    meldung = ('{"ruleId":"no-var","severity":2,"message":"m","line":%d,"column":1}')
    viele = '[{"messages":[' + ",".join(meldung % i for i in range(1, 11)) + "]}]"
    _mit_lauf(monkeypatch, _lauf(viele, 1))
    [warnung] = el.check(make_input(_DATEI, ""))
    assert warnung == (
        "⚠️ ESLint meldet in dieser Datei 10 Fehler:\n  "
        + "\n  ".join(f"{i}:1 no-var: m" for i in range(1, 9))
        + "\n  … und 2 weitere"
        "\n  Vollständig: python3 -m prozesscode.eslint-run")


def test_geprueft_wird_die_geaenderte_datei_als_json(monkeypatch):
    """Gegenprobe: Ein Linter, der eine andere Datei liest, ist grün und wertlos."""
    befehle = _mit_lauf(monkeypatch, _lauf(_json("sauber"), 0))
    el.check(make_input(_DATEI, ""))
    assert befehle == [(str(el.ESLINT), "--format", "json", _DATEI)]


def test_eslint_laeuft_im_client(monkeypatch):
    """Ohne `cwd` fände ESLint weder `eslint.config.js` noch die tsconfig."""
    aufrufe = []
    monkeypatch.setattr(el.subprocess, "run",
                        lambda befehl, **kw: aufrufe.append((befehl, kw)) or "lauf")
    assert el._laufe("eslint", "x.ts") == "lauf"
    assert aufrufe == [(("eslint", "x.ts"),
                        {"capture_output": True, "text": True, "cwd": el.CLIENT,
                         "timeout": 60})]


def test_eslint_vorhanden_prueft_die_datei(monkeypatch, tmp_path):
    monkeypatch.setattr(el, "ESLINT", tmp_path / "eslint")
    assert not el._eslint_vorhanden()
    (tmp_path / "eslint").touch()
    assert el._eslint_vorhanden()


def test_fehlendes_eslint_meldet_sich_statt_stumm_auszufallen(monkeypatch):
    """Ohne node_modules gäbe es sonst nie wieder eine Lint-Meldung – und niemand erführe davon."""
    monkeypatch.setattr(el, "_eslint_vorhanden", lambda: False)
    assert el.check(make_input(_DATEI, "")) == [
        "⚠️ ESLint nicht verfügbar – TypeScript wird je Edit nicht gelintet.\n"
        "  Herstellen: npm --prefix Client ci"]


def test_ein_eslint_absturz_reisst_den_hook_nicht_mit(monkeypatch):
    """Der Linter ist Beiwerk; sein Ausfall darf das Schreiben nicht blockieren."""
    def kracht(*_a):
        raise subprocess.TimeoutExpired("eslint", 60)

    monkeypatch.setattr(el, "_eslint_vorhanden", lambda: True)
    monkeypatch.setattr(el, "_laufe", kracht)
    assert el.check(make_input(_DATEI, "")) == [
        "⚠️ ESLint-Lauf fehlgeschlagen: Command 'eslint' timed out after 60 seconds"]


def test_unlesbare_ausgabe_meldet_sich_mit_stderr(monkeypatch):
    """Bricht ESLint ab (etwa an seiner Konfiguration), steht kein JSON auf stdout. Die
    stderr-Meldung ist hier synthetisch – geprüft wird nur, dass sie durchgereicht wird."""
    _mit_lauf(monkeypatch, _lauf("", 2, stderr="Oops! Something went wrong!\n\nZeile 2\n"))
    assert el.check(make_input(_DATEI, "")) == [
        "⚠️ ESLint-Lauf ohne lesbares Ergebnis (Exit 2): Oops! Something went wrong!"]


def test_unlesbare_ausgabe_ohne_stderr_sagt_das(monkeypatch):
    _mit_lauf(monkeypatch, _lauf("", 2))
    assert el.check(make_input(_DATEI, "")) == [
        "⚠️ ESLint-Lauf ohne lesbares Ergebnis (Exit 2): keine Meldung"]
