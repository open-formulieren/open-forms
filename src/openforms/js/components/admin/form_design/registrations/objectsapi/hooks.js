import useAsync from 'react-use/esm/useAsync';

import {REGISTRATION_OBJECTTYPES_ENDPOINT} from 'components/admin/form_design/constants';
import {getInformatieObjectTypen} from 'components/form/file';
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

export const useGetAvailableInformatieObjecttypen = objectsApiGroup => {
  const {
    loading,
    value: availableInformatieobjecttypen = [],
    error,
  } = useAsync(async () => {
    if (!objectsApiGroup) return [];
    const response = await getInformatieObjectTypen('objects_api', {objectsApiGroup});

    if (!response.ok) {
      throw new Error('Loading available informatieobjecttypen failed');
    }
    return response.data;
  }, [objectsApiGroup]);

  return {
    loading,
    availableInformatieobjecttypen,
    error,
  };
};
