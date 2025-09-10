import {getPrefillAttributes as getYiviPrefillAttributes} from 'components/admin/form_design/variables/prefill/yivi/YiviFields';
import {getYiviAttributeGroups} from 'components/admin/forms/yivi/AttributeGroups';
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

export const getPrefillAttributes = async (plugin, context = {}) => {
  // special case yivi which takes the surrounding form context into account
  if (plugin === 'yivi') {
    const attributeGroups = await getYiviAttributeGroups();
    const {availablePrefillPlugins, authBackends} = context;
    const attributes = getYiviPrefillAttributes(
      availablePrefillPlugins,
      authBackends,
      attributeGroups
    );
    return attributes.map(([attribute, label]) => ({id: attribute, label}));
  }

  const resp = await get(`/api/v2/prefill/plugins/${plugin}/attributes`);
  return resp.data;
};
