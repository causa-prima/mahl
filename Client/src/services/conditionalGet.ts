import { ResultAsync } from 'neverthrow'
import type { ApiError } from '../types/apiError'

type CacheEntry = { readonly etag: string; readonly body: unknown }

// Modul-lokaler Cache URL -> { etag, body }. react-query macht keine HTTP-Conditional-
// Requests; dieser Cache ist der Konsument des Backend-ETags (ADR-S058-1/-3). Ein
// veränderlicher Modul-Singleton ist hier der Kern der Design-Entscheidung (ein Cache,
// der Requests überdauert) – functional/immutable-data wird daher gezielt unterdrückt.
const cache = new Map<string, CacheEntry>()

// Test-Isolation: Der Cache überlebt zwischen Tests (Modul-Singleton). Ohne Reset würde
// ein gecachter ETag/Body einen Folge-Test beeinflussen.
export function resetConditionalGetCache(): void {
  // eslint-disable-next-line functional/immutable-data -- gewollte Cache-Mutation (s.o.)
  cache.clear()
}

// ETag verbatim cachen (RFC 7232, keine Normalisierung) – nur wenn der Server einen sendet.
function cache200(url: string, body: unknown, etag: string | null): void {
  // eslint-disable-next-line functional/no-conditional-statements, functional/immutable-data -- gewollte Cache-Mutation (s.o.)
  if (etag) cache.set(url, { etag, body })
}

async function requestJson<T>(url: string, cached: CacheEntry | undefined): Promise<T> {
  // If-None-Match nur senden, wenn ein gecachter ETag existiert (verbatim, RFC 7232).
  const headers = cached ? { 'If-None-Match': cached.etag } : undefined
  const response = await fetch(url, { headers })
  // 304 kommt real nur, wenn wir If-None-Match aus einem Cache-Eintrag gesendet haben –
  // daher ist `cached` in diesem Zweig per Design vorhanden (YAGNI: kein Defensiv-Pfad).
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion -- 304 impliziert Cache-Eintrag
  if (response.status === 304) return cached!.body as T
  const body = (await response.json()) as T
  cache200(url, body, response.headers.get('ETag'))
  return body
}

export function conditionalGetJson<T>(url: string): ResultAsync<T, ApiError> {
  return ResultAsync.fromPromise(requestJson<T>(url, cache.get(url)), (e) => ({
    kind: 'Unexpected',
    message: String(e),
  }))
}
