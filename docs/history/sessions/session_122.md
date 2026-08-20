# Session 122 – 2026-08-21

**Phase:** SKELETON | **Art:** OBS-Drain – Drain-Steuerung auf Wert statt Menge, Tracker-Fehlablagen umgezogen

Reiner Drain-Durchlauf ohne Produktionscode. Ein Eintrag umgesetzt (OBS-S121-2), vier durch **Umzug**
aufgelöst, ein neuer erfasst und geparkt; Backlog 26 → 22, davon 12 behandlungswürdig unter der neuen
Skala. Der Schwerpunkt lag auf dem Drain-Mechanismus selbst: Er steuerte über die Backlog-**Größe**
und hielt sich damit selbst am Leben, weil jede Drain-Session neue Einträge erzeugt.

Zwei offene Fragen wurden vorgelegt und terminiert (unten E), zwei Produkt-Themen verließen den
OBS-Pool als Tech-Debt, zwei weitere als Guideline-Wissen.

---

## A – OBS-S121-2: Drain-Steuerung hing an der Menge statt am Wert

**Korrektur der Erfassung.** Der Eintrag gab den Kern unvollständig wieder; der User trug nach, was
beim Protokollieren verlorengegangen war: Drain-Sessions folgen aufeinander, erzeugen selbst
Nachschub, und verdrängen dadurch die Entwicklung. Die Beobachtung wurde vor der Behandlung um diesen
Teil ergänzt (dieselbe Klasse Fehler wie S115 – agentenformulierte Erfassung verfehlt das Ziel).

**Messungen** (Commit-Historie, `observations.md` + Archiv, S100–S121):

| Größe | Wert |
|---|---|
| Erfasst | 59 Einträge / 22 Sessions = 2,68 je Session |
| Aufgelöst | ~42 / 22 = 1,9 je Session (Untergrenze – `VERWORFEN` ohne Session-Stempel fehlt) |
| Drain lief | in 10 von 22 Sessions, dort ~4–5 Einträge |
| Feature-Arbeit | **kein implementierter Gherkin-Lauf zwischen S112 und S121**; S113–S119 und S121 mit null Produktdateien |
| Backlog-Struktur | 17 von 26 Einträgen so niedrig bewertet, dass die Wert-Lane sie nie aufgriff |

Der Deckel der alten Rate (`clamp(round(0.4·B), 3, 7)`) war damit nie bindend – bindend war die
Session-Kapazität. Und `B ≥ 13` als Anspruchsbedingung war selbsterhaltend.

**Umgesetzt** (kanonisch in `process.md`, „Score und Behandlungswürdigkeit" + „Lanes und Trigger"):

1. **Score = Impact × Häufigkeit** mit `GERING = 0` (die Rubrik definiert GERING als *keine* Folge –
   folgenlos bleibt folgenlos, auch gehäuft und in einer Cluster-Summe), MITTEL 1, HOCH 3, KRITISCH 9;
   gelegentlich 1, häufig 2, dauerhaft 4. Behandlungswürdig ab 2.
2. **Pflichtfeld `Zusammen-erledigen:`** – Einträge, die sich in einem Zug miterledigen lassen, bilden
   eine Einheit mit summiertem Score. Maßstab ist Bearbeitungs-Kolokation, nicht Problem-Identität.
3. **Trigger** statt Backlog-Zahl: Top-5-Einheiten-Summe ≥ 9 **oder** ≥ 4 Einträge älter als 15 Sessions.
   Zwei Lanes, zwei Auslöser – ohne den zweiten hinge die Alters-Lane am Wert-Trigger.
4. **Alters-Lane** nimmt alle über 15 Sessions statt nur des ältesten; ein Slot führte den Zufluss nicht ab.

**Verworfen:** Rate erhöhen (Deckel war nie bindend), Zielwert aufgeben (Alt-Einträge veralten und
tragen dann falsche Fakten), Potenzierung `Impact^Häufigkeit` (Spreizung 1–64, und `GERING = 1` ließe
fünf folgenlose Einträge zusammen behandlungswürdig werden), log-gewichtete Alterssumme (der
Logarithmus dämpft das Alter so stark, dass ein Anzahl-Trigger daraus wird – die Alters-Lane existiert
aber gerade für die uralten).

**Kalibrierungs-Grenzen**, beide vom User aufgedeckt: Die Wert-Lane war zunächst auf 5 Einträge
gedeckelt – ein Deckel begrenzt aber nur den Vorschlag, nicht die Arbeit, und versteckt
Behandlungswürdiges; die 5 blieb nur in der Trigger-Summe. Und das Kriterium für
`Zusammen-erledigen` war als „erledigt *eine* Lösung beide?" zu eng gefasst: Das trifft fast nur
Duplikate, die konsolidiert statt geclustert gehören (→ LL-S122-1).

## B – Referenzielle Integrität der Kanten

Geprüft statt angenommen: Eine **einseitige** Kante erzeugt dasselbe Cluster wie eine beidseitige –
`cluster()` wertet sie ungerichtet aus. Eine Spiegelung wäre eine zweite Kopie derselben Information
und könnte nur auseinanderlaufen. Der reale Defekt lag woanders: Ein Ziel, das nicht existiert, wurde
**stillschweigend verworfen** – die Kante fiel lautlos aus. Daher: Existenzprüfung zur Schreibzeit
(blockt Vertipper und Selbstreferenz), `obs.py get` zeigt eingehende Kanten (ersetzt den einzigen
echten Nutzen der Spiegelung), und der Drain warnt bei Kanten auf nicht mehr drainbare Einträge.

## C – Ursache der Fehlablagen behoben

Vier Einträge im OBS-Pool waren gar keine Prozess-Beobachtungen. Die Ursache ist strukturell:
`observations.md` trug als einziger Tracker **keine Aufnahmebedingung**, und die Tabelle „Wann gehört
etwas wohin?" in `process.md` kennt nur Prozess-Ziele – wer mit einem Produkt-Befund kam, fand die
Produkt-Tracker gar nicht als Option, und das Kriterium „vorausschauende Beobachtung, wie das System
besser wäre" passt wörtlich auf sie.

Behoben: `CLAUDE.md`-Sektion ist jetzt Einstieg für **alle sechs** Tracker (Schnitt 1 vorweg),
`observations.md` trägt eine Aufnahmebedingung, `process.md` eine Vorschaltfrage, und der Skill
`draining-observations` prüft in **Schritt 0** vor jeder Kandidatenbildung Prozess vs. Produkt.

Umgezogen: OBS-S101-3 → **TD-S122-1** (`useResultMutation` 4er-Tupel), OBS-S108-5 → **TD-S122-2**
(Restore-Endpoint als CORS-Simple-Request ohne Preflight), OBS-S103-2 → `tdd-process.md`
(100 % Mutation Score pinnt keine Reihenfolge), OBS-S105-2 → `coding-guideline-csharp.md`
(kulturbezogene Analyzer unter `TreatWarningsAsErrors`).

## D – Bestands-Migration

Alle 21 offenen Einträge haben das neue Pflichtfeld: vier belegte Kanten-Gruppen (Tracker-Schreibschicht
mit sechs Mitgliedern, `next_run.py`-Paar, `check-bash-permission.py`-Paar), sonst `keiner`. Wirkung:
behandlungswürdig 8 → 12; der Tracker-Cluster zieht `OBS-S107-1` (Score 0) mit, und `OBS-S110-1` +
`OBS-S117-1` überschreiten erst gemeinsam die Schwelle. `obs.py set --zusammen-erledigen` entstand
dabei als fehlendes Werkzeug – der Skill verlangt Kanten-Korrektur, die CLI konnte sie nicht schreiben.

## E – Offene Fragen vorgelegt

- **OQ-S094-2** (Mobile-Szenarien): `Fällig: Phase:MVP` – das bisher fehlende Pflichtfeld nachgetragen.
  Beim Phasenwechsel läuft ein `gherkin-workshop` für die dann bestehenden Seiten.
- **OQ-S119-4** (Regel 5 im Frontend): `Fällig: Phase:V1, S140`, gekoppelt an OQ-S094-1. Befund am
  Bestand im Eintrag festgehalten: `ValidationError` existiert im Client-Code **nicht** – real
  verwendet wird `ApiError`, bereits eine kind-getaggte Union. Es ist also nichts umzustellen; zu
  entscheiden ist, ob die Guideline einen Typ für einen Fall vorschreiben soll, den ADR-S112-4 ausschließt.

## Learnings & Beobachtungen

- **LL-S122-1** – Feld nach breitem Kriterium befüllt, nach engem dokumentiert.
- **LL-S122-2** – drei Prüfmittel ohne Gegenprobe gebaut (Rückfall gegen CM-S116-1, dort vermerkt).
- **LL-S122-3** – eigene Ankündigung als Freigabe behandelt, während eine Frage offen war.
- **OBS-S122-1** – die Trigger-Kalibrierung ist gerechnet, nicht gemessen; `IN BEOBACHTUNG bis S132`
  (Termin bewusst hinter die Abbauphase gelegt, sonst misst die Wiedervorlage nur den Rückstau).

**Verifikation:** 698 Tooling-Tests grün. Der Trigger wurde gegen fünf Fälle geprüft, die Erfolg und
Misserfolg unterscheidbar zeigen – darunter „zwölf Bagatellen lösen nicht aus" und „ein einzelnes
`KRITISCH × gelegentlich` löst allein aus".
