import {rest} from 'msw';

import {DMN_DECISION_DEFINITIONS_LIST, SERVICES_ENDPOINT} from './constants';

export const BASE_URL = process.env.SB_BASE_URL || '';

export const mockServicesGet = services =>
  rest.get(`${BASE_URL}${SERVICES_ENDPOINT}`, (req, res, ctx) => {
    return res(ctx.json(services));
  });

export const mockServiceFetchConfigurationsGet = serviceFetchConfigurations =>
  rest.get(`${BASE_URL}/api/v2/service-fetch-configurations`, (req, res, ctx) => {
    return res(ctx.json(serviceFetchConfigurations));
  });

export const mockDMNDecisionDefinitionsGet = engineDefinitionsMapping =>
  rest.get(`${BASE_URL}/api/v2/dmn/decision-definitions`, (req, res, ctx) => {
    const engine = req.url.searchParams.get('engine');

    return res(ctx.json(engineDefinitionsMapping[engine]));
  });

export const mockDMNDecisionDefinitionVersionsGet = rest.get(
  `${BASE_URL}/api/v2/dmn/decision-definitions/versions`,
  (req, res, ctx) => {
    return res(
      ctx.json([
        {
          id: '2',
          label: 'v2 (version tag: n/a)',
        },
        {
          id: '1',
          label: 'v1 (version tag: n/a)',
        },
      ])
    );
  }
);
