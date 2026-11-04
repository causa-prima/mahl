// Was `python3 -m prozesscode.session-agenda --ueberblick` liefert (session-agenda.ueberblick).
export type Ueberblick = {
  aufgabe: string | null
  weg: string | null
  phase: string | null
  story: string | null
  lauf: string | null
  nachrangig: string[]
}

// Lädt (noch kein Ergebnis), da (Überblick), kaputt (Grund) – oder ausgeblendet nach dem ersten Prompt.
export type Stand =
  | { art: 'laedt' }
  | { art: 'da'; ueberblick: Ueberblick }
  | { art: 'kaputt'; grund: string }
  | { art: 'aus' }

declare module 'claude-code' {
  interface PluginState {
    'naechste-aufgabe': { stand: Stand }
  }
}
