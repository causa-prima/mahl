import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Container from '@mui/material/Container'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import { Link as RouterLink } from 'react-router'
import { useShoppingList } from '../hooks/useShoppingList'

// Solange die Antwort fehlt (Laden oder Fehler), steht unter der Überschrift nichts: kein Leerzustand, kein Spinner.
// Eine nicht leere Liste zeigt ebenfalls nichts: Einträge anzeigen kommt mit dem Übernehmen.
function ShoppingListContent({ entries }: Readonly<{ entries: readonly unknown[] | undefined }>) {
  if (entries?.length !== 0) return null
  return (
    <Stack spacing={2}>
      <Typography>Die Einkaufsliste ist leer.</Typography>
      <Box>
        <Button component={RouterLink} to="/planned" variant="contained">Zu den vorgemerkten Rezepten</Button>
      </Box>
    </Stack>
  )
}

export default function ShoppingListPage() {
  const entries = useShoppingList()

  return (
    <Container component="main" maxWidth="sm">
      <Typography variant="h5" component="h1" gutterBottom>Einkaufsliste</Typography>
      <ShoppingListContent entries={entries} />
    </Container>
  )
}
