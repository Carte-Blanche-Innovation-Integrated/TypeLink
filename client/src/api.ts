import axios from 'axios';
import { Paths } from './api-types/routePaths';
import { Item } from './api-types/components/schemas';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
});

export const fetchItems = async (): Promise<Item[]> => {
  const response = await api.get<Item[]>(Paths.ITEMS_LIST);
  return response.data;
};

export const createItem = async (item: Item): Promise<Item> => {
  const response = await api.post<Item>(Paths.ITEMS_LIST, item);
  return response.data;
};
