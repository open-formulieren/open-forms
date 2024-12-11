import {useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import useAsync from 'react-use/esm/useAsync';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';
import {get} from 'utils/fetch';

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
  name = 'objecttypeVersion',
  apiGroupFieldName = 'objectsApiGroup',
  objectTypeFieldName = 'objecttype',
  label,
}) => {
  const {getFieldProps} = useFormikContext();

  const {value: objectsApiGroup = null} = getFieldProps(apiGroupFieldName);
  const {value: objecttype = ''} = getFieldProps(objectTypeFieldName);

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

  const options = choices.map(([value, label]) => ({value, label}));
  return (
    <FormRow>
      <Field name={name} required label={label} noManageChildProps>
        <ReactSelect
          name={name}
          required
          options={options}
          isLoading={loading}
          isDisabled={!objecttype}
        />
      </Field>
    </FormRow>
  );
};

ObjectTypeVersionSelect.propTypes = {
  /**
   * Name to use for the form field, is passed down to Formik.
   */
  name: PropTypes.string,
  /**
   * Name of the field holding the selected API group. The value is used in the API
   * call to get the available object type versions.
   */
  apiGroupFieldName: PropTypes.string,
  /**
   * Name of the field to select the object type. The value is used in the API
   * call to get the available object type versions.
   */
  objectTypeFieldName: PropTypes.string,
  /**
   * The label that will be shown before the field
   */
  label: PropTypes.node.isRequired,
};

export default ObjectTypeVersionSelect;
