import { useState } from 'react';
import {
  Alert, Box, Button, Chip, CircularProgress, Dialog, DialogActions,
  DialogContent, DialogTitle, FormControl, InputLabel, MenuItem, Select, Typography,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import ShoppingCartIcon from '@mui/icons-material/ShoppingCart';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { getWeeklyPool, addToPool, removeFromPool } from '../api/weeklyPool';
import { getRecipes } from '../api/recipes';
import { generateShoppingList } from '../api/shoppingList';
import ConfirmDialog from '../components/ConfirmDialog';
import type { WeeklyPoolEntryDto } from '../types';
import { extractErrorMessage } from '../utils/errorUtils';

export default function WeeklyPoolPage() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedRecipeId, setSelectedRecipeId] = useState<number>(0);
  const [mutationError, setMutationError] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<WeeklyPoolEntryDto | null>(null);

  const { data: pool, isLoading, error } = useQuery({ queryKey: ['weekly-pool'], queryFn: getWeeklyPool });
  const { data: recipes } = useQuery({ queryKey: ['recipes'], queryFn: getRecipes });

  const addMutation = useMutation({
    mutationFn: addToPool,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['weekly-pool'] });
      setDialogOpen(false);
      setSelectedRecipeId(0);
      setMutationError(null);
    },
    onError: (err) => setMutationError(extractErrorMessage(err)),
  });

  const removeMutation = useMutation({
    mutationFn: removeFromPool,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['weekly-pool'] });
      setMutationError(null);
    },
    onError: (err) => setMutationError(extractErrorMessage(err)),
  });

  const generateMutation = useMutation({
    mutationFn: generateShoppingList,
    onSuccess: () => { setMutationError(null); navigate('/shopping-list'); },
    onError: (err) => setMutationError(extractErrorMessage(err)),
  });

  if (isLoading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>;
  if (error) return <Alert severity="error">Fehler beim Laden des Wochenplans.</Alert>;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5">Wochenplan</Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="outlined" startIcon={<AddIcon />} onClick={() => { setMutationError(null); setDialogOpen(true); }}>Rezept hinzufügen</Button>
          <Button variant="contained" startIcon={<ShoppingCartIcon />} onClick={() => generateMutation.mutate()} disabled={generateMutation.isPending}>
            {generateMutation.isPending ? 'Wird generiert...' : 'Einkaufsliste generieren'}
          </Button>
        </Box>
      </Box>

      {mutationError && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setMutationError(null)}>{mutationError}</Alert>}

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
        {pool?.length === 0 && <Typography color="text.secondary">Noch keine Rezepte im Wochenplan.</Typography>}
        {pool?.map(entry => (
          <Chip
            key={entry.id}
            label={`${entry.recipeTitle} (${new Date(entry.addedAt).toLocaleDateString('de-DE')})`}
            onDelete={() => setConfirmDelete(entry)}
            color="primary"
            variant="outlined"
          />
        ))}
      </Box>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Rezept zum Wochenplan hinzufügen</DialogTitle>
        <DialogContent sx={{ pt: 2 }}>
          {mutationError && <Alert severity="error" sx={{ mb: 2 }}>{mutationError}</Alert>}
          <FormControl fullWidth>
            <InputLabel>Rezept</InputLabel>
            <Select value={selectedRecipeId} label="Rezept" onChange={e => setSelectedRecipeId(Number(e.target.value))}>
              <MenuItem value={0}><em>Wählen...</em></MenuItem>
              {recipes?.map(r => <MenuItem key={r.id} value={r.id}>{r.title}</MenuItem>)}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Abbrechen</Button>
          <Button variant="contained" onClick={() => addMutation.mutate({ recipeId: selectedRecipeId })} disabled={selectedRecipeId === 0 || addMutation.isPending}>
            Hinzufügen
          </Button>
        </DialogActions>
      </Dialog>

      <ConfirmDialog
        open={confirmDelete !== null}
        title="Rezept aus Wochenplan entfernen"
        content={`"${confirmDelete?.recipeTitle}" aus dem Wochenplan entfernen?`}
        confirmLabel="Entfernen"
        onConfirm={() => { if (confirmDelete) removeMutation.mutate(confirmDelete.id); setConfirmDelete(null); }}
        onCancel={() => setConfirmDelete(null)}
      />
    </Box>
  );
}
