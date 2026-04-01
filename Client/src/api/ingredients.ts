import apiClient from './client';
import type { IngredientDto, CreateIngredientDto } from '../types';

export const getIngredients = () => apiClient.get<IngredientDto[]>('/ingredients').then(r => r.data);
export const getIngredient = (id: number) => apiClient.get<IngredientDto>(`/ingredients/${id}`).then(r => r.data);
export const createIngredient = (dto: CreateIngredientDto) => apiClient.post<IngredientDto>('/ingredients', dto).then(r => r.data);
export const deleteIngredient = (id: number) => apiClient.delete(`/ingredients/${id}`);
