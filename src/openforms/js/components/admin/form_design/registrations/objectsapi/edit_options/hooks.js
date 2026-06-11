import {useContext, useMemo} from 'react';
import {useAsync} from 'react-use';

import {APIContext} from 'components/admin/form_design/Context';

import {asJsonSchema, fetchTargetPaths} from '../utils';

export const useVariableJsonSchema = (variable, components, transformToList = undefined) => {
  const schema = useMemo(
    () => asJsonSchema(variable, components, transformToList),
    [variable, components, transformToList]
  );
  return schema;
};

export const useFetchTargetPaths = ({
  objectsApiGroup,
  objecttype,
  objecttypeVersion,
  variableJsonSchema,
}) => {
  const {csrftoken} = useContext(APIContext);

  const {
    loading,
    value: targetPaths,
    error,
  } = useAsync(
    async () =>
      await fetchTargetPaths(
        csrftoken,
        objectsApiGroup,
        objecttype,
        objecttypeVersion,
        variableJsonSchema
      ),
    [csrftoken, objectsApiGroup, objecttype, objecttypeVersion, variableJsonSchema]
  );

  return {loading, targetPaths, error};
};
