import {rest} from 'msw';

import {API_BASE_URL} from 'utils/fetch';

export const mockProcessDefinitionsGet = (definitions = []) =>
  rest.get(
    `${API_BASE_URL}/api/v2/registration/plugins/camunda/process-definitions`,
    (req, res, ctx) => res(ctx.json(definitions))
  );
