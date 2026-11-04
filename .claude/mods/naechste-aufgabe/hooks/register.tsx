// Zeigt beim Session-Start über dem Prompt, was als Nächstes ansteht.
//
// Die Session-Agenda (prozesscode/session-agenda.py) geht per SessionStart-Hook nur ins Modell;
// der User sah nichts, bis der Agent loslegte. Dieses Band zeigt denselben Stand – die
// Auswahl trifft `session-agenda --ueberblick` mit der Rangfolge der Injektion, hier wird nur
// gezeichnet. Mit dem ersten Prompt ist der Stand veraltet, das Band verschwindet.
import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Stand, Ueberblick } from '../types'

const stand = atom({ plugin: 'naechste-aufgabe', key: 'stand' } as const, { art: 'aus' } as Stand)

export const BEFEHL = ['python3', '-m', 'prozesscode.session-agenda', '--ueberblick'] as const
const NACHSEHEN = 'python3 -m prozesscode.session-agenda --ueberblick'

export async function lies($: EngineInterface): Promise<Stand> {
  try {
    const lauf = await $.process.run([...BEFEHL], { cwd: await $.session.root(), timeoutMs: 20000 })
    if (lauf.exitCode !== 0) {
      return { art: 'kaputt', grund: `Exit ${lauf.exitCode}: ${lauf.stderr.trim().slice(-200)}` }
    }
    return { art: 'da', ueberblick: JSON.parse(lauf.stdout) as Ueberblick }
  } catch (fehler) {
    return { art: 'kaputt', grund: String(fehler) }
  }
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const ergebnis = await next(e)
    if (!e.isInteractive) return ergebnis
    await update($, stand, () => ({ art: 'laedt' }))
    // Im Hintergrund: Die Agenda braucht rund zwei Sekunden, der Start soll darauf nicht warten.
    $.clock.after(0, async () => {
      const neu = await lies($)
      await update($, stand, alt => (alt.art === 'aus' ? alt : neu))
    })
    return ergebnis
  })

  on('prompt.submit', async ($, e, next) => {
    await update($, stand, () => ({ art: 'aus' }))
    return next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const s = await read($, stand)
    if (e.props.hasSurvey || s.art === 'aus') return next(e)
    const { Box, Text } = $.ui.resolve(e)

    if (s.art === 'laedt') {
      return <Box><Text dimColor>Als Nächstes: Session-Agenda wird gelesen …</Text></Box>
    }
    if (s.art === 'kaputt') {
      return (
        <Box flexDirection="column">
          <Text color="warning">Als Nächstes: Session-Agenda nicht lesbar – {s.grund}</Text>
          <Text dimColor>Nachsehen: {NACHSEHEN}</Text>
        </Box>
      )
    }
    const u = s.ueberblick
    const lauf = [u.story && `Story ${u.story}`, u.lauf && `nächster Lauf ${u.lauf}`]
      .filter(Boolean).join(' · ')
    return (
      <Box flexDirection="column">
        <Text>
          <Text bold>Als Nächstes: </Text>
          {u.aufgabe ?? 'keine Aufgabe erzwungen – frei für das, was ansteht'}
          {u.weg ? ` → ${u.weg}` : ''}
        </Text>
        {lauf ? <Text dimColor>{lauf}</Text> : null}
        {u.nachrangig.length > 0
          ? <Text dimColor>Außerdem offen: {u.nachrangig.join(', ')}</Text>
          : null}
      </Box>
    )
  })
}
