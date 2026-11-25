import { errAsync, okAsync, ResultAsync } from 'neverthrow'
import { toUnexpectedError } from '../types/apiError'
import type { ApiError } from '../types/apiError'

// Request ohne Body und ohne If-Match (PUT, DELETE, POST). Jede Nicht-2xx-Antwort ist ein Fehler:
// der Zustand ändert sich dann nicht.
export function sendWithoutBody(method: 'PUT' | 'DELETE' | 'POST', url: string): ResultAsync<Response, ApiError> {
  return ResultAsync.fromPromise(fetch(url, { method }), toUnexpectedError).andThen((response) =>
    response.ok
      ? okAsync<Response, ApiError>(response)
      : errAsync<Response, ApiError>({ kind: 'Unexpected', message: `${method} ${url} fehlgeschlagen: ${String(response.status)}` }),
  )
}
