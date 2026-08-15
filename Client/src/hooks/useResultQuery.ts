import { useQuery } from '@tanstack/react-query'
import type { ResultAsync } from 'neverthrow'

// US-904 Zutat anlegen: Query-State Minimal/YAGNI – nur der success-Zweig wird ausgeübt
// (befüllte Liste). Pending kollabiert zu undefined und wird vom Empty-State-Pfad
// abgedeckt. Volle MutationState-Union (pending/error) aufgeschoben – Erweiterung bei
// eigenen Lade-/Fehler-Szenarien. Kanonische Form: ADR-S056-1 und
// coding-guideline-typescript.md §4b; Stand der Abweichung: TD-S101-1.
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
