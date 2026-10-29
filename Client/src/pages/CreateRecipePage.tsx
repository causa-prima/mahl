import { useId, useRef } from 'react'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Container from '@mui/material/Container'
import Dialog from '@mui/material/Dialog'
import DialogActions from '@mui/material/DialogActions'
import DialogTitle from '@mui/material/DialogTitle'
import FormControl from '@mui/material/FormControl'
import FormHelperText from '@mui/material/FormHelperText'
import FormLabel from '@mui/material/FormLabel'
import InputLabel from '@mui/material/InputLabel'
import OutlinedInput from '@mui/material/OutlinedInput'
import Stack from '@mui/material/Stack'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'
import { useNavigate } from 'react-router'
import { useResultMutation } from '../hooks/useResultMutation'
import { createRecipe } from '../services/recipesApi'
import { useDiscardQuestion } from '../hooks/useDiscardQuestion'
import { useRecipeFieldMessages } from '../hooks/useRecipeFieldMessages'
import type { FieldMessage } from '../hooks/useRecipeFieldMessages'
import { useRecipeForm } from '../hooks/useRecipeForm'
import { toNewRecipe } from '../domain/recipe'
import type { Recipe } from '../domain/recipe'

const ingredientsHint = 'Eine Zutat je Zeile: Menge, Einheit, Zutat – z. B. „250 g Mehl“ oder „Salz“.'

// ADR-S135-4: "Rezept anlegen" ist eine eigene Seite, kein Dialog.
export default function CreateRecipePage() {
  const navigate = useNavigate()
  const { values, hasInput, setTitle, setIngredients, changeStep, addStep } = useRecipeForm()
  // Die Detailansicht lädt das Rezept selbst über die Adresse (ADR-S142-2).
  const [save, error] = useResultMutation(createRecipe, (created: Recipe) => {
    void navigate(`/recipes/${created.id}`)
  })
  const field = useRecipeFieldMessages(error)

  const leaveToList = () => { void navigate('/recipes') }
  const discardQuestion = useDiscardQuestion(hasInput, leaveToList)

  return (
    <Container component="main" maxWidth="sm">
      <Box
        component="form"
        onSubmit={(e: Readonly<React.SyntheticEvent>) => {
          e.preventDefault()
          save(toNewRecipe(values))
        }}
      >
        <Typography variant="h5" component="h1" gutterBottom>Rezept anlegen</Typography>
        <TitleAndIngredientsFields
          title={values.title}
          ingredients={values.ingredients}
          onTitleChange={setTitle}
          onIngredientsChange={setIngredients}
          titleField={field.title}
          ingredientsField={field.ingredients}
        />
        <Stack spacing={2}>
          <StepsSection
            steps={values.steps}
            stepsField={field.steps}
            onChange={changeStep}
            onAdd={addStep}
          />
          <FormActions onCancel={discardQuestion.cancel} />
        </Stack>
      </Box>
      <DiscardDialog
        open={discardQuestion.open}
        onKeepEditing={discardQuestion.keepEditing}
        onDiscard={leaveToList}
      />
    </Container>
  )
}

function FormActions({ onCancel }: Readonly<{ onCancel: () => void }>) {
  return (
    <Stack
      direction="row"
      spacing={1}
      // Stryker disable next-line ObjectLiteral,StringLiteral: Layout-Wert, in jsdom nicht beobachtbar (Einzelfall, vom User freigegeben S143)
      sx={{ justifyContent: 'flex-end' }}
    >
      <Button type="button" onClick={onCancel}>Abbrechen</Button>
      {/* formNoValidate: Validierung ist server-only (ADR-S090-1) – sonst blockiert der native
          `required`-Check das Absenden leerer Pflichtfelder, bevor der Server sie melden kann. */}
      <Button type="submit" formNoValidate variant="contained">Speichern</Button>
    </Stack>
  )
}

type DiscardDialogProps = {
  readonly open: boolean
  readonly onKeepEditing: () => void
  readonly onDiscard: () => void
}

// ADR-S135-4: Escape und Klick neben die Nachfrage (onClose) wirken wie "Weiter bearbeiten".
function DiscardDialog({ open, onKeepEditing, onDiscard }: Readonly<DiscardDialogProps>) {
  const keepEditingRef = useRef<HTMLButtonElement>(null)
  const titleId = useId()
  return (
    <Dialog
      open={open}
      onClose={onKeepEditing}
      role="alertdialog"
      aria-labelledby={titleId}
      // ADR-S100-1: autoFocus wird während der Öffnen-Transition ignoriert; Fokus nach deren Ende setzen.
      slotProps={{ transition: { onEntered: () => { keepEditingRef.current?.focus() } } }}
    >
      <DialogTitle id={titleId}>Eingaben verwerfen?</DialogTitle>
      <DialogActions>
        <Button ref={keepEditingRef} onClick={onKeepEditing}>Weiter bearbeiten</Button>
        <Button color="error" onClick={onDiscard}>Verwerfen</Button>
      </DialogActions>
    </Dialog>
  )
}

type TitleAndIngredientsFieldsProps = {
  readonly title: string
  readonly ingredients: string
  readonly onTitleChange: (title: string) => void
  readonly onIngredientsChange: (ingredients: string) => void
  readonly titleField: FieldMessage<HTMLInputElement>
  readonly ingredientsField: FieldMessage<HTMLTextAreaElement>
}

function TitleAndIngredientsFields(props: Readonly<TitleAndIngredientsFieldsProps>) {
  const { title, ingredients, onTitleChange, onIngredientsChange, titleField, ingredientsField } = props
  return (
    <>
      <TextField
        label="Titel"
        required
        // ADR-S135-4: Beim Öffnen liegt der Fokus auf dem Titel.
        autoFocus
        fullWidth
        margin="normal"
        value={title}
        error={titleField.message !== undefined}
        helperText={titleField.message}
        inputRef={titleField.ref}
        onChange={(e) => { onTitleChange(e.target.value) }}
      />
      <IngredientsField value={ingredients} field={ingredientsField} onChange={onIngredientsChange} />
    </>
  )
}

type IngredientsFieldProps = {
  readonly value: string
  readonly field: FieldMessage<HTMLTextAreaElement>
  readonly onChange: (ingredients: string) => void
}

// Eigene Komposition statt TextField: Hinweis und Meldung sind beide FormHelperText im FormControl
// (Abstand und Einzug der outlined-Variante). Der Hinweis ersetzt den Placeholder, bleibt beim Tippen
// stehen (ADR-S135-4) und bleibt auch im Fehlerzustand grau (error={false}); die Meldung steht darunter.
function IngredientsField({ value, field, onChange }: Readonly<IngredientsFieldProps>) {
  const inputId = useId()
  const hintId = useId()
  const messageId = useId()
  const { message } = field
  // Stryker disable next-line ConditionalExpression: Meldungselement nur bei vorhandener Meldung (ADR-S144-3)
  const messageElement = message !== undefined && <FormHelperText id={messageId}>{message}</FormHelperText>
  // error={false}: Der Hinweis bleibt grau, auch wenn das Feld im Fehlerzustand ist.
  // Stryker disable next-line BooleanLiteral: reine Farbe des Hinweises ohne Semantik (ADR-S144-3)
  const hintElement = <FormHelperText id={hintId} error={false}>{ingredientsHint}</FormHelperText>
  return (
    // error trägt aria-invalid an das Eingabefeld weiter – Semantik, getestet (ADR-S144-3).
    <FormControl fullWidth required margin="normal" error={message !== undefined}>
      <InputLabel htmlFor={inputId}>Zutaten</InputLabel>
      <OutlinedInput
        id={inputId}
        label="Zutaten"
        multiline
        minRows={3}
        value={value}
        inputRef={field.ref}
        slotProps={{
          input: {
            // Stryker disable next-line ConditionalExpression: Verknüpfung nur bei vorhandener Meldung (ADR-S144-3)
            'aria-describedby': message === undefined ? hintId : `${hintId} ${messageId}`,
          },
        }}
        onChange={(e) => { onChange(e.target.value) }}
      />
      {hintElement}
      {messageElement}
    </FormControl>
  )
}

type StepsSectionProps = {
  readonly steps: readonly string[]
  readonly onChange: (index: number, instruction: string) => void
  readonly onAdd: () => void
  readonly stepsField: FieldMessage<HTMLTextAreaElement>
}

function StepsSection({ steps, onChange, onAdd, stepsField }: Readonly<StepsSectionProps>) {
  const messageId = useId()
  const { message } = stepsField
  // Stryker disable next-line ConditionalExpression: Verknüpfung nur bei vorhandener Meldung (ADR-S144-3)
  const describedBy = message === undefined ? undefined : messageId
  // Stryker disable next-line ConditionalExpression: Meldungselement nur bei vorhandener Meldung (ADR-S144-3)
  const messageElement = message !== undefined && <FormHelperText id={messageId}>{message}</FormHelperText>
  return (
    // aria-label: Der Asterisk der Legende ist aria-hidden und eine Gruppe kennt kein aria-required;
    // der zugängliche Name trägt deshalb die Pflichtangabe (enthält den sichtbaren Namen, WCAG 2.5.3).
    <FormControl
      component="fieldset"
      aria-label="Schritte (Pflichtangabe)"
      aria-describedby={describedBy}
      // Stryker disable next-line ConditionalExpression,EqualityOperator: reine Farbe der Legende, eine Gruppe kennt kein aria-invalid (ADR-S144-3)
      error={message !== undefined}
    >
      <FormLabel component="legend" required>Schritte</FormLabel>
      {messageElement}
      {steps.map((instruction, index) => (
        <TextField
          // Schritte haben keine Identität außer ihrer Position; es wird nur angehängt.
          key={index}
          label={`Schritt ${String(index + 1)}`}
          // Nur nachträglich hinzugefügte Schrittfelder (Index > 0) übernehmen beim Einhängen den Fokus
          // (ADR-S135-4); das erste würde sonst mit dem Titel konkurrieren.
          autoFocus={index > 0}
          fullWidth
          multiline
          minRows={2}
          margin="normal"
          value={instruction}
          inputRef={index === 0 ? stepsField.ref : undefined}
          // Der Fokus springt auf das erste Schrittfeld: es trägt die Meldung selbst, ohne roten Rahmen (UI-Entwurf).
          slotProps={{
            htmlInput: {
              'aria-invalid': index === 0 && message !== undefined,
              // Nur das erste Schrittfeld trägt die Meldung (Fokusziel, ADR-S135-4).
              'aria-describedby': index === 0 ? describedBy : undefined,
            },
          }}
          onChange={(e) => { onChange(index, e.target.value) }}
        />
      ))}
      <Box>
        <Button onClick={onAdd}>Schritt hinzufügen</Button>
      </Box>
    </FormControl>
  )
}
