import { useState } from 'react'

// ADR-S135-4: Mit Eingaben fragt Abbrechen nach („Eingaben verwerfen?"), ohne führt es direkt über `leave` weg.
export function useDiscardQuestion(hasInput: boolean, leave: () => void) {
  const [open, setOpen] = useState(false)

  return {
    open,
    cancel: hasInput ? () => { setOpen(true) } : leave,
    keepEditing: () => { setOpen(false) },
  }
}
