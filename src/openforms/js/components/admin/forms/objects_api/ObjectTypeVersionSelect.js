import {useFormikContext} from 'formik';
import _ from 'lodash';
import {FormattedMessage} from 'react-intl';
import useAsync from 'react-use/esm/useAsync';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';
import {get} from 'utils/fetch';

import {useSynchronizeSelect} from './hooks';

const getObjecttypeVersionsEndpoint = uuid => {
  const bits = ['/api/v2/objects-api/object-types', encodeURIComponent(uuid), 'versions'];
  return bits.join('/');
};

const getAvailableVersions = async (uuid, apiGroupID) => {
  const endpoint = getObjecttypeVersionsEndpoint(uuid);
  const response = await get(endpoint, {objects_api_group: apiGroupID});
  if (!response.ok) {
    throw new Error('Loading available object type versions failed');
  }
  const versions = response.data;
  return versions.sort((v1, v2) => v2.version - v1.version);
};

const ObjectTypeVersionSelect = ({
  objectTypeName = 'objecttype',
  objectTypeVersionName = 'objecttypeVersion',
  apiGroupName = 'objectsApiGroup',
}) => {
  const {values} = useFormikContext();
  const objectsApiGroup = _.get(values, apiGroupName, null);
  const objecttype = _.get(values, objectTypeName, '');

  const {
    loading,
    value: versions = [],
    error,
  } = useAsync(async () => {
    if (!objectsApiGroup || !objecttype) return [];
    return getAvailableVersions(objecttype, objectsApiGroup);
  }, [objectsApiGroup, objecttype]);
  if (error) throw error;

  const choices = loading
    ? []
    : versions.map(version => [version.version, `${version.version} (${version.status})`]);

  useSynchronizeSelect(objectTypeVersionName, loading, choices);

  const options = choices.map(([value, label]) => ({value, label}));
  return (
    <FormRow>
      <Field
        name={objectTypeVersionName}
        required
        label={
          <FormattedMessage
            description="Objects API registration options 'objecttypeVersion' label"
            defaultMessage="Version"
          />
        }
        noManageChildProps
      >
        <ReactSelect
          name={objectTypeVersionName}
          required
          options={options}
          isLoading={loading}
          isDisabled={!objecttype}
        />
      </Field>
    </FormRow>
  );
};

export default ObjectTypeVersionSelect;
