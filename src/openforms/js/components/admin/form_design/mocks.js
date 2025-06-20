import {HttpResponse, http} from 'msw';

import {API_BASE_URL} from 'utils/fetch';

import {
  DMN_DECISION_DEFINITIONS_LIST,
  DMN_DECISION_DEFINITIONS_PARAMS_LIST,
  DMN_DECISION_DEFINITIONS_VERSIONS_LIST,
  FORM_ENDPOINT,
  SERVICES_ENDPOINT,
} from './constants';

export const mockServicesGet = services =>
  http.get(`${API_BASE_URL}${SERVICES_ENDPOINT}`, () => HttpResponse.json(services));

export const mockServiceFetchConfigurationsGet = serviceFetchConfigurations =>
  http.get(`${API_BASE_URL}/api/v2/service-fetch-configurations`, () =>
    HttpResponse.json(serviceFetchConfigurations)
  );

export const mockDMNDecisionDefinitionsGet = engineDefinitionsMapping =>
  http.get(`${API_BASE_URL}${DMN_DECISION_DEFINITIONS_LIST}`, ({request}) => {
    const url = new URL(request.url);
    const engine = url.searchParams.get('engine');

    return HttpResponse.json(engineDefinitionsMapping[engine]);
  });

export const mockDMNDecisionDefinitionVersionsGet = http.get(
  `${API_BASE_URL}${DMN_DECISION_DEFINITIONS_VERSIONS_LIST}`,
  () =>
    HttpResponse.json([
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

export const mockDMNParametersGet = definitionsParams =>
  http.get(`${API_BASE_URL}${DMN_DECISION_DEFINITIONS_PARAMS_LIST}`, ({request}) => {
    const url = new URL(request.url);
    const definition = url.searchParams.get('definition');
    const version = url.searchParams.get('version');

    const versionedParams = definitionsParams[definition]?._versions?.[version];
    const unVersionedParams = definitionsParams[definition];
    const {inputs, outputs} = versionedParams ?? unVersionedParams;
    return HttpResponse.json({inputs, outputs});
  });

export const mockPrefillAttributesGet = pluginAttributes =>
  http.get(`${API_BASE_URL}/api/v2/prefill/plugins/:plugin/attributes`, ({params}) => {
    const {plugin} = params;
    const attributeList = pluginAttributes[plugin] || [];
    return HttpResponse.json(attributeList);
  });

export const mockObjectsAPIPrefillPropertiesGet = pluginProperties =>
  http.get(
    `${API_BASE_URL}/api/v2/prefill/plugins/objects-api/objecttypes/:uuid/versions/:version/properties`,
    ({params}) => {
      const {uuid, version} = params;
      const propertyList = pluginProperties[uuid][version] || [];
      return HttpResponse.json(propertyList);
    }
  );

export const mockFormJsonSchemaGet = schema =>
  http.get(`${API_BASE_URL}/api/v2/forms/:uuid/json_schema`, () => {
    if (schema === undefined) {
      return new HttpResponse(null, {status: 500, statusText: 'Schema generation error'});
    } else {
      return HttpResponse.json(schema);
    }
  });
