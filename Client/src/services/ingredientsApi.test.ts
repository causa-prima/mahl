import { describe, it, expect } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import { deleteIngredient, restoreIngredient } from './ingredientsApi'

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

// ADR-S084-3-Addendum: run-11 „Reaktivierung" – ob restoreIngredient eine 200-Antwort korrekt
// als Reaktivierung (nicht als Konflikt) erkennt, ist auf der gerenderten Komponente NICHT
// killbar. Ein falsch als Konflikt erkannter 200-Fall führt in IngredientsPage zu einem Crash
// beim Aufbau der Konflikt-Snackbar (Zugriff auf ein Feld, das die 200-Antwort nicht hat) – React
// Query fängt Fehler aus dem onSuccess-Callback intern ab, sie werden weder sichtbar noch lassen
// sie einen Komponenten-Test fehlschlagen. `closeDialog`/die Listen-Aktualisierung sind zu diesem
// Zeitpunkt bereits gelaufen (kommen ohnehin aus dem GET-Refetch, nicht aus dem geparsten Wert) –
// der Bug bliebe für jeden Komponenten-Test unsichtbar. Getestet daher auf der obersten Schicht,
// auf der er beobachtbar ist: dem Rückgabewert des Service-Clients selbst (reiner HTTP-Kontrakt
// über MSW, kein vi.mock, ADR-S057-1).
describe('restoreIngredient', () => {
  it('erkennt eine 200-Antwort als Reaktivierung, nicht als Konflikt', async () => {
    // Given: der Server antwortet 200 mit dem reaktivierten Datensatz (flache Form, kein
    //   verschachteltes "ingredient"-Feld – das trägt nur die 409-Antwort, ADR-S111-1)
    const restored = { id: '1', name: 'Mehl', baseUnit: 'g', etag: '"00000001"' }
    server.use(http.post('/api/ingredients/:id/restore', () => HttpResponse.json(restored, { status: 200 })))

    // When: die Zutat "1" reaktiviert wird
    const result = await restoreIngredient('1', 'Mehl', 'g')

    // Then: das Ergebnis ist eindeutig eine Reaktivierung mit dem reaktivierten Datensatz –
    //   nicht fälschlich ein Konflikt (der Frontend-Typ trägt für den Konflikt andere Felder)
    expect(result._unsafeUnwrap()).toEqual({ kind: 'Restored', ingredient: restored })
  })
})
