import apiClient from './client';
import type { RecipeSummaryDto, RecipeDto, CreateRecipeDto } from '../types';

export const getRecipes = () => apiClient.get<RecipeSummaryDto[]>('/recipes').then(r => r.data);
export const getRecipe = (id: number) => apiClient.get<RecipeDto>(`/recipes/${id}`).then(r => r.data);
export const createRecipe = (dto: CreateRecipeDto) => apiClient.post<RecipeDto>('/recipes', dto).then(r => r.data);
export const deleteRecipe = (id: number) => apiClient.delete(`/recipes/${id}`);
