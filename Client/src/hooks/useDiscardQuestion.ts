import { useEffect, useRef } from 'react'
import { useBlocker } from 'react-router'

export type LeaveRelease = {
  readonly isAllowed: () => boolean
  readonly leaveWithoutQuestion: (leave: () => void) => void
}

// Freigabe der Navigation für die Weiterleitung nach dem Speichern. Eigener Hook, weil der Aufrufer sie schon
// für das Speichern braucht, `useDiscardQuestion` aber dessen Zustand (`saving`) – sonst wäre die Reihenfolge zirkulär.
//
// Der Merker ist nötig, weil die Weiterleitung aus dem onSuccess kommt: Dort kennt die Blocker-Funktion noch
// `saving === true` (vor dem nächsten Rendern wird nichts neu registriert), die Weiterleitung sperrte sich sonst
// selbst. Er wird nicht zurückgesetzt: Er ist nur nach einem Speichern gesetzt, danach folgt nur noch das Verlassen
// der Seite.
export function useLeaveRelease(): LeaveRelease {
  const allowed = useRef(false)
  return {
    isAllowed: () => allowed.current,
    leaveWithoutQuestion: (leave: () => void) => {
      // eslint-disable-next-line functional/immutable-data -- Flag für den Blocker, wird erst beim Navigieren gelesen
      allowed.current = true
      leave()
    },
  }
}

type DiscardQuestionState = {
  readonly hasInput: boolean
  readonly saving: boolean
}

// ADR-S135-4, ADR-S135-6: Wer mit Eingaben wegnavigiert (Abbrechen, Navigationsleiste, Browser-Zurück), wird
// gefragt. Der Blocker hält die Navigation an; „Verwerfen" setzt sie fort, „Weiter bearbeiten" bricht sie ab.
// Während des Speicherns (`saving`) ist die Navigation still gesperrt, ohne Nachfrage: „Verwerfen" wäre
// irreführend, weil das Rezept trotzdem entsteht (ADR-S135-6). So kann das Speicherergebnis nie nach dem Verlassen
// eintreffen (ADR-S135-4). Ohne Eingaben bleibt der Weg auch während des Speicherns frei – ein leeres Formular lehnt
// der Server immer ab, es entsteht nichts (ADR-S135-6, Addendum S151). Die Weiterleitung nach dem Speichern gibt
// `release` frei.
export function useDiscardQuestion(
  { hasInput, saving }: Readonly<DiscardQuestionState>,
  release: Readonly<LeaveRelease>,
) {
  const blocker = useBlocker(() => hasInput && !release.isAllowed())

  const blocked = blocker.state === 'blocked' ? blocker : undefined

  // Ein während des Speicherns angehaltener Versuch wird still zurückgenommen. Bliebe er stehen, öffnete sich die
  // Nachfrage nach einem fehlgeschlagenen Speichern nachträglich (`saving` wird false).
  useEffect(() => {
    (saving ? blocked : undefined)?.reset()
  }, [saving, blocked])

  return {
    // `!saving`: Der Effect läuft erst nach dem Rendern – ohne die Bedingung stünde die Nachfrage für dieses eine
    // Rendern zwischen Anhalten und Zurücknehmen kurz auf.
    open: blocked !== undefined && !saving,
    keepEditing: () => { blocked?.reset() },
    discard: () => { blocked?.proceed() },
  }
}
