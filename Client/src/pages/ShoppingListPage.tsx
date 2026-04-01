import { useState } from 'react';
import {
  Alert, Box, Button, Checkbox, CircularProgress, Divider, List, ListItem,
  ListItemIcon, ListItemText, Typography,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getShoppingList, generateShoppingList, checkItem, uncheckItem } from '../api/shoppingList';
import { extractErrorMessage } from '../utils/errorUtils';

export default function ShoppingListPage() {
  const queryClient = useQueryClient();
  const [mutationError, setMutationError] = useState<string | null>(null);

  const { data, isLoading, error } = useQuery({ queryKey: ['shopping-list'], queryFn: getShoppingList });

  const checkMutation = useMutation({
    mutationFn: checkItem,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['shopping-list'] }); setMutationError(null); },
    onError: (err) => setMutationError(extractErrorMessage(err)),
  });

  const uncheckMutation = useMutation({
    mutationFn: uncheckItem,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['shopping-list'] }); setMutationError(null); },
    onError: (err) => setMutationError(extractErrorMessage(err)),
  });

  const generateMutation = useMutation({
    mutationFn: generateShoppingList,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['shopping-list'] }); setMutationError(null); },
    onError: (err) => setMutationError(extractErrorMessage(err)),
  });

  if (isLoading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>;
  if (error) return <Alert severity="error">Fehler beim Laden der Einkaufsliste.</Alert>;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5">Einkaufsliste</Typography>
        <Button variant="outlined" startIcon={<RefreshIcon />} onClick={() => generateMutation.mutate()} disabled={generateMutation.isPending}>
          {generateMutation.isPending ? 'Wird generiert...' : 'Neu generieren'}
        </Button>
      </Box>

      {mutationError && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setMutationError(null)}>{mutationError}</Alert>}

      <Typography variant="h6" gutterBottom>Noch kaufen</Typography>
      {data?.openItems.length === 0 && <Typography color="text.secondary">Keine offenen Artikel.</Typography>}
      <List>
        {data?.openItems.map(item => (
          <ListItem key={item.id} disablePadding>
            <ListItemIcon>
              <Checkbox
                edge="start"
                checked={false}
                onChange={() => checkMutation.mutate(item.id)}
                disabled={checkMutation.isPending}
              />
            </ListItemIcon>
            <ListItemText primary={item.ingredientName} secondary={`${item.quantity} ${item.unit}`} />
          </ListItem>
        ))}
      </List>

      {(data?.boughtItems.length ?? 0) > 0 && (
        <>
          <Divider sx={{ my: 2 }} />
          <Typography variant="h6" gutterBottom>Erledigt</Typography>
          <List>
            {data?.boughtItems.map(item => (
              <ListItem key={item.id} disablePadding>
                <ListItemIcon>
                  <Checkbox
                    edge="start"
                    checked={true}
                    onChange={() => uncheckMutation.mutate(item.id)}
                    disabled={uncheckMutation.isPending}
                  />
                </ListItemIcon>
                <ListItemText
                  primary={item.ingredientName}
                  secondary={`${item.quantity} ${item.unit}`}
                  sx={{ '& .MuiListItemText-primary': { textDecoration: 'line-through', color: 'text.secondary' } }}
                />
              </ListItem>
            ))}
          </List>
        </>
      )}
    </Box>
  );
}
