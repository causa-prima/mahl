import { describe, it, expect, vi, beforeEach } from 'vitest';
import apiClient from '../../api/client';
import { getShoppingList, generateShoppingList, checkItem, uncheckItem } from '../../api/shoppingList';

vi.mock('../../api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}));

const mockClient = vi.mocked(apiClient);

beforeEach(() => {
  vi.clearAllMocks();
});

describe('getShoppingList', () => {
  it('calls GET /shopping-list and returns data', async () => {
    const data = { items: [] };
    mockClient.get.mockResolvedValueOnce({ data });

    const result = await getShoppingList();

    expect(mockClient.get).toHaveBeenCalledWith('/shopping-list');
    expect(result).toEqual(data);
  });
});

describe('generateShoppingList', () => {
  it('calls POST /shopping-list/generate', async () => {
    mockClient.post.mockResolvedValueOnce({ data: undefined });

    await generateShoppingList();

    expect(mockClient.post).toHaveBeenCalledWith('/shopping-list/generate');
  });
});

describe('checkItem', () => {
  it('calls PUT /shopping-list/items/1/check', async () => {
    mockClient.put.mockResolvedValueOnce({ data: undefined });

    await checkItem(1);

    expect(mockClient.put).toHaveBeenCalledWith('/shopping-list/items/1/check');
  });
});

describe('uncheckItem', () => {
  it('calls PUT /shopping-list/items/2/uncheck', async () => {
    mockClient.put.mockResolvedValueOnce({ data: undefined });

    await uncheckItem(2);

    expect(mockClient.put).toHaveBeenCalledWith('/shopping-list/items/2/uncheck');
  });
});
