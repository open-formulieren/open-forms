import useAsync from 'react-use/esm/useAsync';

import {REGISTRATION_OBJECTTYPES_ENDPOINT} from 'components/admin/form_design/constants';
import {get} from 'utils/fetch';

export const useGetAvailableObjectTypes = objectsApiGroup => {
  const {
    loading,
    value: availableObjecttypes = [],
    error,
  } = useAsync(async () => {
    if (!objectsApiGroup) return [];
    const response = await get(REGISTRATION_OBJECTTYPES_ENDPOINT, {
      objects_api_group: objectsApiGroup,
    });
    if (!response.ok) {
      throw new Error('Loading available object types failed');
    }
    return response.data;
  }, [objectsApiGroup]);

  return {
    loading,
    availableObjecttypes,
    error,
  };
};
