import {useField, useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';
import {usePrevious, useUpdateEffect} from 'react-use';
import useAsync from 'react-use/esm/useAsync';

import {OBJECTS_API_OBJECTTYPES_ENDPOINT} from 'components/admin/form_design/constants';
import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';
import {get} from 'utils/fetch';

import {useSynchronizeSelect} from './hooks';

const getAvailableObjectTypes = async apiGroupID => {
  const response = await get(OBJECTS_API_OBJECTTYPES_ENDPOINT, {objects_api_group: apiGroupID});
  if (!response.ok) {
    throw new Error('Loading available object types failed');
  }
  return response.data;
};

const ObjectTypeSelect = ({
  name = 'objecttype',
  apiGroupFieldName = 'objectsApiGroup',
  onChangeCheck,
  versionFieldName = 'objecttypeVersion',
}) => {
  const [fieldProps, , fieldHelpers] = useField(name);
  const {
    values,
    setFieldValue,
    getFieldProps,
    initialValues: {objecttype: initialObjecttype},
  } = useFormikContext();
  const objectsApiGroup = getFieldProps(apiGroupFieldName).value ?? null;
  const {value} = fieldProps;
  const {setValue} = fieldHelpers;

  const {
    loading,
    value: objectTypes = [],
    error,
  } = useAsync(async () => {
    if (!objectsApiGroup) return [];
    return await getAvailableObjectTypes(objectsApiGroup);
  }, [objectsApiGroup]);
  if (error) throw error;

  const choices = loading
    ? []
    : objectTypes.map(({uuid, name, dataClassification}) => [
        uuid,
        `${name} (${dataClassification})`,
      ]);
  const options = choices.map(([value, label]) => ({value, label}));

  useSynchronizeSelect(name, loading, choices);

  const previousValue = usePrevious(value);

  // when a different object type is selected, ensure that the version is reset
  useUpdateEffect(() => {
    if (loading) return;
    if (value === initialObjecttype || value === previousValue) return;
    setFieldValue(versionFieldName, undefined); // clears the value
  }, [loading, value]);

  return (
    <FormRow>
      <Field
        name={name}
        required
        label={
          <FormattedMessage
            description="Objects API registration options 'Objecttype' label"
            defaultMessage="Objecttype"
          />
        }
        helpText={
          <FormattedMessage
            description="Objects API registration options 'Objecttype' helpText"
            defaultMessage="The registration result will be an object from the selected type."
          />
        }
        noManageChildProps
      >
        <ReactSelect
          name={name}
          options={options}
          isLoading={loading}
          isDisabled={!objectsApiGroup}
          required
          onChange={selectedOption => {
            const okToProceed = onChangeCheck === undefined || onChangeCheck();
            if (okToProceed) setValue(selectedOption.value);
          }}
        />
      </Field>
    </FormRow>
  );
};

ObjectTypeSelect.propTypes = {
  /**
   * Name to use for the form field, is passed down to Formik.
   */
  name: PropTypes.string,
  /**
   * Optional callback to confirm the change. Return `true` to continue with the change,
   * return `false` to abort it.
   */
  onChangeCheck: PropTypes.func,
  /**
   * Name of the field holding the selected API group. The value is used in the API
   * call to get the available object types.
   */
  apiGroupFieldName: PropTypes.string,
  /**
   * Name of the field to select the object type version. When the selected object type
   * changes, the version will be reset/unset.
   */
  versionFieldName: PropTypes.string,
};

export default ObjectTypeSelect;
