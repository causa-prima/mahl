import { useEffect, useMemo, useRef } from 'react'
import type { RefObject } from 'react'
import type { ApiError } from '../types/apiError'

export type FieldMessage<Element extends HTMLElement> = {
  readonly message: string | undefined
  readonly ref: RefObject<Element | null>
}

// Meldungen und Fokus des Formulars „Rezept anlegen".
// ADR-S090-1: Meldungen kommen feld-keyed vom Server; je Feld wird die erste angezeigt.
// ADR-S135-4: Nach einem Fehler erhält das erste fehlerhafte Feld den Fokus (Titel, Zutaten, Schritte).
export function useRecipeFieldMessages(error: ApiError | undefined) {
  const titleRef = useRef<HTMLInputElement>(null)
  const ingredientsRef = useRef<HTMLTextAreaElement>(null)
  const firstStepRef = useRef<HTMLTextAreaElement>(null)
  const fields = error?.kind === 'FieldErrors' ? error.fields : undefined
  const titleMessage = fields?.title?.[0]
  const ingredientsMessage = fields?.ingredients?.[0]
  const stepsMessage = fields?.steps?.[0]
  const field = useMemo(() => ({
    title: { message: titleMessage, ref: titleRef },
    ingredients: { message: ingredientsMessage, ref: ingredientsRef },
    steps: { message: stepsMessage, ref: firstStepRef },
  }), [titleMessage, ingredientsMessage, stepsMessage])

  useEffect(() => {
    const inFocusOrder = [field.title, field.ingredients, field.steps]
    inFocusOrder.find(({ message }) => message !== undefined)?.ref.current?.focus()
    // `error` ist je Speichern ein neues Objekt: auch eine gleiche Meldung holt den Fokus erneut.
  }, [error, field])

  return field
}
