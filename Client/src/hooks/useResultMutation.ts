import { useMutation } from '@tanstack/react-query'
import type { ResultAsync } from 'neverthrow'

// US-904 Zutat anlegen: Mutation-State Minimal/YAGNI – nur der Erfolgs-Seiteneffekt
// (onSuccess) wird ausgeübt. Volle MutationState-Union (pending/error) aufgeschoben
// (ADR-S083-2) – Erweiterung bei Button-Disable-/Error-Szenarien.
export function useResultMutation<TData, TError, TVariables>(
  fn: (variables: TVariables) => ResultAsync<TData, TError>,
  onSuccess: () => void,
): (variables: TVariables) => void {
  const mutation = useMutation({
    mutationFn: (variables: TVariables) => Promise.resolve(fn(variables)),
    onSuccess,
  })

  return mutation.mutate
}
