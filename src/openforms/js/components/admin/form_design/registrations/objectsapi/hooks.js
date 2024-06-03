import useAsync from 'react-use/esm/useAsync';
import {get} from 'utils/fetch';

import {REGISTRATION_OBJECTTYPES_ENDPOINT} from 'components/admin/form_design/constants';

export const useGetAvailableObjectTypes = () => {
  const {
    loading,
    value: availableObjecttypes = [],
    error,
  } = useAsync(
    async () => {
      const response = await get(REGISTRATION_OBJECTTYPES_ENDPOINT);
      if (!response.ok) {
        throw new Error('Loading available object types failed');
      }
      return response.data;
    },
    // available object types only need to be loaded once when the component mounts
    []
  );

  return {
    loading,
    availableObjecttypes,
    error,
  };
};
