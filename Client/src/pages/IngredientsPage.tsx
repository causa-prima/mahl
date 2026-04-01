import { useState } from 'react';
import {
  Alert, Box, Button, CircularProgress, Dialog, DialogActions, DialogContent, DialogTitle,
  IconButton, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  TextField, Typography,
} from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getIngredients, createIngredient, deleteIngredient } from '../api/ingredients';
import ConfirmDialog from '../components/ConfirmDialog';
import type { IngredientDto } from '../types';
import { extractErrorMessage } from '../utils/errorUtils';

export default function IngredientsPage() {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [name, setName] = useState('');
  const [defaultUnit, setDefaultUnit] = useState('');
  const [mutationError, setMutationError] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<IngredientDto | null>(null);

  const { data: ingredients, isLoading, error } = useQuery({
    queryKey: ['ingredients'],
    queryFn: getIngredients,
  });

  const createMutation = useMutation({
    mutationFn: createIngredient,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ingredients'] });
      setDialogOpen(false);
      setName('');
      setDefaultUnit('');
      setMutationError(null);
    },
    onError: (err) => setMutationError(extractErrorMessage(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteIngredient,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ingredients'] });
      setMutationError(null);
    },
    onError: (err) => setMutationError(extractErrorMessage(err)),
  });

  const handleCreate = () => {
    if (name.trim() && defaultUnit.trim()) {
      createMutation.mutate({ name: name.trim(), defaultUnit: defaultUnit.trim() });
    }
  };

  if (isLoading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>;
  if (error) return <Alert severity="error">Fehler beim Laden der Zutaten.</Alert>;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5">Zutaten</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => { setMutationError(null); setDialogOpen(true); }}>
          Neue Zutat
        </Button>
      </Box>

      {mutationError && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setMutationError(null)}>{mutationError}</Alert>}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Einheit</TableCell>
              <TableCell>Immer vorrätig</TableCell>
              <TableCell align="right">Aktionen</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {ingredients?.map(ing => (
              <TableRow key={ing.id}>
                <TableCell>{ing.name}</TableCell>
                <TableCell>{ing.defaultUnit}</TableCell>
                <TableCell>{ing.alwaysInStock ? 'Ja' : 'Nein'}</TableCell>
                <TableCell align="right">
                  <IconButton color="error" size="small" onClick={() => setConfirmDelete(ing)}>
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={dialogOpen} onClose={() => { setDialogOpen(false); setName(''); setDefaultUnit(''); setMutationError(null); }} maxWidth="sm" fullWidth>
        <DialogTitle>Neue Zutat</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
          {mutationError && <Alert severity="error">{mutationError}</Alert>}
          <TextField label="Name" value={name} onChange={e => setName(e.target.value)} fullWidth required />
          <TextField label="Einheit" value={defaultUnit} onChange={e => setDefaultUnit(e.target.value)} fullWidth required placeholder="z.B. g, ml, Stk" />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setDialogOpen(false); setName(''); setDefaultUnit(''); setMutationError(null); }} autoFocus>Abbrechen</Button>
          <Button variant="contained" onClick={handleCreate} disabled={!name.trim() || !defaultUnit.trim() || createMutation.isPending}>
            {createMutation.isPending ? 'Wird erstellt...' : 'Erstellen'}
          </Button>
        </DialogActions>
      </Dialog>

      <ConfirmDialog
        open={confirmDelete !== null}
        title="Zutat löschen"
        content={`"${confirmDelete?.name}" wirklich löschen?`}
        onConfirm={() => { if (confirmDelete) { deleteMutation.mutate(confirmDelete.id); } setConfirmDelete(null); }}
        onCancel={() => setConfirmDelete(null)}
      />
    </Box>
  );
}
