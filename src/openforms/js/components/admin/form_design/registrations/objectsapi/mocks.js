import {rest} from 'msw';

import {API_BASE_URL} from 'utils/fetch';

export const mockObjecttypesGet = objecttypes =>
  rest.get(`${API_BASE_URL}/api/v2/objects-api/object-types`, (req, res, ctx) => {
    return res(ctx.json(objecttypes));
  });

export const mockObjecttypeVersionsGet = versions =>
  rest.get(`${API_BASE_URL}/api/v2/objects-api/object-types/:uuid/versions`, (req, res, ctx) => {
    return res(ctx.json(versions));
  });

export const mockObjecttypesError = () =>
  rest.all(`${API_BASE_URL}/api/v2/*`, (req, res, ctx) => {
    return res(ctx.status(500));
  });

export const mockTargetPathsPost = paths =>
  rest.post(
    `${API_BASE_URL}/api/v2/registration/plugins/objects-api/target-paths`,
    async (req, res, ctx) => {
      const requestBody = await req.json();
      const variableJsonSchemaType = requestBody.variableJsonSchema.type;

      return res(ctx.json(paths[variableJsonSchemaType]));
    }
  );

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
  rest.get(`${API_BASE_URL}/api/v2/objects-api/catalogues`, (req, res, ctx) => {
    return res(ctx.json(CATALOGUES));
  });

const DOCUMENT_TYPES = {
  'https://example.com/catalogi/api/v1/catalogussen/1': [
    {
      url: 'https://example.com/catalogi/api/v1/iot/1',
      omschrijving: 'Test PDF',
      catalogusLabel: 'Catalogus 1',
      isPublished: true,
    },
    {
      url: 'https://example.com/catalogi/api/v1/iot/2',
      omschrijving: 'Test attachment',
      catalogusLabel: 'Catalogus 1',
      isPublished: true,
    },
  ],
  'https://example.com/catalogi/api/v1/catalogussen/2': [
    {
      url: 'https://example.com/catalogi/api/v1/iot/1',
      omschrijving: 'Other PDF',
      catalogusLabel: 'Catalogus 2',
      isPublished: true,
    },
    {
      url: 'https://example.com/catalogi/api/v1/iot/4',
      omschrijving: 'Other attachment',
      catalogusLabel: 'Catalogus 2',
      isPublished: true,
    },
  ],
  'https://example.com/catalogi/api/v1/catalogussen/3': [
    {
      url: 'https://example.com/catalogi/api/v1/iot/10',
      omschrijving: 'Document type 1',
      catalogusLabel: 'TEST (111111111)',
      isPublished: false,
    },
    {
      url: 'https://example.com/catalogi/api/v1/iot/11',
      omschrijving: 'Document type 2',
      catalogusLabel: 'TEST (111111111)',
      isPublished: true,
    },
    {
      url: 'https://example.com/catalogi/api/v1/iot/12',
      omschrijving: 'Document type 3',
      catalogusLabel: 'TEST (111111111)',
      isPublished: true,
    },
    {
      url: 'https://example.com/catalogi/api/v1/iot/13',
      omschrijving: 'Document type 4 with a rather long draft description',
      catalogusLabel: 'TEST (111111111)',
      isPublished: false,
    },
  ],
};

export const mockDocumentTypesGet = () =>
  rest.get(`${API_BASE_URL}/api/v2/objects-api/informatieobjecttypen`, (req, res, ctx) => {
    const catalogusUrl = req.url.searchParams.get('catalogus_url');
    const match = DOCUMENT_TYPES[catalogusUrl] ?? [];
    return res(ctx.json(match));
  });
