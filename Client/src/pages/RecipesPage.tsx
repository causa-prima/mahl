import { useState } from 'react';
import {
  Alert, Box, Button, Card, CardActions, CardContent, CircularProgress, Collapse,
  Dialog, DialogActions, DialogContent, DialogTitle, Divider, IconButton,
  List, ListItem, ListItemText, MenuItem, Select, TextField, Typography,
  FormControl, InputLabel,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getRecipes, getRecipe, createRecipe, deleteRecipe } from '../api/recipes';
import { getIngredients } from '../api/ingredients';
import ConfirmDialog from '../components/ConfirmDialog';
import type { RecipeSummaryDto } from '../types';
import { extractErrorMessage } from '../utils/errorUtils';

interface IngredientFormRow {
  uuid: string;
  ingredientId: number;
  quantity: number;
  unit: string;
}

interface StepFormRow {
  uuid: string;
  instruction: string;
}

function RecipeDetailCard({ recipe }: { recipe: RecipeSummaryDto }) {
  const [expanded, setExpanded] = useState(false);

  const { data: detail, isFetching, refetch } = useQuery({
    queryKey: ['recipe', recipe.id],
    queryFn: () => getRecipe(recipe.id),
    enabled: false,
    refetchOnMount: false,
  });

  const handleToggle = () => {
    if (!expanded && !detail) refetch();
    setExpanded(prev => !prev);
  };

  return (
    <>
      <CardContent sx={{ cursor: 'pointer' }} onClick={handleToggle}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <Box>
            <Typography variant="h6">{recipe.title}</Typography>
            {recipe.sourceUrl && (
              <Typography variant="body2" color="text.secondary" onClick={e => e.stopPropagation()}>
                <a href={recipe.sourceUrl} target="_blank" rel="noreferrer">{recipe.sourceUrl}</a>
              </Typography>
            )}
          </Box>
          <IconButton size="small" onClick={e => { e.stopPropagation(); handleToggle(); }}>
            {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>
      </CardContent>
      <Collapse in={expanded}>
        <Divider />
        <CardContent>
          {isFetching && <CircularProgress size={20} />}
          {detail && (
            <>
              <Typography variant="subtitle2" gutterBottom>Zutaten</Typography>
              <List dense disablePadding>
                {detail.ingredients.map(ing => (
                  <ListItem key={ing.id} disablePadding>
                    <ListItemText primary={`${ing.ingredientName}: ${ing.quantity} ${ing.unit}`} />
                  </ListItem>
                ))}
              </List>
              <Typography variant="subtitle2" sx={{ mt: 1 }} gutterBottom>Schritte</Typography>
              <List dense disablePadding>
                {detail.steps.map(step => (
                  <ListItem key={step.id} disablePadding>
                    <ListItemText primary={`${step.stepNumber}. ${step.instruction}`} />
                  </ListItem>
                ))}
              </List>
            </>
          )}
        </CardContent>
      </Collapse>
    </>
  );
}

export default function RecipesPage() {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [title, setTitle] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [ingredients, setIngredients] = useState<IngredientFormRow[]>([{ uuid: crypto.randomUUID(), ingredientId: 0, quantity: 1, unit: '' }]);
  const [steps, setSteps] = useState<StepFormRow[]>([{ uuid: crypto.randomUUID(), instruction: '' }]);
  const [mutationError, setMutationError] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<RecipeSummaryDto | null>(null);

  const { data: recipes, isLoading, error } = useQuery({ queryKey: ['recipes'], queryFn: getRecipes });
  const { data: allIngredients } = useQuery({ queryKey: ['ingredients'], queryFn: getIngredients });

  const createMutation = useMutation({
    mutationFn: createRecipe,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recipes'] });
      setDialogOpen(false);
      resetForm();
      setMutationError(null);
    },
    onError: (err) => setMutationError(extractErrorMessage(err)),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteRecipe,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recipes'] });
      setMutationError(null);
    },
    onError: (err) => setMutationError(extractErrorMessage(err)),
  });

  const resetForm = () => {
    setTitle(''); setSourceUrl('');
    setIngredients([{ uuid: crypto.randomUUID(), ingredientId: 0, quantity: 1, unit: '' }]);
    setSteps([{ uuid: crypto.randomUUID(), instruction: '' }]);
    setMutationError(null);
  };

  const handleCreate = () => {
    const validIngredients = ingredients.filter(i => i.ingredientId > 0);
    const validSteps = steps.filter(s => s.instruction.trim());
    createMutation.mutate({
      title: title.trim(),
      sourceUrl: sourceUrl.trim() || undefined,
      ingredients: validIngredients.map(({ ingredientId, quantity, unit }) => ({ ingredientId, quantity, unit })),
      steps: validSteps.map(({ instruction }) => ({ instruction: instruction.trim() })),
    });
  };

  const isSubmitDisabled =
    !title.trim() ||
    ingredients.filter(i => i.ingredientId > 0).length === 0 ||
    steps.filter(s => s.instruction.trim()).length === 0 ||
    createMutation.isPending;

  if (isLoading) return <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>;
  if (error) return <Alert severity="error">Fehler beim Laden der Rezepte.</Alert>;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5">Rezepte</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => { resetForm(); setDialogOpen(true); }}>Neues Rezept</Button>
      </Box>

      {mutationError && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setMutationError(null)}>{mutationError}</Alert>}

      <Grid container spacing={2}>
        {recipes?.map(recipe => (
          <Grid key={recipe.id} size={{ xs: 12, sm: 6, md: 4 }}>
            <Card>
              <RecipeDetailCard recipe={recipe} />
              <CardActions>
                <IconButton color="error" size="small" onClick={() => setConfirmDelete(recipe)}>
                  <DeleteIcon />
                </IconButton>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog open={dialogOpen} onClose={() => { setDialogOpen(false); resetForm(); }} maxWidth="md" fullWidth>
        <DialogTitle>Neues Rezept</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 2 }}>
          {mutationError && <Alert severity="error">{mutationError}</Alert>}
          <TextField label="Titel" value={title} onChange={e => setTitle(e.target.value)} fullWidth required />
          <TextField label="Quell-URL (optional)" value={sourceUrl} onChange={e => setSourceUrl(e.target.value)} fullWidth />

          <Typography variant="subtitle1">Zutaten</Typography>
          {ingredients.map((ing) => (
            <Box key={ing.uuid} sx={{ display: 'flex', gap: 1 }}>
              <FormControl sx={{ minWidth: 160 }}>
                <InputLabel>Zutat</InputLabel>
                <Select
                  value={ing.ingredientId}
                  label="Zutat"
                  onChange={e => {
                    setIngredients(prev => prev.map(r => r.uuid === ing.uuid ? { ...r, ingredientId: Number(e.target.value) } : r));
                  }}
                >
                  <MenuItem value={0}><em>Wählen...</em></MenuItem>
                  {allIngredients?.map(a => <MenuItem key={a.id} value={a.id}>{a.name}</MenuItem>)}
                </Select>
              </FormControl>
              <TextField
                label="Menge" type="number" value={ing.quantity}
                onChange={e => setIngredients(prev => prev.map(r => r.uuid === ing.uuid ? { ...r, quantity: Number(e.target.value) } : r))}
                sx={{ width: 100 }}
              />
              <TextField
                label="Einheit" value={ing.unit}
                onChange={e => setIngredients(prev => prev.map(r => r.uuid === ing.uuid ? { ...r, unit: e.target.value } : r))}
                sx={{ width: 100 }}
              />
              <IconButton onClick={() => setIngredients(prev => prev.filter(r => r.uuid !== ing.uuid))} color="error"><DeleteIcon /></IconButton>
            </Box>
          ))}
          <Button onClick={() => setIngredients(prev => [...prev, { uuid: crypto.randomUUID(), ingredientId: 0, quantity: 1, unit: '' }])}>+ Zutat</Button>

          <Typography variant="subtitle1">Schritte</Typography>
          {steps.map((step, i) => (
            <Box key={step.uuid} sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
              <Typography sx={{ minWidth: 24 }}>{i + 1}.</Typography>
              <TextField
                label="Anweisung" value={step.instruction} fullWidth multiline
                onChange={e => setSteps(prev => prev.map(r => r.uuid === step.uuid ? { ...r, instruction: e.target.value } : r))}
              />
              <IconButton onClick={() => setSteps(prev => prev.filter(r => r.uuid !== step.uuid))} color="error"><DeleteIcon /></IconButton>
            </Box>
          ))}
          <Button onClick={() => setSteps(prev => [...prev, { uuid: crypto.randomUUID(), instruction: '' }])}>+ Schritt</Button>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setDialogOpen(false); resetForm(); }}>Abbrechen</Button>
          <Button variant="contained" onClick={handleCreate} disabled={isSubmitDisabled}>
            {createMutation.isPending ? 'Wird erstellt...' : 'Erstellen'}
          </Button>
        </DialogActions>
      </Dialog>

      <ConfirmDialog
        open={confirmDelete !== null}
        title="Rezept löschen"
        content={`"${confirmDelete?.title}" wirklich löschen?`}
        onConfirm={() => { if (confirmDelete) deleteMutation.mutate(confirmDelete.id); setConfirmDelete(null); }}
        onCancel={() => setConfirmDelete(null)}
      />
    </Box>
  );
}
