import type { On } from 'claude-code'
import { expect, mock, test } from 'claude-code/testing'
import type { Engine, MockClock } from 'claude-code/testing'

const UEBERBLICK = {
  aufgabe: 'Jenga-Score: -28 / 100  [RETRO FÄLLIG] (fällig ≤ 0)',
  weg: 'Session mit Skill `kaizen` beginnen.',
  phase: 'SKELETON 🔄',
  story: 'US-602 (Rezept-Erfassung)',
  lauf: '`run-9` „Anlegen·Validierung Titel und Anweisung" (Full-Stack)',
  nachrangig: ['abhaengigkeiten', 'obs-drain'],
}
const BAND = {
  plugin: 'naechste-aufgabe',
  component: 'AbovePrompt',
  props: { hasSurvey: false, isWorking: false, maxRows: 20, bodyColumns: 120,
           scroll: { offset: 0, bodyRows: 20 }, view: {} },
} as const
const START = { cwd: '/repo', surface: 'terminal', isInteractive: true } as const

type Lauf = { argv?: readonly string[], cwd?: string }

// Steht für die Engine: die Agenda antwortet mit `stdout` (oder scheitert mit `exitCode`).
// Gibt die Uhr zurück – der Agenda-Lauf startet über `$.clock.after`, erst `settle` lässt ihn laufen.
function engine(on: On, laeufe: Lauf[], stdout: string, exitCode = 0): MockClock {
  const uhr = mock.clock(on)
  on('session.start', (_$, e) => ({ cwd: e.cwd }))
  on('session.root', async () => ({ value: '/repo' }))
  on('process.run', async (_$, e) => {
    laeufe.push({ argv: e.argv, cwd: e.init?.cwd })
    return { value: { exitCode, stdout, stderr: exitCode === 0 ? '' : 'Traceback: kaputt',
                      isStdoutTruncated: false, isStderrTruncated: false } }
  })
  on('prompt.submit', (_$, e) => ({ text: e.text }))
  on('classic.SessionStart', () => ({}))
  // Was die Engine selbst über dem Prompt zeichnet – sichtbar, wenn die Mod das Band abgibt.
  on('ui.render', ($, e) => {
    const { Text } = $.ui.resolve(e)
    return <Text>{ENGINE_BAND}</Text>
  })
  return uhr
}
const ENGINE_BAND = 'Band der Engine'

async function texte($: Engine, surface: 'terminal' | 'desktop') {
  const band = await $.ui.mount({ ...BAND, surface })
  const gefunden = await band.findAll({ type: 'Text' })
  await band.unmount()
  return gefunden.map(t => t.text)
}

test('zeigt nach dem Start Aufgabe mit Weg, Story und Lauf und die übrigen Punkte', async ($, on) => {
  const laeufe: Lauf[] = []
  const uhr = engine(on, laeufe, JSON.stringify(UEBERBLICK))

  await $.session.start(START)
  await uhr.settle()

  expect(laeufe).toEqual([{ argv: ['python3', '-m', 'prozesscode.session-agenda', '--ueberblick'],
                            cwd: '/repo' }])
  for (const surface of ['terminal', 'desktop'] as const) {
    const t = (await texte($, surface)).join('\n')
    expect(t).toContain('Als Nächstes:')
    expect(t).toContain('Jenga-Score: -28 / 100  [RETRO FÄLLIG] (fällig ≤ 0) → Session mit Skill `kaizen` beginnen.')
    expect(t).toContain('Story US-602 (Rezept-Erfassung) · nächster Lauf `run-9` „Anlegen·Validierung Titel und Anweisung" (Full-Stack)')
    expect(t).toContain('Außerdem offen: abhaengigkeiten, obs-drain')
  }
})

test('verschwindet mit dem ersten Prompt', async ($, on) => {
  const uhr = engine(on, [], JSON.stringify(UEBERBLICK))
  await $.session.start(START)
  await uhr.settle()

  expect(await texte($, 'terminal')).not.toEqual([ENGINE_BAND])  // Gegenprobe: vorher zeigt die Mod
  await $.prompt.submit({ text: 'mach weiter', wait: false, origin: { kind: 'composer' } })

  expect(await texte($, 'terminal')).toEqual([ENGINE_BAND])
})

test('erscheint nach /clear wieder – dort feuert nur der Settings-Hook SessionStart', async ($, on) => {
  const laeufe: Lauf[] = []
  const uhr = engine(on, laeufe, JSON.stringify(UEBERBLICK))
  await $.session.start(START)
  await uhr.settle()
  await $.prompt.submit({ text: 'mach weiter', wait: false, origin: { kind: 'composer' } })
  await $.prompt.submit({ text: '/clear', wait: false, origin: { kind: 'composer' } })
  expect(await texte($, 'terminal')).toEqual([ENGINE_BAND])  // Gegenprobe: vor dem Hook ist es aus

  await $.classic.SessionStart({ source: 'clear' })
  await uhr.settle()

  expect(laeufe).toHaveLength(2)
  expect((await texte($, 'terminal')).join('\n')).toContain('Als Nächstes:')
})

test('nach einer Zusammenfassung bleibt es aus – die Session läuft weiter', async ($, on) => {
  const laeufe: Lauf[] = []
  const uhr = engine(on, laeufe, JSON.stringify(UEBERBLICK))
  await $.session.start(START)
  await uhr.settle()
  await $.prompt.submit({ text: 'mach weiter', wait: false, origin: { kind: 'composer' } })

  await $.classic.SessionStart({ source: 'compact' })
  await uhr.settle()

  expect(laeufe).toHaveLength(1)
  expect(await texte($, 'terminal')).toEqual([ENGINE_BAND])
})

test('ohne erzwungene Aufgabe sagt es das, statt leer zu bleiben', async ($, on) => {
  const uhr = engine(on, [], JSON.stringify({ ...UEBERBLICK, aufgabe: null, weg: null, nachrangig: [] }))
  await $.session.start(START)
  await uhr.settle()

  const t = (await texte($, 'terminal')).join('\n')
  expect(t).toContain('keine Aufgabe erzwungen')
  expect(t).not.toContain('Außerdem offen')
})

test('scheitert die Agenda, nennt das Band Grund und Befehl zum Nachsehen', async ($, on) => {
  const uhr = engine(on, [], '', 1)
  await $.session.start(START)
  await uhr.settle()

  const t = (await texte($, 'terminal')).join('\n')
  expect(t).toContain('Session-Agenda nicht lesbar – Exit 1: Traceback: kaputt')
  expect(t).toContain('python3 -m prozesscode.session-agenda --ueberblick')
})

test('ohne Person am Prompt (claude -p) liest es die Agenda gar nicht', async ($, on) => {
  const laeufe: Lauf[] = []
  const uhr = engine(on, laeufe, JSON.stringify(UEBERBLICK))
  await $.session.start({ ...START, isInteractive: false })
  await uhr.settle()

  expect(laeufe).toEqual([])
  expect(await texte($, 'terminal')).toEqual([ENGINE_BAND])
})
