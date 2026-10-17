// Zeigt bei Tracker-Schreibbefehlen (obs|lessons|td|oq add|set|remove) den Diff der Datei in
// einem Pane, solange der Aufruf auf Freigabe und Ausführung wartet.
//
// Nur Anzeige: Die Freigabe bleibt beim PreToolUse-Hook und seinem Prompt, den kein Mod
// gestalten kann. Berechnet wird der Diff in Python (prozesscode/tracker_diff.py), aus dem
// echten Werkzeug-Code mit abgefangenem Schreiben – hier wird er nur gezeichnet.
const TRACKER = /^python3 -m prozesscode\.(obs|lessons|td|oq) (add|set|remove)\b/
const PANE = 'tracker-diff'

// Je wartendem Aufruf sein Befund; das Pane zeigt den jüngsten.
const offen = new Map()

async function berechne($, command) {
  try {
    const lauf = await $.process.run(['python3', '-m', 'prozesscode.tracker_diff'],
      { stdin: command, cwd: await $.session.root(), timeoutMs: 10000 })
    if (lauf.exitCode !== 0) {
      return { dateien: [], fehler: 'tracker_diff endete mit Exit ' + lauf.exitCode + ': ' + lauf.stderr.trim().slice(-400) }
    }
    return JSON.parse(lauf.stdout)
  } catch (fehler) {
    return { dateien: [], fehler: 'tracker_diff nicht aufrufbar: ' + fehler }
  }
}

// Stile aus tracker_diff.py → Text-Props. ANSI-Farben: Im Pane erscheinen alle Farben gedämpft
// (Hex, Theme-Schlüssel, ANSI und invers am echten Terminal verglichen); ANSI hatte dort den
// meisten Kontrast.
const STIL = {
  fett: { weight: 'semibold' },
  code: { color: 'suggestion' },
  kursiv: { italic: true },
  weg: { backgroundColor: 'red', color: 'white', strikethrough: true },
  neu: { backgroundColor: 'green', color: 'white' },
}
// Ganze neue oder gelöschte Zeilen: Marke vorn, die ganze Zeile in der Farbe.
const ZEILE = {
  neu: { marke: '+ ', props: STIL.neu },
  weg: { marke: '− ', props: STIL.weg },
}

// Grob, wie viele Zeilen der Inhalt im Pane braucht, aus der Geometrie, die die Engine meldet
// (ein Zeichen = eine Zelle, Umbruch an Wortgrenzen nicht nachgebildet). Scrollen geht nicht,
// solange der Prompt die Tastatur hat – darum der Hinweis, wenn es nicht passt.
function geschaetzteZeilen(befund, spalten) {
  let zeilen = 2 * befund.dateien.length
  for (const datei of befund.dateien) {
    for (const block of datei.bloecke) {
      zeilen += 1
      for (const zeile of block.zeilen) {
        const laenge = zeile.reduce((n, s) => n + s.text.length, 2)
        zeilen += Math.max(1, Math.ceil(laenge / Math.max(spalten, 20)))
      }
    }
  }
  return zeilen
}


function zeichneZeile(Text, art, zeile, key) {
  const stuecke = zeile.map((s) => Text(Object.assign({ children: [s.text] }, ...s.stil.map((n) => STIL[n] || {}))))
  const rahmen = ZEILE[art]
  if (!rahmen) return Text({ key, children: stuecke.length ? stuecke : [' '] })
  return Text({ key, ...rahmen.props, children: [rahmen.marke, ...stuecke] })
}

export function register(on) {
  on('tool.call', { tool: 'Bash' }, async ($, e, next) => {
    if (!TRACKER.test(e.command)) return next(e)
    const befund = await berechne($, e.command)
    if (!befund) return next(e)
    offen.set(e.tool_use_id, befund)
    await $.ui.open({ id: PANE, title: 'Tracker-Änderung' })
    $.ui.invalidate('ui.render')
    try {
      // Das Warten auf next zählt nicht gegen das Zeitlimit des Hooks: Prompt und Ausführung laufen darin.
      return await next(e)
    } finally {
      offen.delete(e.tool_use_id)
      if (offen.size === 0) await $.ui.close({ id: PANE })
      else $.ui.invalidate('ui.render')
    }
  }).catch(async (_$, e, next) => next(e))

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e, next) => {
    const befund = [...offen.values()].pop()
    if (!befund) return next(e)
    const { Box, Text } = $.ui.resolve(e)
    const kinder = []
    if (befund.fehler) kinder.push(Text({ key: 'fehler', color: 'error', children: ['Der Befehl würde scheitern: ' + befund.fehler] }))
    if (befund.warnung) kinder.push(Text({ key: 'warnung', color: 'warning', children: ['⚠ ' + befund.warnung] }))
    for (const datei of befund.dateien) {
      kinder.push(Text({ key: 'datei:' + datei.datei, weight: 'semibold', underline: true, children: [datei.datei] }))
      datei.bloecke.forEach((block, b) => {
        const zeilen = block.zeilen.map((zeile, z) => zeichneZeile(Text, block.art, zeile, datei.datei + ':' + b + ':' + z))
        kinder.push(Box({ key: 'block:' + datei.datei + ':' + b, flexDirection: 'column', children: zeilen }))
      })
    }
    if (kinder.length === 0) kinder.push(Text({ key: 'leer', children: ['Der Befehl ändert keine Datei.'] }))
    const zeilen = e.props.scroll && e.props.scroll.bodyRows
    if (!zeilen || geschaetzteZeilen(befund, e.props.bodyColumns) <= zeilen) {
      return Box({ flexDirection: 'column', gap: 1, children: kinder })
    }
    // Passt es nicht: das Pane genau so hoch wie gemeldet, die Engine schneidet den Inhalt ab,
    // und die letzte Zeile sagt es – dort, wo der Inhalt weiterginge.
    return Box({ flexDirection: 'column', height: zeilen, children: [
      Box({ key: 'inhalt', flexDirection: 'column', gap: 1, flexGrow: 1, overflow: 'hidden', children: kinder }),
      Text({ key: 'zuviel', dimColor: true,
        children: ['↓ Mehr, als hier Platz hat – Fenster vergrößern (scrollen geht bei offenem Prompt nicht)'] }),
    ] })
  })
}
