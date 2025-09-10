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

export const getPrefillPlugins = async componentType => {
  const resp = await get('/api/v2/prefill/plugins', {componentType});
  return resp.data;
};

export const getPrefillAttributes = async plugin => {
  const resp = await get(`/api/v2/prefill/plugins/${plugin}/attributes`);
  return resp.data;
};
