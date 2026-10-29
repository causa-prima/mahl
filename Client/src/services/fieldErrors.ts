import { errAsync, ResultAsync } from 'neverthrow'
import type { ApiError } from '../types/apiError'

// ADR-S090-1: 422-Body ist feld-keyed. Das Frontend konsumiert ausschließlich `errors`.
type FieldErrorBody = { readonly errors: Readonly<Record<string, readonly string[]>> }

// ADR-S090-1: 422 -> feld-keyed Validierungsfehler als Err.
export function toFieldErrors<T>(response: Response): ResultAsync<T, ApiError> {
  return ResultAsync.fromSafePromise(response.json() as Promise<FieldErrorBody>).andThen((body) =>
    errAsync<T, ApiError>({ kind: 'FieldErrors', fields: body.errors }),
  )
}
