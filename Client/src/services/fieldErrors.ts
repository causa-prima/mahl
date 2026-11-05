import { errAsync, ResultAsync } from 'neverthrow'
import type { ApiError } from '../types/apiError'

// ADR-S090-1: 422-Body ist feld-keyed. Das Frontend konsumiert ausschließlich `errors`.
export type FieldErrors = Readonly<Record<string, readonly string[]>>
type FieldErrorBody = { readonly errors: FieldErrors }

// ADR-S144-1: Key-Format `steps[i].instruction` mit i = Index in der gesendeten Schrittliste. Liefert die erste
// Meldung zur Anweisung des gesendeten Schritts mit diesem Index (oder undefined).
export const instructionMessageAtSentIndex = (
  fields: FieldErrors | undefined,
  sentIndex: number,
): string | undefined => fields?.[`steps[${String(sentIndex)}].instruction`]?.[0]

// ADR-S090-1: 422 -> feld-keyed Validierungsfehler als Err.
export function toFieldErrors<T>(response: Response): ResultAsync<T, ApiError> {
  return ResultAsync.fromSafePromise(response.json() as Promise<FieldErrorBody>).andThen((body) =>
    errAsync<T, ApiError>({ kind: 'FieldErrors', fields: body.errors }),
  )
}
