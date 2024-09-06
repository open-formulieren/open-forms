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

const CASE_TYPES = {
  'https://example.com/catalogi/api/v1/catalogussen/1': [
    {
      identification: 'ZT01',
      description: 'Permit',
      isPublished: true,
    },
    {
      identification: 'ZT02',
      description: 'Request passport',
      isPublished: true,
    },
    {
      identification: 'ZT03',
      description: "Request driver's license",
      isPublished: true,
    },
  ],
  'https://example.com/catalogi/api/v1/catalogussen/2': [
    {
      identification: 'ZT11',
      description: 'Some case type',
      isPublished: true,
    },
  ],
  'https://example.com/catalogi/api/v1/catalogussen/3': [
    {
      identification: 'ZT21',
      description: 'Published case type',
      isPublished: true,
    },
    {
      identification: 'ZT22',
      description: 'Draft case type',
      isPublished: false,
    },
  ],
};

export const mockCaseTypesGet = () =>
  rest.get(`${API_BASE_URL}/api/v2/registration/plugins/zgw-api/case-types`, (req, res, ctx) => {
    const catalogueUrl = req.url.searchParams.get('catalogue_url');
    const match = CASE_TYPES[catalogueUrl] ?? [];
    return res(ctx.json(match));
  });
