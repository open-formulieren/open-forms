import {rest} from 'msw';

import {API_BASE_URL} from 'utils/fetch';

const CATALOGUES = [
  {
    url: 'https://example.com/catalogi/api/v1/catalogussen/1',
    rsin: '000000000',
    domain: 'TEST',
    label: 'Catalogus 1',
  },
  {
    url: 'https://example.com/catalogi/api/v1/catalogussen/2',
    rsin: '000000000',
    domain: 'OTHER',
    label: 'Catalogus 2',
  },
  {
    url: 'https://example.com/catalogi/api/v1/catalogussen/3',
    rsin: '111111111',
    domain: 'TEST',
    label: 'TEST (111111111)',
    catalogusLabel: '',
  },
];

export const mockCataloguesGet = () =>
  rest.get(`${API_BASE_URL}/api/v2/registration/plugins/zgw-api/catalogues`, (req, res, ctx) => {
    return res(ctx.json(CATALOGUES));
  });
