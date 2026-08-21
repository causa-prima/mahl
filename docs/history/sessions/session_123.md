# Session 123 – 2026-08-21

**Phase:** SKELETON | **Art:** Kaizen-Retro S116–122 + Agenda-Bugfix

Retro der Periode S116–122 (14 Findings, 6 Sessions). Zentraler Befund: **8 von 9 HOCH-Findings
hatten keinen Countermeasure-Anschluss** – der Fehlausgang, den CM-S078-2 seit S078 beschreibt, in
verschärfter Form. Als Antwort entsteht der Anschluss ab jetzt bei der **Erfassung** statt in der
Retro. Vorgeschaltet ein Bugfix, der die Retro überhaupt erst sichtbar machte.

---

## A – Der Retro-Trigger fiel genau dann aus, wenn er greifen sollte

Die Session-Agenda meldete `Agenda-Modul retro ausgefallen (Exit 2)` und schlug stattdessen einen
OBS-Drain vor. Ursache: `jenga_score.py` meldete „Retro fällig" über **Exit 2**, `session-agenda.py`
wertet – für alle Module einheitlich – jeden Exit ≠ 0 als Modulausfall. Das Retro-Modul fiel damit
genau in dem Fall aus, für den es gebaut ist.

Der erste Fixansatz hätte `_laufe()` um erlaubte Signal-Exits erweitert; der User hielt dagegen, ob
nicht eher das eine abweichende Script zu korrigieren sei. Die Prüfung gab ihm recht: Der Exit-2 war
**nirgends dokumentiert** (`process.md` führt `jenga_score.py` rein als Report), von **keinem** Test
gedeckt und wurde von **keinem** Aufrufer ausgewertet – `session-agenda.py` liest den Text, der
frühere `session-start.sh` griff per grep. Alle übrigen Report-Scripts der Agenda (`obs-drain.py`,
`next_run.py`, `td_due.py`) liefern Exit 0; Exit ≠ 0 nutzen nur die echten Gates. Behoben an der
Quelle, `_laufe()` blieb unangetastet. Sechs Tests in `test_jenga_score.py` und
`test_session_agenda.py`, je mit Gegenprobe (ein echter Absturz muss weiterhin als Ausfall gelten).

## B – Schritt 0: Noise-Review und Impact-Sanity-Check

36 Einträge geprüft (14 aktuelle Periode, 22 Archiv S107–115), **kein Noise**. Zwei Grenzfälle
bewusst behalten: LL-S113-2 (der Kernfakt ist eine statische Tatsache, die Regel darüber ein
Testdesign-Urteil) und LL-S107-1 (trägt seinen Fix im Text, die Regel bleibt aber verletzbar).

Drei Impacts nach User-Freigabe von MITTEL auf HOCH korrigiert: LL-S118-1, LL-S120-4, LL-S121-1.
Gegen den eigenen Aufwärts-Bias geprüft – bester Abwärtskandidat LL-S117-1 bewusst belassen, weil
echte Nacharbeit entstand. LL-S121-3 als KRITISCH-Kandidat vorgelegt und begründet bei HOCH belassen.

**Tag-Befund:** `LL-S121-2` trug `[Messung]`, das in keiner der beiden kanonischen Quellen steht und
über alle 169 Einträge genau 1× vorkommt → auf `[Kommunikation]` korrigiert, konsistent mit
LL-S114-1/LL-S109-1. Erster empirischer Beleg für OBS-S116-4.

## C – Der zentrale Befund: HOCH-Findings ohne Anschluss

Mechanisch geprüft über die Erwähnung jeder LL-ID in `countermeasures.md`: Von 9 HOCH-Findings der
Periode hatte genau **eines** einen Anschluss (LL-S122-2). Aufschlussreich die Verteilung – die
Findings *mit* Anschluss stammen aus S116 selbst, die Nachträge entstehen also **in der Retro** statt
laufend, obwohl `process.md` „sofort" verlangt.

Die in S116 beschlossene Delegation an den Drain (OBS-S116-5) war zu langsam: Score 1 liegt unter der
Wert-Lane-Schwelle, aufgegriffen hätte ihn die Alters-Lane erst ab `ALT_AB = 15` Sessions, also S131.
Für ein Problem mit acht Instanzen in sechs Sessions zu spät. *(Die zuerst notierte Begründung „der
Drain hätte ihn nie angenommen" war falsch – sie übersah die Alters-Lane; vom User korrigiert, in
CM-S078-2 und im OBS-Archiv richtiggestellt.)*

**Maßnahme (via TDD):** Der LL-Eintrag trägt das Feld `CM-Bezug:`, erzwungen von
`lessons.py add --cm-bezug` für KRITISCH/HOCH – zulässig ist eine in `countermeasures.md`
**existierende** CM-ID oder `neu`; Freitext und tote IDs brechen mit Exit 1 ab. Bei MITTEL/GERING
optional. Verankert in `lessons_entry.py`, `lessons.py`, Template, `process.md`, `closing-session`;
der Rückweg im `kaizen`-Skill Schritt 3, der die Bezüge vor der Archivierung einlöst. Bewusst offen
gelassen: Der Zwang sitzt im Script, ein direkter Edit umgeht ihn – als nächster Kandidat in
CM-S078-2 notiert, mit Wirksamkeitskriterium statt Drain-Delegation.

## D – Countermeasures

Die 8 fehlenden Nachträge gezogen: CM-S116-1 (LL-S120-1/-2/-4, LL-S121-1/-3), CM-S064-1 (LL-S120-3),
CM-S095-2 (LL-S121-2), CM-S047-1 (LL-S118-1).

- **CM-S116-1** – Diagnose korrigiert: Die S122-Fassung vermutete, die Gegenprobe-Regel springe nur
  bei erkennbaren „Gates" nicht an. LL-S121-1 und LL-S121-3 widerlegen das – beide *sind* Gates.
  Tragfähiger: Sie springt beim **Bauen** generell nicht an, nur beim nachträglichen Hinterfragen.
- **CM-S064-1** – fünfte Tarnung: Die bisherigen vier betreffen fremde Quellen, LL-S122-1 die eigene,
  gerade erzeugte Arbeit.
- **CM-S078-2** → AKTIV (Maßnahme gebaut). **CM-S114-1** → BEWÄHRT (28/28 TD-Einträge vollständig,
  0 abgeschaffte Felder, 9 Sessions Evidenz; Regressions-Kanal: der Hook prüft Syntax, nicht ob ein
  Anker real eintritt).
- **CM-S114-2** – Kriterium nachgeschärft: Es band den Termin an eine Session-*Nummer* statt an Läufe
  der richtigen *Art*; nach S114 lag genau eine Implementierungs-Session. Jetzt „nach ≥3
  Implementierungs-Läufen".
- Keine Evidenz und daher unverändert: CM-S056-1 sowie CM-S070-1/-4, CM-S102-3, CM-S101-1, CM-S082-1,
  CM-S070-5 – alle nur in `implementing-scenario`-Läufen beobachtbar, davon gab es einen (S120).
- Keine Regression auf den BEWÄHRTEN. Bei CM-S102-2 sauber nachgezählt: 3 echte `ref-ok`-Marker wie
  in S116 (ein erster Zähler ergab 7 und zählte Prosa-Erwähnungen in Session-Logs mit).

## E – Durchsicht auf Redundanz und Länge

Auf Aufforderung des Users alle Änderungen gegengelesen. Ergebnis: eine Format-Beschreibung
dupliziert in genau dem `process.md`-Abschnitt, der „hier nicht duplizieren" anordnet; dieselbe
Session-Statistik in vier Dokumenten; CM-Nachträge 2–2,5× so lang wie die bestehenden derselben
Maßnahme (gemessen, nicht geschätzt). Alles gekürzt bzw. auf Verweise umgestellt. Beim Kürzen selbst
entstand ein Inhaltsfehler („sonst weglassen" statt „sonst optional"), vom User gefangen.

## Archivierung

`lessons_learned.md` → `archive/session_116_to_122.md` (14 Einträge), neu aus Template; der
Jenga-Score sprang sauber auf 100/100 zurück. OBS-S116-5 → UMGESETZT und ins Archiv verschoben,
OBS-S123-1 neu erfasst → 27 Einträge, davon 21 offen.

## Learnings & Beobachtungen

- **LL-S123-1** – Report-Script meldete seinen Befund per Exit-Code; das Modul fiel genau im Zielfall aus.
- **LL-S123-2** – Ausnahme im generischen Rahmen geplant, statt den einen abweichenden Aufrufer zu korrigieren.
- **LL-S123-3** – `grep -c` zählt Vorkommen, nicht Objekte; Zahl als Statusbefund vorgelegt.
- **LL-S123-4** – dieselbe Erklärung in vier Dokumente geschrieben, eines davon verbietet Duplikate ausdrücklich.
- **LL-S123-5** – Verdichten machte aus einer optionalen Angabe ein scheinbares Verbot.
- **LL-S123-6** – mehrpfadigen Mechanismus an einem Pfad geprüft und das Ergebnis fürs Ganze genommen.
- **LL-S123-7** – Befehl gegen eine Fixture ohne Datei-Header geprüft; an der echten Datei zählte er
  die Header-Erklärung mit (dieselbe Ursache wie LL-S116-1). Beim Verifizieren gefunden und behoben.
- **OBS-S123-1** – frisch geschriebene Doku wird nie auf Verdichtbarkeit geprüft; mit OBS-S117-3 verknüpft.

**Verifikation:** 713 Tooling-Tests grün. Jede Prüfstelle mit Gegenprobe gebaut – die CM-Bezug-Pflicht
gegen alle vier Impacts in beiden Richtungen, `cm_ids()` gegen eine unabhängige Zählung am echten
Bestand (33 = 33), der Score-Reset nach der Archivierung (100/100).
