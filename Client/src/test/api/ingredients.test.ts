import { describe, it, expect, vi, beforeEach } from 'vitest';
import apiClient from '../../api/client';
import { getIngredients, createIngredient, deleteIngredient } from '../../api/ingredients';

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

describe('getIngredients', () => {
  it('calls GET /ingredients and returns data', async () => {
    const data = [{ id: 1, name: 'Mehl', defaultUnit: 'g' }];
    mockClient.get.mockResolvedValueOnce({ data });

    const result = await getIngredients();

    expect(mockClient.get).toHaveBeenCalledWith('/ingredients');
    expect(result).toEqual(data);
  });
});

describe('createIngredient', () => {
  it('calls POST /ingredients with correct body and returns data', async () => {
    const dto = { name: 'Mehl', defaultUnit: 'g' };
    const created = { id: 1, ...dto };
    mockClient.post.mockResolvedValueOnce({ data: created });

    const result = await createIngredient(dto);

    expect(mockClient.post).toHaveBeenCalledWith('/ingredients', dto);
    expect(result).toEqual(created);
  });
});

describe('deleteIngredient', () => {
  it('calls DELETE /ingredients/1', async () => {
    mockClient.delete.mockResolvedValueOnce({ data: undefined });

    await deleteIngredient(1);

    expect(mockClient.delete).toHaveBeenCalledWith('/ingredients/1');
  });
});
