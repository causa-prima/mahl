import apiClient from './client';
import type { WeeklyPoolEntryDto, AddToPoolDto } from '../types';

export const getWeeklyPool = () => apiClient.get<WeeklyPoolEntryDto[]>('/weekly-pool').then(r => r.data);
export const addToPool = (dto: AddToPoolDto) => apiClient.post<WeeklyPoolEntryDto>('/weekly-pool', dto).then(r => r.data);
export const removeFromPool = (entryId: number) => apiClient.delete(`/weekly-pool/${entryId}`);
