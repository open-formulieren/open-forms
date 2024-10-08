import {rest} from 'msw';

import {API_BASE_URL} from 'utils/fetch';

import {
  DMN_DECISION_DEFINITIONS_LIST,
  DMN_DECISION_DEFINITIONS_PARAMS_LIST,
  DMN_DECISION_DEFINITIONS_VERSIONS_LIST,
  SERVICES_ENDPOINT,
} from './constants';

export const mockServicesGet = services =>
  rest.get(`${API_BASE_URL}${SERVICES_ENDPOINT}`, (req, res, ctx) => {
    return res(ctx.json(services));
  });

export const mockServiceFetchConfigurationsGet = serviceFetchConfigurations =>
  rest.get(`${API_BASE_URL}/api/v2/service-fetch-configurations`, (req, res, ctx) => {
    return res(ctx.json(serviceFetchConfigurations));
  });

export const mockDMNDecisionDefinitionsGet = engineDefinitionsMapping =>
  rest.get(`${API_BASE_URL}${DMN_DECISION_DEFINITIONS_LIST}`, (req, res, ctx) => {
    const engine = req.url.searchParams.get('engine');

    return res(ctx.json(engineDefinitionsMapping[engine]));
  });

export const mockDMNDecisionDefinitionVersionsGet = rest.get(
  `${API_BASE_URL}${DMN_DECISION_DEFINITIONS_VERSIONS_LIST}`,
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

export const mockDMNParametersGet = definitionsParams =>
  rest.get(`${API_BASE_URL}${DMN_DECISION_DEFINITIONS_PARAMS_LIST}`, (req, res, ctx) => {
    const definition = req.url.searchParams.get('definition');
    const version = req.url.searchParams.get('version');

    const versionedParams = definitionsParams[definition]?._versions?.[version];
    const unVersionedParams = definitionsParams[definition];
    const {inputs, outputs} = versionedParams ?? unVersionedParams;
    return res(ctx.json({inputs, outputs}));
  });

export const mockPrefillAttributesGet = pluginAttributes =>
  rest.get(`${API_BASE_URL}/api/v2/prefill/plugins/:plugin/attributes`, (req, res, ctx) => {
    const {plugin} = req.params;
    const attributeList = pluginAttributes[plugin] || [];
    return res(ctx.json(attributeList));
  });

export const mockObjectsAPIPrefillPropertiesGet = pluginProperties =>
  rest.get(
    `${API_BASE_URL}/api/v2/prefill/plugins/objects-api/objecttypes/:uuid/versions/:version/properties`,
    (req, res, ctx) => {
      const {uuid, version} = req.params;
      const propertyList = pluginProperties[uuid][version] || [];
      return res(ctx.json(propertyList));
    }
  );
