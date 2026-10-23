import { useState } from 'react'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Container from '@mui/material/Container'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'
import { useNavigate } from 'react-router'
import { useResultMutation } from '../hooks/useResultMutation'
import { createRecipe } from '../services/recipesApi'
import { asIngredientsText, asRecipeTitle, asStepInstruction } from '../domain/recipe'
import type { Recipe } from '../domain/recipe'

// ADR-S135-4: "Rezept anlegen" ist eine eigene Seite, kein Dialog.
export default function CreateRecipePage() {
  const navigate = useNavigate()
  const [title, setTitle] = useState('')
  const [ingredients, setIngredients] = useState('')
  const [steps, setSteps] = useState<readonly string[]>([''])
  // Nach dem Speichern zeigt die Detailansicht das Rezept aus der 201-Antwort (Router-State).
  const [save] = useResultMutation(createRecipe, (created: Recipe) => {
    void navigate(`/recipes/${created.id}`, { state: created })
  })

  const changeStep = (index: number, instruction: string) => {
    setSteps(steps.map((step, i) => (i === index ? instruction : step)))
  }

  return (
    <Container component="main" maxWidth="sm">
      <Box
        component="form"
        onSubmit={(e: Readonly<React.SyntheticEvent>) => {
          e.preventDefault()
          save({
            title: asRecipeTitle(title),
            ingredients: asIngredientsText(ingredients),
            steps: steps.map((instruction) => ({ instruction: asStepInstruction(instruction) })),
          })
        }}
      >
        <Typography variant="h5" component="h1" gutterBottom>Rezept anlegen</Typography>
        <TextField
          label="Titel"
          fullWidth
          margin="normal"
          value={title}
          onChange={(e) => { setTitle(e.target.value) }}
        />
        <TextField
          label="Zutaten"
          fullWidth
          multiline
          minRows={3}
          margin="normal"
          value={ingredients}
          onChange={(e) => { setIngredients(e.target.value) }}
        />
        <Stack spacing={2}>
          <Box>
            <StepFields steps={steps} onChange={changeStep} />
            <Button onClick={() => { setSteps([...steps, '']) }}>Schritt hinzufügen</Button>
          </Box>
          <Button type="submit" variant="contained">Speichern</Button>
        </Stack>
      </Box>
    </Container>
  )
}

type StepFieldsProps = {
  readonly steps: readonly string[]
  readonly onChange: (index: number, instruction: string) => void
}

function StepFields({ steps, onChange }: Readonly<StepFieldsProps>) {
  return steps.map((instruction, index) => (
    <TextField
      // Schritte haben keine Identität außer ihrer Position; es wird nur angehängt.
      key={index}
      label={`Schritt ${String(index + 1)}`}
      fullWidth
      multiline
      minRows={2}
      margin="normal"
      value={instruction}
      onChange={(e) => { onChange(index, e.target.value) }}
    />
  ))
}
