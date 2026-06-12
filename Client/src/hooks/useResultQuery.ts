import { useQuery } from '@tanstack/react-query'
import type { ResultAsync } from 'neverthrow'

// US-904 Zutat anlegen: Query-State Minimal/YAGNI – nur der success-Zweig wird ausgeübt
// (befüllte Liste). Pending kollabiert zu undefined und wird vom Empty-State-Pfad
// abgedeckt. Volle MutationState-Union (pending/error) aufgeschoben (ADR-S083-2) –
// Erweiterung bei eigenen Lade-/Fehler-Szenarien.
export function useResultQuery<TData, TError>(
  key: readonly unknown[],
  fn: () => ResultAsync<TData, TError>,
): TData | undefined {
  const query = useQuery({
    queryKey: key,
    queryFn: () => Promise.resolve(fn()),
  })

  return query.data?.unwrapOr(undefined as TData)
}
