import axios from 'axios';
import { Paths } from './api-types/routePaths';
import { Item } from './api-types/components/schemas';

const api = axios.create({
  baseURL: 'http://localhost:8000/',
});

export const fetchItems = async (): Promise<Item[]> => {
  const response = await api.get<Item[]>(Paths.ITEM_SET_2);
  return response.data;
};

export const createItem = async (item: Item): Promise<Item> => {
  const response = await api.post<Item>(Paths.ITEM_SET_2, item);
  return response.data;
};
