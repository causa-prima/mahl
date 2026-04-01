import apiClient from './client';
import type { ShoppingListResponseDto } from '../types';

export const getShoppingList = () => apiClient.get<ShoppingListResponseDto>('/shopping-list').then(r => r.data);
export const generateShoppingList = () => apiClient.post('/shopping-list/generate');
export const checkItem = (id: number) => apiClient.put(`/shopping-list/items/${id}/check`);
export const uncheckItem = (id: number) => apiClient.put(`/shopping-list/items/${id}/uncheck`);
