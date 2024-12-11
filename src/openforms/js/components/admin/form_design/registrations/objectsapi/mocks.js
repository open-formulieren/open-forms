import {HttpResponse, http} from 'msw';

import {API_BASE_URL} from 'utils/fetch';

export const mockObjecttypesGet = objecttypes =>
  http.get(`${API_BASE_URL}/api/v2/objects-api/object-types`, () => HttpResponse.json(objecttypes));

export const mockObjecttypeVersionsGet = versions =>
  http.get(`${API_BASE_URL}/api/v2/objects-api/object-types/:uuid/versions`, ({params}) => {
    if (params.uuid === 'a-non-existing-uuid') {
      return HttpResponse.json([]);
    }
    return HttpResponse.json(versions);
  });

export const mockObjecttypesError = () =>
  http.all(`${API_BASE_URL}/api/v2/*`, () =>
    HttpResponse.json(
      {
        type: 'http://localhost:8000/fouten/APIException/',
        code: 'server-error',
        title: 'Internal Server Error.',
        status: 500,
        detail: '',
        instance: 'urn:uuid:41e0174a-efc2-4cc0-9bf2-8366242a4e75',
      },
      {status: 500}
    )
  );

export const mockTargetPathsPost = paths =>
  http.post(
    `${API_BASE_URL}/api/v2/registration/plugins/objects-api/target-paths`,
    async ({request}) => {
      const requestBody = await request.json();
      const variableJsonSchemaType = requestBody.variableJsonSchema.type;

      return HttpResponse.json(paths[variableJsonSchemaType]);
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
  http.get(`${API_BASE_URL}/api/v2/objects-api/catalogues`, () => HttpResponse.json(CATALOGUES));

const DOCUMENT_TYPES = {
  'https://example.com/catalogi/api/v1/catalogussen/1': [
    {
      url: 'https://example.com/catalogi/api/v1/iot/1',
      description: 'Test PDF',
      catalogueLabel: 'Catalogus 1',
      isPublished: true,
    },
    {
      url: 'https://example.com/catalogi/api/v1/iot/2',
      description: 'Test attachment',
      catalogueLabel: 'Catalogus 1',
      isPublished: true,
    },
  ],
  'https://example.com/catalogi/api/v1/catalogussen/2': [
    {
      url: 'https://example.com/catalogi/api/v1/iot/1',
      description: 'Other PDF',
      catalogueLabel: 'Catalogus 2',
      isPublished: true,
    },
    {
      url: 'https://example.com/catalogi/api/v1/iot/4',
      description: 'Other attachment',
      catalogueLabel: 'Catalogus 2',
      isPublished: true,
    },
  ],
  'https://example.com/catalogi/api/v1/catalogussen/3': [
    {
      url: 'https://example.com/catalogi/api/v1/iot/10',
      description: 'Document type 1',
      catalogueLabel: 'TEST (111111111)',
      isPublished: false,
    },
    {
      url: 'https://example.com/catalogi/api/v1/iot/11',
      description: 'Document type 2',
      catalogueLabel: 'TEST (111111111)',
      isPublished: true,
    },
    {
      url: 'https://example.com/catalogi/api/v1/iot/12',
      description: 'Document type 3',
      catalogueLabel: 'TEST (111111111)',
      isPublished: true,
    },
    {
      url: 'https://example.com/catalogi/api/v1/iot/13',
      description: 'Document type 4 with a rather long draft description',
      catalogueLabel: 'TEST (111111111)',
      isPublished: false,
    },
  ],
};

export const mockDocumentTypesGet = () =>
  http.get(`${API_BASE_URL}/api/v2/objects-api/document-types`, ({request}) => {
    const url = new URL(request.url);
    const catalogusUrl = url.searchParams.get('catalogue_url');
    const match = DOCUMENT_TYPES[catalogusUrl] ?? [];
    return HttpResponse.json(match);
  });
