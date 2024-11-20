import {HttpResponse, http} from 'msw';

import {API_BASE_URL} from 'utils/fetch';

export const mockProcessDefinitionsGet = (definitions = []) =>
  http.get(`${API_BASE_URL}/api/v2/registration/plugins/camunda/process-definitions`, () =>
    HttpResponse.json(definitions)
  );
