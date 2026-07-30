import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import type { Result, ResultAsync } from 'neverthrow'

// ADR-S083-2: bewusst minimal modelliert – kein MutationState-Discriminated-Union, kein
// matchState, kein throwOnError. `error`/`isPending`/`reset` decken genau das ab, was die
// bisher umgesetzten US-904-Szenarien beobachten (Erfolg, Feld-Fehler, Pending, Reset beim
// Schließen); die volle Union bleibt für @US-904-error/resilience aufgeschoben. Details/
// Begründung: docs/history/adr.md (ADR-S083-2).
// run-11: `onSuccess` reicht den Erfolgswert durch (statt ihn zu verschlucken) – kein neuer
// Zustand, keine neue Union, nur der bereits vorhandene Ok-Wert wird sichtbar. Getrieben vom
// Reaktivierungs-Konflikt-Szenario, das den gespeicherten Stand für die Snackbar braucht
// (ADR-S111-3). Bestehende Aufrufer mit 0-Parameter-Callback bleiben typkorrekt zuweisbar.
export function useResultMutation<TData, TError, TVariables>(
  fn: (variables: TVariables) => ResultAsync<TData, TError>,
  onSuccess: (data: TData) => void,
): readonly [(variables: TVariables) => void, TError | undefined, boolean, () => void] {
  const [error, setError] = useState<TError | undefined>(undefined)
  const mutation = useMutation<Result<TData, TError>, Error, TVariables>({
    // Promise.resolve flacht die ResultAsync (thenable) zu Promise<Result> ab –
    // React Query erwartet ein echtes Promise, nicht das ResultAsync selbst.
    mutationFn: (variables: TVariables) => Promise.resolve(fn(variables)),
    onSuccess: (result) => {
      result.match(
        (data) => {
          setError(undefined)
          onSuccess(data)
        },
        (e) => { setError(e) },
      )
    },
  })

  const reset = () => { setError(undefined) }

  return [mutation.mutate, error, mutation.isPending, reset]
}
