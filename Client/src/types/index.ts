export interface IngredientDto { id: number; name: string; defaultUnit: string; alwaysInStock: boolean; }
export interface CreateIngredientDto { name: string; defaultUnit: string; }
export interface RecipeSummaryDto { id: number; title: string; sourceUrl?: string; sourceImagePath?: string; }
export interface RecipeIngredientDto { id: number; ingredientId: number; ingredientName: string; quantity: number; unit: string; }
export interface StepDto { id: number; stepNumber: number; instruction: string; }
export interface RecipeDto { id: number; title: string; sourceUrl?: string; sourceImagePath?: string; ingredients: RecipeIngredientDto[]; steps: StepDto[]; }
export interface CreateRecipeIngredientDto { ingredientId: number; quantity: number; unit: string; }
export interface CreateStepDto { instruction: string; }
export interface CreateRecipeDto { title: string; sourceUrl?: string; ingredients: CreateRecipeIngredientDto[]; steps: CreateStepDto[]; }
export interface WeeklyPoolEntryDto { id: number; recipeId: number; recipeTitle: string; addedAt: string; }
export interface AddToPoolDto { recipeId: number; }
export interface ShoppingListItemDto { id: number; ingredientId: number; ingredientName: string; quantity: number; unit: string; boughtAt?: string; }
export interface ShoppingListResponseDto { openItems: ShoppingListItemDto[]; boughtItems: ShoppingListItemDto[]; }
