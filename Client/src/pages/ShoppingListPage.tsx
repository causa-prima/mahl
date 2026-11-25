import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Container from '@mui/material/Container'
import List from '@mui/material/List'
import ListItem from '@mui/material/ListItem'
import Stack from '@mui/material/Stack'
import Typography from '@mui/material/Typography'
import { Link as RouterLink } from 'react-router'
import { formatQuantity } from '../domain/recipe'
import { useShoppingList } from '../hooks/useShoppingList'
import type { ShoppingListItem } from '../services/shoppingListApi'

// ADR-S067-1: Kachel mit zwei Zeilen, Name und darunter die Menge mit Einheit; ohne Menge nur der Name.
// Beide Zeilen sind eigene Block-Elemente (Typography rendert ein <p>).
// Lange Namen brechen um (overflowWrap, Silbentrennung über <html lang="de">), statt die Spalte zu weiten.
function ShoppingListTile({ item }: Readonly<{ item: ShoppingListItem }>) {
  return (
    // Stryker disable next-line ObjectLiteral,StringLiteral: Layout-Werte der Kachel, in jsdom nicht beobachtbar (ADR-S136-2)
    <ListItem disablePadding sx={{ display: 'block', border: 1, borderColor: 'divider', borderRadius: 1, p: 1, overflowWrap: 'anywhere', hyphens: 'auto' }}>
      <Typography>{item.name}</Typography>
      {item.quantity !== null && <Typography variant="body2" color="text.secondary">{formatQuantity(item.quantity, item.unit)}</Typography>}
    </ListItem>
  )
}

// Solange die Antwort fehlt (Laden oder Fehler), steht unter der Überschrift nichts: kein Leerzustand, kein Spinner.
function ShoppingListContent({ items }: Readonly<{ items: readonly ShoppingListItem[] | undefined }>) {
  if (items === undefined) return null
  if (items.length === 0) {
    return (
      <Stack spacing={2}>
        <Typography>Die Einkaufsliste ist leer.</Typography>
        <Box>
          <Button component={RouterLink} to="/planned" variant="contained">Zu den vorgemerkten Rezepten</Button>
        </Box>
      </Stack>
    )
  }
  return (
    // minmax(0, 1fr): Die Spalten dürfen schmaler als ihr Inhalt werden, sonst sprengt ein langer Name das Raster.
    // Stryker disable next-line ObjectLiteral,StringLiteral: Layout-Werte (3 Kacheln je Zeile, Abstand), in jsdom nicht beobachtbar (ADR-S136-2)
    <List aria-labelledby="shopping-list-heading" disablePadding sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: 1 }}>
      {items.map((item) => <ShoppingListTile key={item.name} item={item} />)}
    </List>
  )
}

export default function ShoppingListPage() {
  const items = useShoppingList()

  return (
    <Container component="main" maxWidth="sm">
      <Typography variant="h5" component="h1" id="shopping-list-heading" gutterBottom>Einkaufsliste</Typography>
      <ShoppingListContent items={items} />
    </Container>
  )
}
