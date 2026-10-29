import type { On } from 'claude-code'
import { expect, test } from 'claude-code/testing'
import type { FoundElement } from 'claude-code/testing'

const BEFEHL = 'python3 -m prozesscode.td set TD-S080-1 --titel "Neu"'
const BEFUND = {
  dateien: [{
    datei: 'docs/tech-debt.md',
    bloecke: [{
      art: 'geaendert',
      zeilen: [[{ text: 'TD-S080-1 — ', stil: ['fett'] }, { text: 'Alt', stil: ['fett', 'weg'] },
                { text: 'Neu', stil: ['fett', 'neu'] }]],
    }],
  }],
  fehler: null,
  warnung: null,
}
const PANE = {
  plugin: 'tracker-diff',
  surface: 'terminal',
  component: 'Pane',
  requestId: 'tracker-diff',
  props: { title: 'Tracker-Änderung', isFocused: false, bodyColumns: 80, placement: 'dock',
           scroll: { offset: 0, bodyRows: 40 }, view: {} },
} as const
const ERLEDIGT = { result: { stdout: '', stderr: '', interrupted: false } }

type Aufruf = { argv?: readonly string[], stdin?: string, geoeffnet?: string, geschlossen?: string }

// Steht für die Engine: das Diff-Werkzeug antwortet mit `befund` (oder scheitert selbst mit
// `exitCode`), das Pane wird platziert.
function engine(on: On, befund: object, aufrufe: Aufruf[], exitCode = 0) {
  on('session.root', async () => ({ value: '/repo' }))
  on('process.run', async (_$, e) => {
    aufrufe.push({ argv: e.argv, stdin: e.init?.stdin })
    return { value: { exitCode, stdout: exitCode === 0 ? JSON.stringify(befund) : '',
                      stderr: exitCode === 0 ? '' : 'Traceback: kaputt',
                      isStdoutTruncated: false, isStderrTruncated: false } }
  })
  on('ui.open', async (_$, e) => { aufrufe.push({ geoeffnet: e.id }); return { value: { isPlaced: true } } })
  on('ui.close', async (_$, e) => { aufrufe.push({ geschlossen: e.id }); return { value: undefined } })
}

test('zeigt während des wartenden Aufrufs den Diff im Pane und schließt es danach', async ($, on) => {
  const aufrufe: Aufruf[] = []
  engine(on, BEFUND, aufrufe)
  let gestrichen: FoundElement | undefined
  let hinzu: FoundElement | undefined
  on('tool.call', async () => {
    // Hier wartet der Aufruf auf Freigabe und Ausführung: Jetzt muss das Pane den Diff zeigen.
    const pane = await $.ui.mount(PANE)
    gestrichen = await pane.find({ type: 'Text', text: /^Alt$/ })
    hinzu = await pane.find({ type: 'Text', text: /^Neu$/ })
    return ERLEDIGT
  })

  await $.tool.call({ tool: 'Bash', command: BEFEHL, tool_use_id: 'toolu_1' })

  expect(gestrichen?.props).toMatchObject({ strikethrough: true, weight: 'semibold' })
  expect(gestrichen?.props.backgroundColor).toBeDefined()
  expect(hinzu?.props.backgroundColor).toBeDefined()
  expect(hinzu?.props.backgroundColor).not.toBe(gestrichen?.props.backgroundColor)
  expect(aufrufe[0]).toEqual({ argv: ['python3', '-m', 'prozesscode.tracker_diff'], stdin: BEFEHL })
  expect(aufrufe).toContainEqual({ geoeffnet: 'tracker-diff' })
  expect(aufrufe.at(-1)).toEqual({ geschlossen: 'tracker-diff' })
})

const LANG = 'Gemessen in S130: ' + 'der Lauf bewertet nur einen Teil der Mutanten. '.repeat(40)
const LANGER_BEFUND = {
  dateien: [{
    datei: 'docs/kaizen/observations.md',
    bloecke: [
      { art: 'weg', zeilen: [[{ text: '• Beobachtung: ' + LANG, stil: [] }]] },
      { art: 'neu', zeilen: [[{ text: '• Beobachtung: kurz und neu', stil: [] }]] },
    ],
  }],
  fehler: null,
  warnung: null,
}

test('weist unten auf weiteren Inhalt hin, nur wenn er nicht ins Pane passt', async ($, on) => {
  engine(on, LANGER_BEFUND, [])
  type Baum = { props?: Record<string, unknown>, children: Baum[] }
  const gezeichnet: Record<string, Baum> = {}
  on('tool.call', async () => {
    for (const [name, bodyRows] of [['eng', 20], ['weit', 200]] as const) {
      const pane = await $.ui.mount({ ...PANE, props: { ...PANE.props, scroll: { offset: 0, bodyRows } } })
      gezeichnet[name] = (await pane.drawn()) as unknown as Baum
      await pane.unmount()
    }
    return ERLEDIGT
  })

  await $.tool.call({ tool: 'Bash', command: BEFEHL, tool_use_id: 'toolu_4' })

  // Eng: das Pane genau so hoch wie gemeldet, der Inhalt darin abgeschnitten, der Hinweis als
  // letzte Zeile – dort, wo der Inhalt weiterginge.
  expect(gezeichnet.eng).toMatchObject({ props: { height: 20 } })
  const [inhalt, hinweis] = gezeichnet.eng?.children ?? []
  expect(inhalt).toMatchObject({ props: { overflow: 'hidden', flexGrow: 1 } })
  expect(JSON.stringify(hinweis)).toContain('Mehr, als hier Platz hat')
  expect(JSON.stringify(gezeichnet.weit)).not.toContain('Mehr, als hier Platz hat')
})

test('lässt andere Bash-Befehle unberührt', async ($, on) => {
  const aufrufe: Aufruf[] = []
  engine(on, BEFUND, aufrufe)
  on('tool.call', async () => ERLEDIGT)

  await $.tool.call({ tool: 'Bash', command: 'python3 -m prozesscode.td get TD-S080-1', tool_use_id: 'toolu_2' })

  expect(aufrufe).toEqual([])
})

test('weist einen Befehl, der scheitern würde, ab – ohne Pane und ohne Freigabe-Prompt', async ($, on) => {
  // Ein Befehl, der nichts schreiben kann, braucht keine Freigabe.
  const aufrufe: Aufruf[] = []
  engine(on, { dateien: [], fehler: 'TD-S000-0 existiert nicht.', warnung: null }, aufrufe)
  let weitergereicht = false
  on('tool.call', async () => { weitergereicht = true; return ERLEDIGT })

  const ergebnis = await $.tool.call({ tool: 'Bash', command: 'python3 -m prozesscode.td set TD-S000-0 --titel X', tool_use_id: 'toolu_3' })

  expect('deny' in ergebnis ? ergebnis.deny : '').toContain('TD-S000-0 existiert nicht.')
  expect(weitergereicht).toBe(false)
  expect(aufrufe.filter((a) => a.geoeffnet)).toEqual([])
})

test('lässt den Befehl durch, wenn das Diff-Werkzeug selbst scheitert', async ($, on) => {
  // Gegenstück: Ein Fehler im Diff-Werkzeug sagt nichts über den Befehl – nur anzeigen, nie abweisen.
  engine(on, BEFUND, [], 1)
  let gezeichnet
  on('tool.call', async () => {
    const pane = await $.ui.mount(PANE)
    gezeichnet = await pane.find({ type: 'Text', text: /Diff nicht berechenbar/ })
    return ERLEDIGT
  })

  const ergebnis = await $.tool.call({ tool: 'Bash', command: BEFEHL, tool_use_id: 'toolu_5' })

  expect(gezeichnet).toBeDefined()
  expect(ergebnis).toEqual(ERLEDIGT)
})

function ganzerEintrag(art: 'neu' | 'weg') {
  return {
    dateien: [{
      datei: 'docs/kaizen/observations.md',
      bloecke: [{ art, eintrag: true, zeilen: [[{ text: 'OBS-S143-9 – Titel', stil: ['fett'] }],
                                              [{ text: '• Status: NEU', stil: [] }]] }],
    }],
    fehler: null,
    warnung: null,
  }
}

for (const [art, hinweis] of [['neu', /^Neuer Eintrag$/], ['weg', /^Eintrag wird entfernt$/]] as const) {
  test(`zeigt einen ganzen Eintrag (${art}) mit farbigem Hinweis oben und Zeilen ohne Hintergrund`, async ($, on) => {
    // Ein ganz grün bzw. rot hinterlegter Eintrag ist schwer zu lesen; der Hinweis sagt es einmal.
    engine(on, ganzerEintrag(art), [])
    let marke: FoundElement | undefined
    let zeile: FoundElement | undefined
    on('tool.call', async () => {
      const pane = await $.ui.mount(PANE)
      marke = await pane.find({ type: 'Text', text: hinweis })
      zeile = await pane.find({ type: 'Text', text: /^• Status: NEU$/ })
      return ERLEDIGT
    })

    await $.tool.call({ tool: 'Bash', command: BEFEHL, tool_use_id: 'toolu_6' })

    expect(marke?.props.backgroundColor).toBeDefined()
    expect(zeile?.props.backgroundColor).toBeUndefined()
  })
}
