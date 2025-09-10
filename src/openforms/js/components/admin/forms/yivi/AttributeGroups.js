import {useAsync} from 'react-use';

import {get} from 'utils/fetch';

export const YIVI_ATTRIBUTE_GROUPS_ENDPOINT =
  '/api/v2/authentication/plugins/yivi/attribute-groups';

const getYiviAttributeGroups = async () => {
  const response = await get(YIVI_ATTRIBUTE_GROUPS_ENDPOINT);
  if (!response.ok) {
    throw new Error('Loading available attribute groups failed');
  }
  return response.data;
};

export const useGetYiviAttributeGroups = () => {
  const {
    loading,
    value: availableYiviAttributeGroups = [],
    error,
  } = useAsync(getYiviAttributeGroups, []);
  return {loading, availableYiviAttributeGroups, error};
};
