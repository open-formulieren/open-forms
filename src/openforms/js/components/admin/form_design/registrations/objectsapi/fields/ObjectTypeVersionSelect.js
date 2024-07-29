import {useField, useFormikContext} from 'formik';
import {FormattedMessage} from 'react-intl';
import useAsync from 'react-use/esm/useAsync';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import Select, {LOADING_OPTION} from 'components/admin/forms/Select';
import {get} from 'utils/fetch';

import {useSynchronizeSelect} from './hooks';

const getObjecttypeVersionsEndpoint = uuid => {
  const bits = [
    '/api/v2/registration/plugins/objects-api/object-types',
    encodeURIComponent(uuid),
    'versions',
  ];
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

const ObjectTypeVersionSelect = () => {
  const [fieldProps, , {setValue}] = useField('objecttypeVersion');
  const {
    values: {objectsApiGroup = null, objecttype = ''},
  } = useFormikContext();

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
    ? LOADING_OPTION
    : versions.map(version => [version.version, `${version.version} (${version.status})`]);

  useSynchronizeSelect('objecttypeVersion', loading, choices);

  return (
    <FormRow>
      <Field
        name="objecttypeVersion"
        required
        label={
          <FormattedMessage
            description="Objects API registration options 'objecttypeVersion' label"
            defaultMessage="Version"
          />
        }
      >
        <Select
          required
          disabled={!objecttype}
          choices={choices}
          id="id_objecttypeVersion"
          {...fieldProps}
          onChange={event => {
            // overridden to handle the proper data type, since very <option value>
            // turns into a string in HTML
            const newVersion = parseInt(event.currentTarget.value, 10);
            setValue(newVersion);
          }}
        />
      </Field>
    </FormRow>
  );
};

export default ObjectTypeVersionSelect;
