import {HttpResponse, http} from 'msw';

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
  http.get(`${API_BASE_URL}/api/v2/registration/plugins/zgw-api/catalogues`, () =>
    HttpResponse.json(CATALOGUES)
  );

export const mockCataloguesGetError = () =>
  http.get(`${API_BASE_URL}/api/v2/registration/plugins/zgw-api/catalogues`, () =>
    HttpResponse.json({unexpected: 'error'}, {status: 500})
  );

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
    {
      identification: 'ZT23',
      description: 'Published case type with a rather long description',
      isPublished: true,
    },
  ],
};

export const mockCaseTypesGet = () =>
  http.get(`${API_BASE_URL}/api/v2/registration/plugins/zgw-api/case-types`, ({request}) => {
    const url = new URL(request.url);
    const catalogueUrl = url.searchParams.get('catalogue_url');
    const match = CASE_TYPES[catalogueUrl] ?? [];
    return HttpResponse.json(match);
  });

const DOCUMENT_TYPES = {
  ZT01: [
    {
      description: 'Attachment',
      isPublished: true,
    },
    {
      description: 'Picture or scan of passport/identity card',
      isPublished: true,
    },
  ],
  ZT02: [
    {
      description: 'Attachment',
      isPublished: true,
    },
    {
      description: 'Other',
      isPublished: true,
    },
  ],
  ZT03: [],
  ZT11: [
    {
      description: 'Attachment',
      isPublished: true,
    },
  ],
  ZT21: [
    {
      description: 'Attachment',
      isPublished: true,
    },
  ],
  ZT22: [
    {
      description: 'Draft document type for draft case type',
      isPublished: false,
    },
    {
      description: 'Published document type for draft case type',
      isPublished: true,
    },
  ],
  ZT23: [
    {
      description: 'Attachment',
      isPublished: true,
    },
  ],
};

export const mockDocumenTypesGet = () =>
  http.get(`${API_BASE_URL}/api/v2/registration/plugins/zgw-api/document-types`, ({request}) => {
    const url = new URL(request.url);
    const caseTypeIdentification = url.searchParams.get('case_type_identification');
    const match = DOCUMENT_TYPES[caseTypeIdentification] ?? [];
    return HttpResponse.json(match);
  });

// The backend must filter out the 'initiator' as there can only be one.
const ROLE_TYPES = [
  {
    description: 'Baliemedewerker',
    descriptionGeneric: 'klantcontacter',
  },
  {
    description: 'Belanghebbende',
    descriptionGeneric: 'belanghebbende',
  },
];

export const mockRoleTypesGet = () =>
  http.get(`${API_BASE_URL}/api/v2/registration/plugins/zgw-api/role-types`, () =>
    HttpResponse.json(ROLE_TYPES)
  );

const PRODUCTS = [
  {
    url: 'https://example.com/product/1234',
  },
  {
    url: 'https://example.com/product/4321',
    description: undefined,
  },
  {
    url: 'https://example.com/product/1423',
    description: 'Product 1423',
  },
];

export const mockProductsGet = () =>
  http.get(`${API_BASE_URL}/api/v2/registration/plugins/zgw-api/products`, () =>
    HttpResponse.json(PRODUCTS)
  );
