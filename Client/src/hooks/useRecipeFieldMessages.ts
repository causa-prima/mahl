import { useEffect, useMemo, useRef } from 'react'
import type { RefObject } from 'react'
import { messagesByFieldIndex } from '../domain/recipe'
import { instructionMessageAtSentIndex } from '../services/fieldErrors'
import type { ApiError } from '../types/apiError'

export type FieldMessage<Element extends HTMLElement> = {
  readonly message: string | undefined
  readonly ref: RefObject<Element | null>
}

// eslint-disable-next-line functional/prefer-immutable-types -- Ref-Callback erhält das DOM-Element
export type InputRefCallback = (element: HTMLTextAreaElement | null) => void

// ADR-S135-4 (Addendum S148): Das Zutatenfeld zeigt alle Meldungen des Servers in dessen Reihenfolge.
export type FieldMessageList<Element extends HTMLElement> = {
  readonly messages: readonly string[]
  readonly ref: RefObject<Element | null>
}

// Stabile Referenz für „keine Meldungen": `?? []` erzeugte je Rendern ein neues Array, und die useMemo-Abhängigkeiten
// (Fokus-Reihenfolge, Rückgabe) liefen jedes Mal neu.
const noMessages: readonly string[] = []

type FocusCandidate = { readonly message: string | undefined; readonly element: () => HTMLElement | null | undefined }

// ADR-S135-4: Nach einem Fehler erhält das erste Feld mit Meldung den Fokus. `candidates` steht in der
// Reihenfolge der Felder im Formular und muss memoisiert sein (sonst fokussiert jedes Rendern erneut).
function useFocusFirstMessage(error: ApiError | undefined, candidates: readonly FocusCandidate[]) {
  useEffect(() => {
    candidates.find(({ message }) => message !== undefined)?.element()?.focus()
    // `error` ist je Speichern ein neues Objekt: auch eine gleiche Meldung holt den Fokus erneut.
  }, [error, candidates])
}

// Meldungen und Fokus des Formulars „Rezept anlegen".
// ADR-S090-1: Meldungen kommen feld-keyed vom Server; je Feld wird die erste angezeigt.
// ADR-S144-1: `sentFieldIndexes` ordnet die Meldungen zu `steps[i].instruction` dem Formularfeld zu, aus dem
// der Schritt stammt (Stand beim Speichern).
export function useRecipeFieldMessages(error: ApiError | undefined, sentFieldIndexes: readonly number[]) {
  const titleRef = useRef<HTMLInputElement>(null)
  const ingredientsRef = useRef<HTMLTextAreaElement>(null)
  const stepInputs = useRef<(HTMLTextAreaElement | null)[]>([])
  const fields = error?.kind === 'FieldErrors' ? error.fields : undefined
  const titleMessage = fields?.title?.[0]
  const ingredientsMessages = fields?.ingredients ?? noMessages
  const stepsMessage = fields?.steps?.[0]
  const instructionMessages = useMemo(
    () => messagesByFieldIndex(sentFieldIndexes, (sentIndex) => instructionMessageAtSentIndex(fields, sentIndex)),
    [fields, sentFieldIndexes],
  )

  const firstInstruction = useMemo(() => [...instructionMessages][0], [instructionMessages])
  const focusOrder = useMemo<readonly FocusCandidate[]>(() => [
    { message: titleMessage, element: () => titleRef.current },
    { message: ingredientsMessages[0], element: () => ingredientsRef.current },
    { message: stepsMessage, element: () => stepInputs.current[0] },
    // Nur die erste Anweisungs-Meldung zählt (Formularreihenfolge): sie erhält den Fokus.
    { message: firstInstruction?.[1], element: () => stepInputs.current[firstInstruction?.[0] ?? 0] },
  ], [titleMessage, ingredientsMessages, stepsMessage, firstInstruction])
  useFocusFirstMessage(error, focusOrder)

  // useMemo: Der React-Compiler-Lint (react-hooks/refs) akzeptiert Objekte mit Refs im Rückgabewert nur memoisiert.
  return useMemo(() => ({
    title: { message: titleMessage, ref: titleRef },
    ingredients: { messages: ingredientsMessages, ref: ingredientsRef },
    steps: {
      message: stepsMessage,
      instructionMessage: (fieldIndex: number) => instructionMessages.get(fieldIndex),
      inputRef: (fieldIndex: number): InputRefCallback => (element) => {
        // eslint-disable-next-line functional/immutable-data -- Ref-Ablage der Eingabefelder (Fokusziele)
        stepInputs.current[fieldIndex] = element
      },
    },
  }), [titleMessage, ingredientsMessages, stepsMessage, instructionMessages])
}
