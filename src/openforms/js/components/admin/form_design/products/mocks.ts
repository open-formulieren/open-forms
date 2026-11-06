import {HttpResponse, http} from 'msw';

import {API_BASE_URL} from 'utils/fetch';

import {Product} from '@/components/types';

export const mockProductsGet = (products: Product[]) =>
  http.get(`${API_BASE_URL}/api/v2/products`, () => HttpResponse.json(products));
