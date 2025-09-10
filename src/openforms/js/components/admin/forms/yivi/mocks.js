import {HttpResponse, http} from 'msw';

import {API_BASE_URL} from 'utils/fetch';

const DEFAULT_ATTRIBUTE_GROUPS = [
  {
    uuid: 'efffa9ef-5697-4fea-9f7b-c296cc3f95fa',
    name: 'A custom group for fetching custom attributes',
    description: 'Custom group description',
    attributes: [
      'irma.gemeente.personalDetails.firstName',
      'irma.gemeente.personalDetails.lastName',
    ],
  },
  {
    uuid: 'fc9eff0e-4b87-4231-afd1-76e3fe5e8530',
    name: 'Profile group',
    description: '',
    attributes: [
      'irma.gemeente.personalDetails.firstName',
      'irma.gemeente.personalDetails.dateOfBirth',
    ],
  },
];

export const mockYiviAttributeGroupsGet = (groups = DEFAULT_ATTRIBUTE_GROUPS) =>
  http.get(`${API_BASE_URL}/api/v2/authentication/plugins/yivi/attribute-groups`, () =>
    HttpResponse.json(groups)
  );
