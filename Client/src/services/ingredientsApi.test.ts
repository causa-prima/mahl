import { describe, it, expect } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import { deleteIngredient } from './ingredientsApi'

// ADR-S084-3 / ADR-S041-5-Addendum: Der If-Match-Header ist auf der gerenderten Komponente NICHT
// beobachtbar – ob er mitgeht oder fehlt, ändert nichts am DOM (der MSW-Handler des Komponenten-
// Tests antwortet in beiden Fällen 204). Geprüft wird er daher auf der obersten Schicht, auf der er
// beobachtbar ist: der HTTP-Schnittstelle des Service-Clients. Kein vi.mock – reiner HTTP-Kontrakt
// über MSW (ADR-S057-1).
// Realistische ETag-Form: per-Zeile-xmin, lowercase hex in Quotes (ADR-S106-1 / ADR-S108-1).
const ETAG = '"0000a1b2"'

describe('deleteIngredient', () => {
  it('sendet DELETE auf die Zutat mit dem Zeilen-ETag als If-Match', async () => {
    // Given: der Server nimmt das DELETE entgegen und hält Route + If-Match fest
    const capture: { current: { id: string; ifMatch: string | null } | undefined } = { current: undefined }
    server.use(
      http.delete('/api/ingredients/:id', ({ params, request }) => {
        // eslint-disable-next-line functional/immutable-data -- Capture: Request für Then-Block festhalten
        capture.current = { id: String(params.id), ifMatch: request.headers.get('If-Match') }
        return new HttpResponse(null, { status: 204 })
      }),
    )

    // When: die Zutat "42" mit ihrem Zeilen-ETag gelöscht wird
    await deleteIngredient('42', ETAG)

    // Then: das DELETE ging an genau diese Zutat und trug den ETag verbatim als If-Match
    //   (ADR-S058-1: mutierender Single-Resource-Endpoint verlangt If-Match, sonst 428)
    expect(capture.current).toEqual({ id: '42', ifMatch: ETAG })
  })
})
