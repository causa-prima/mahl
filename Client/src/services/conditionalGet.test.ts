import { describe, it, expect, beforeEach } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import { conditionalGetJson, resetConditionalGetCache } from './conditionalGet'

// Der Conditional-GET-Cache ist modul-lokal und überlebt zwischen Tests.
// Ohne Reset würde ein Test (gecachter ETag/Body) den nächsten beeinflussen
// (z.B. ein gesendeter If-None-Match-Header aus einem Vorlauf-Test).
// resetConditionalGetCache() stellt pro Test einen leeren Ausgangszustand her.
beforeEach(() => {
  resetConditionalGetCache()
})

type Item = { readonly id: string; readonly name: string }

const URL = '/api/items'

// Realistische ETag-Form: das Backend bildet den Collection-ETag per
// Convert.ToHexString(SHA256.HashData(...)) (ADR-S058-3) -> Uppercase-Hex in Quotes.
// Der Helper echo't verbatim (RFC 7232), normalisiert das Casing also nicht.
const ETAG_1 = '"A3F2C1B47E9D5068A1B2C3D4E5F60718293A4B5C6D7E8F90A1B2C3D4E5F60718"'
const ETAG_2 = '"00112233445566778899AABBCCDDEEFF00112233445566778899AABBCCDDEEFF"'

describe('conditionalGetJson', () => {
  it('sendet beim ersten GET ohne Cache keinen If-None-Match-Header und liefert den 200-Body', async () => {
    // Given: kein Cache-Eintrag; Server liefert 200 mit Body und ETag
    const capture: { current: string | null | undefined } = { current: undefined }
    const body: readonly Item[] = [{ id: '1', name: 'Tomaten' }]
    server.use(
      http.get(URL, ({ request }) => {
        // eslint-disable-next-line functional/immutable-data -- Capture: Request-Header für Then-Block festhalten
        capture.current = request.headers.get('If-None-Match')
        return HttpResponse.json(body, { headers: { ETag: ETAG_1 } })
      }),
    )

    // When: erster conditionalGetJson-Aufruf
    const result = await conditionalGetJson<readonly Item[]>(URL)

    // Then: kein If-None-Match gesendet (es gab keinen ETag zu schicken)
    expect(capture.current).toBeNull()
    // Then: der 200-Body wird als ok zurückgegeben
    expect(result._unsafeUnwrap()).toEqual(body)
  })

  it('sendet beim zweiten GET den zuvor erhaltenen ETag als If-None-Match', async () => {
    // Given: erster GET liefert 200 mit ETag ETAG_1 -> wird gecacht
    const capture: { current: string | null | undefined } = { current: undefined }
    server.use(
      http.get(URL, ({ request }) => {
        // eslint-disable-next-line functional/immutable-data -- Capture: Request-Header für Then-Block festhalten
        capture.current = request.headers.get('If-None-Match')
        return HttpResponse.json([{ id: '1', name: 'Tomaten' }], { headers: { ETag: ETAG_1 } })
      }),
    )
    await conditionalGetJson<readonly Item[]>(URL)

    // When: zweiter Aufruf für dieselbe URL
    await conditionalGetJson<readonly Item[]>(URL)

    // Then: If-None-Match trägt den ETag verbatim (inkl. Quotes + Casing, RFC 7232)
    expect(capture.current).toBe(ETAG_1)
  })
})

describe('conditionalGetJson – Cache & 304', () => {
  it('liefert bei 304 den gecachten Body aus der vorherigen 200-Antwort', async () => {
    // Given: erster GET liefert 200 mit Body + ETag; danach antwortet der Server 304
    const cachedBody: readonly Item[] = [{ id: '1', name: 'Tomaten' }]
    // eslint-disable-next-line functional/no-let -- MSW-Handler-Umschaltung: 200 beim ersten, 304 beim zweiten GET
    let firstCall = true
    server.use(
      http.get(URL, () => {
        if (firstCall) {
          firstCall = false
          return HttpResponse.json(cachedBody, { headers: { ETag: ETAG_1 } })
        }
        return new HttpResponse(null, { status: 304 })
      }),
    )
    const first = await conditionalGetJson<readonly Item[]>(URL)
    expect(first._unsafeUnwrap()).toEqual(cachedBody)

    // When: zweiter Aufruf -> Server antwortet 304 (kein Body)
    const second = await conditionalGetJson<readonly Item[]>(URL)

    // Then: der gecachte Body wird als ok zurückgegeben
    expect(second._unsafeUnwrap()).toEqual(cachedBody)
  })

  it('aktualisiert bei 200 mit neuem ETag den Cache, sodass der Folge-Request den neuen ETag sendet', async () => {
    // Given: erster GET liefert ETAG_1, zweiter GET liefert 200 mit neuem ETAG_2
    const captures: string[] = []
    const etagsPerCall = [ETAG_1, ETAG_2] as const
    // eslint-disable-next-line functional/no-let -- MSW-Handler-Umschaltung: ETag pro Aufruf wechseln
    let call = 0
    server.use(
      http.get(URL, ({ request }) => {
        // eslint-disable-next-line functional/immutable-data -- Capture: gesendete If-None-Match-Header sammeln
        captures.push(request.headers.get('If-None-Match') ?? '<none>')
        const etag = etagsPerCall[call] ?? ETAG_2
        call += 1
        return HttpResponse.json([{ id: '1', name: 'Tomaten' }], { headers: { ETag: etag } })
      }),
    )
    await conditionalGetJson<readonly Item[]>(URL) // 200 -> cacht ETAG_1
    await conditionalGetJson<readonly Item[]>(URL) // 200 -> cacht ETAG_2

    // When: dritter Aufruf
    await conditionalGetJson<readonly Item[]>(URL)

    // Then: erster Request ohne ETag, zweiter mit ETAG_1, dritter mit dem aktualisierten ETAG_2
    expect(captures).toEqual(['<none>', ETAG_1, ETAG_2])
  })
})
