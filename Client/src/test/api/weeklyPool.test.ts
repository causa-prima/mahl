import { describe, it, expect, vi, beforeEach } from 'vitest';
import apiClient from '../../api/client';
import { getWeeklyPool, addToPool, removeFromPool } from '../../api/weeklyPool';

vi.mock('../../api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

const mockClient = vi.mocked(apiClient);

beforeEach(() => {
  vi.clearAllMocks();
});

describe('getWeeklyPool', () => {
  it('calls GET /weekly-pool and returns data', async () => {
    const data = [{ id: 1, recipeId: 5, recipeName: 'Pasta' }];
    mockClient.get.mockResolvedValueOnce({ data });

    const result = await getWeeklyPool();

    expect(mockClient.get).toHaveBeenCalledWith('/weekly-pool');
    expect(result).toEqual(data);
  });
});

describe('addToPool', () => {
  it('calls POST /weekly-pool with correct body and returns data', async () => {
    const dto = { recipeId: 5 };
    const created = { id: 1, recipeId: 5, recipeName: 'Pasta' };
    mockClient.post.mockResolvedValueOnce({ data: created });

    const result = await addToPool(dto);

    expect(mockClient.post).toHaveBeenCalledWith('/weekly-pool', dto);
    expect(result).toEqual(created);
  });
});

describe('removeFromPool', () => {
  it('calls DELETE /weekly-pool/3', async () => {
    mockClient.delete.mockResolvedValueOnce({ data: undefined });

    await removeFromPool(3);

    expect(mockClient.delete).toHaveBeenCalledWith('/weekly-pool/3');
  });
});
