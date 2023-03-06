import {rest} from 'msw';

import {SERVICES_ENDPOINT} from './constants';

export const BASE_URL = 'http://localhost:6006';

export const mockServices = services =>
  rest.get(`${BASE_URL}${SERVICES_ENDPOINT}`, (req, res, ctx) => {
    return res(ctx.json(services));
  });

export const mockServiceFetchConfigurations = serviceFetchConfigurations =>
  rest.get(`${BASE_URL}/api/v2/service-fetch-configurations`, (req, res, ctx) => {
    return res(ctx.json(serviceFetchConfigurations));
  });
