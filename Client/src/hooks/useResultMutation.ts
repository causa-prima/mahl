import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import type { Result, ResultAsync } from 'neverthrow'

// US-904 Zutat anlegen: success-Seiteneffekt (onSuccess) + beobachtbarer Fehlerzustand.
// ADR-S083-2: der aufgeschobene Error-State wird hier eingelöst. Domain-Err reist als
// Result durch React Querys Success-Pfad (kein throw); onSuccess feuert NUR bei Ok,
// der Err-Wert wird als `error` zurückgegeben.
// ADR-S083-2-Addendum (run-2, "Speichern-Button deaktiviert während des Speicherns"):
// der pending-Teil der dort aufgeschobenen vollen MutationState-Union wird hier minimal
// eingelöst (nur `isPending`, aus `mutation.isPending`) – kein MutationState-Discriminated-
// Union, kein matchState, kein throwOnError (siehe ADR-S083-2 im adr.md für die Begründung,
// warum die volle Union weiterhin aufgeschoben bleibt).
export function useResultMutation<TData, TError, TVariables>(
  fn: (variables: TVariables) => ResultAsync<TData, TError>,
  onSuccess: () => void,
): readonly [(variables: TVariables) => void, TError | undefined, boolean] {
  const [error, setError] = useState<TError | undefined>(undefined)
  const mutation = useMutation<Result<TData, TError>, Error, TVariables>({
    // Promise.resolve flacht die ResultAsync (thenable) zu Promise<Result> ab –
    // React Query erwartet ein echtes Promise, nicht das ResultAsync selbst.
    mutationFn: (variables: TVariables) => Promise.resolve(fn(variables)),
    onSuccess: (result) => {
      result.match(
        () => {
          setError(undefined)
          onSuccess()
        },
        (e) => { setError(e) },
      )
    },
  })

  return [mutation.mutate, error, mutation.isPending]
}
