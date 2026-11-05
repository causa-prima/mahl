import { useId, useRef, useState } from 'react'
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
import type { FieldMessage, InputRefCallback } from '../hooks/useRecipeFieldMessages'
import { useRecipeForm } from '../hooks/useRecipeForm'
import { sentStepFieldIndexes, toNewRecipe } from '../domain/recipe'
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
  // Stand beim Speichern: welches Formularfeld welchen gesendeten Schritt trug (ADR-S144-1).
  const [sentFieldIndexes, setSentFieldIndexes] = useState<readonly number[]>([])
  const field = useRecipeFieldMessages(error, sentFieldIndexes)

  const leaveToList = () => { void navigate('/recipes') }
  const discardQuestion = useDiscardQuestion(hasInput, leaveToList)

  return (
    <Container component="main" maxWidth="sm">
      <Box
        component="form"
        onSubmit={(e: Readonly<React.SyntheticEvent>) => {
          e.preventDefault()
          setSentFieldIndexes(sentStepFieldIndexes(values.steps))
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
            stepsMessage={field.steps.message}
            instructionMessage={field.steps.instructionMessage}
            inputRef={field.steps.inputRef}
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
      <FieldMessageText id={messageId} message={message} />
    </FormControl>
  )
}

type StepsSectionProps = {
  readonly steps: readonly string[]
  readonly onChange: (index: number, instruction: string) => void
  readonly onAdd: () => void
  readonly stepsMessage: string | undefined
  readonly instructionMessage: (fieldIndex: number) => string | undefined
  readonly inputRef: (fieldIndex: number) => InputRefCallback
}

function StepsSection(props: Readonly<StepsSectionProps>) {
  const { steps, onChange, onAdd, stepsMessage: message, instructionMessage, inputRef } = props
  const messageId = useId()
  // Stryker disable next-line ConditionalExpression: Verknüpfung nur bei vorhandener Meldung (ADR-S144-3)
  const describedBy = message === undefined ? undefined : messageId
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
      <FieldMessageText id={messageId} message={message} />
      {steps.map((instruction, index) => (
        <StepField
          // Schritte haben keine Identität außer ihrer Position; es wird nur angehängt.
          key={index}
          label={`Schritt ${String(index + 1)}`}
          value={instruction}
          // Nur nachträglich hinzugefügte Schrittfelder (Index > 0) übernehmen beim Einhängen den Fokus
          // (ADR-S135-4); das erste würde sonst mit dem Titel konkurrieren.
          autoFocus={index > 0}
          inputRef={inputRef(index)}
          message={instructionMessage(index)}
          // Nur das erste Feld ist Fokusziel der Listen-Meldung (ADR-S135-4); `describedBy` ist nur bei
          // vorhandener Meldung gesetzt.
          listMessageId={index === 0 ? describedBy : undefined}
          onChange={(text) => { onChange(index, text) }}
        />
      ))}
      <Box>
        <Button onClick={onAdd}>Schritt hinzufügen</Button>
      </Box>
    </FormControl>
  )
}

// ADR-S144-3: Meldungselement nur bei vorhandener Meldung.
function FieldMessageText({ id, message }: Readonly<{ id: string, message: string | undefined }>) {
  // Stryker disable next-line ConditionalExpression: Meldungselement nur bei vorhandener Meldung (ADR-S144-3)
  return message !== undefined && <FormHelperText id={id}>{message}</FormHelperText>
}

type StepFieldProps = {
  readonly label: string
  readonly value: string
  readonly autoFocus: boolean
  readonly inputRef: InputRefCallback
  // Meldung zur Anweisung dieses Schritts (Hilfetext unter dem Feld)
  readonly message: string | undefined
  // Id der Listen-Meldung an der Legende, nur gesetzt am Fokusziel dieser Meldung: Das Feld trägt sie selbst
  // (aria-invalid, aria-describedby), ohne roten Rahmen (UI-Entwurf).
  readonly listMessageId: string | undefined
  readonly onChange: (instruction: string) => void
}

function StepField(props: Readonly<StepFieldProps>) {
  const { label, value, autoFocus, inputRef, message, listMessageId, onChange } = props
  return (
    <TextField
      label={label}
      autoFocus={autoFocus}
      fullWidth
      multiline
      minRows={2}
      margin="normal"
      value={value}
      inputRef={inputRef}
      // error trägt aria-invalid und die Verknüpfung des Hilfetextes an das Eingabefeld (Semantik, getestet).
      // Annahme: Das Feld mit Listen-Meldung hat keine Anweisungs-Meldung (bei der Listen-Meldung wurde
      // kein Schritt gesendet) – die beiden aria-Quellen kollidieren nie.
      error={message !== undefined}
      helperText={message}
      slotProps={{
        htmlInput: listMessageId === undefined ? {} : { 'aria-invalid': true, 'aria-describedby': listMessageId },
      }}
      onChange={(e) => { onChange(e.target.value) }}
    />
  )
}
