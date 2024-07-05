import {rest} from 'msw';

import {API_BASE_URL} from 'utils/fetch';

export const mockInformatieobjecttypenGet = informatieobjecttypen =>
  rest.get(`${API_BASE_URL}/api/v2/registration/informatieobjecttypen`, (req, res, ctx) => {
    return res(ctx.json(informatieobjecttypen));
  });
