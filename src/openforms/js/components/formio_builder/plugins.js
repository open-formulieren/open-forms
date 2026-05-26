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

  // If the plugin declares a custom attributes endpoint, use it instead of the
  // default static list. This lets third-party plugins supply context-aware
  // attributes without requiring changes to this file.  The matching auth
  // backend's options are forwarded as query parameters so the endpoint can
  // scope the attribute list to the selected authentication flow.
  const {availablePrefillPlugins = [], authBackends = []} = context;
  const pluginMeta = availablePrefillPlugins.find(p => p.id === plugin);
  if (pluginMeta?.customAttributesUrl) {
    const requiredPlugins = pluginMeta.requiresAuthPlugin || [];
    const authBackend = authBackends.find(b => requiredPlugins.includes(b.backend));
    const queryParams = authBackend?.options || {};
    const resp = await get(pluginMeta.customAttributesUrl, queryParams);
    if (!resp.ok) return [];
    return (resp.data || []).map(item => ({id: item.id, label: item.label || item.id}));
  }

  const resp = await get(`/api/v2/prefill/plugins/${plugin}/attributes`);
  return resp.data;
};
