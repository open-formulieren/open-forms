import {get} from 'utils/fetch';

export const getValidatorPlugins = async componentType => {
  const resp = await get(
    '/api/v2/validation/plugins',
    componentType ? {componentType: componentType} : {}
  );
  return resp.data;
};

export const getRegistrationAttributes = async () => {
  const resp = await get('/api/v2/registration/attributes');
  return resp.data;
};

export const getPrefillPlugins = async () => {
  const resp = await get('/api/v2/prefill/plugins');
  return resp.data;
};

// export const getPrefillAttributes = async plugin => {
//   // const resp = await get(`/api/v2/prefill/plugins/${plugin}/attributes`);
//   const resp = await get(`/api/v2/prefill/plugins/objects-api/groups`);
//   return resp.data;
// };

// export const getPrefillObjectsAPIGroups = async () => {
//   const resp = await get(`/api/v2/prefill/plugins/objects-api/groups`);
//   return resp.data;
// };

// export const getPrefillObjectsAPIObjecttypes = async () => {
//   const resp = await get(`/api/v2/prefill/plugins/objects-api/objecttypes/2`);
//   return resp.data;
// };

// export const getPrefillObjectsAPIObjecttypeVersions = async () => {
//   const resp = await get(
//     `/api/v2/prefill/plugins/objects-api/objecttypes/2/ac1fa3f8-fb2a-4fcb-b715-d480aceeda10/versions`
//   );
//   return resp.data;
// };

export const getPrefillObjectsAPIObjecttypeVersions = async () => {
  const resp = await get(
    `/api/v2/prefill/plugins/objects-api/objecttypes/ac1fa3f8-fb2a-4fcb-b715-d480aceeda10/versions/1/attributes`,
    {
      objects_api_group: '2',
    }
  );
  return resp.data;
};
