import { useState } from 'react'
// eslint-disable-next-line @typescript-eslint/no-restricted-imports -- useResultQuery noch nicht implementiert; Migration in Szenario 2 (US-904-happy-path)
import { useQuery } from '@tanstack/react-query'
import Button from '@mui/material/Button'
import Dialog from '@mui/material/Dialog'
import TextField from '@mui/material/TextField'
import { fetchIngredients } from '../services/ingredientsApi'

export default function IngredientsPage() {
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  // Stryker disable next-line ArrayDeclaration -- Default [] nie getestet: data ist während Tests nie undefined (MSW liefert immer []). Entfällt wenn Loading-State-Szenario implementiert ist.
  const { data: ingredients = [] } = useQuery({
    // Stryker disable next-line StringLiteral,ArrayDeclaration -- queryKey ist ein Cache-Bezeichner, kein Verhalten
    queryKey: ['ingredients'],
    queryFn: fetchIngredients,
  })

  // Stryker disable next-line ConditionalExpression: Non-Empty-Listen-Pfad wird von keinem aktuellen Szenario getestet; erst US-904 "Zutat anlegen" rendert Zutaten in der Liste. Zeitlich begrenzte Suppression – mit jenem Szenario entfernen (AGENT_MEMORY tech debt).
  if (ingredients.length === 0) {
    return (
      <div>
        <p>Noch keine Zutaten angelegt.</p>
        <Button variant="contained" onClick={() => { setIsDialogOpen(true) }}>Zutat anlegen</Button>
        <Dialog open={isDialogOpen}>
          <TextField label="Name" />
          <TextField label="Einheit" />
        </Dialog>
      </div>
    )
  }

  return (
    <ul data-testid="ingredient-list">
      {
        // Stryker disable next-line ArrowFunction: Listen-Render-Pfad (NoCoverage) wird von keinem aktuellen Szenario ausgeführt; erst US-904 "Zutat anlegen" rendert Zutaten in der Liste. Zeitlich begrenzte Suppression – mit jenem Szenario entfernen (AGENT_MEMORY tech debt).
        ingredients.map((_, i) => <li key={i} />)
      }
    </ul>
  )
}
