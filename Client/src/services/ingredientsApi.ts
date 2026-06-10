export function fetchIngredients(): Promise<unknown[]> {
  // Stryker disable next-line StringLiteral: URL wird von keinem aktuellen Szenario gepinnt – bei "" greift MSW nicht → Fehler → data=[] → Empty-State-Test bleibt grün. Erst ein Szenario, das eine befüllte Liste rendert (US-904 "Zutat anlegen" / "Mehrere Zutaten"), killt diesen Mutanten. Zeitlich begrenzte Suppression – dann entfernen (AGENT_MEMORY tech debt).
  return fetch('/api/ingredients').then(r => r.json())
}
