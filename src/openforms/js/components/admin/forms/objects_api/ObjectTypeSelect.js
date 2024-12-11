import {useField, useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {flushSync} from 'react-dom';
import useAsync from 'react-use/esm/useAsync';

import {OBJECTS_API_OBJECTTYPES_ENDPOINT} from 'components/admin/form_design/constants';
import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';
import {get} from 'utils/fetch';

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
  label,
  helpText,
  onObjectTypeChange = undefined,
}) => {
  const [{value}, , fieldHelpers] = useField(name);
  const {values, getFieldProps, setValues} = useFormikContext();
  const objectsApiGroup = getFieldProps(apiGroupFieldName).value ?? null;
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

  return (
    <FormRow>
      <Field name={name} required label={label} helpText={helpText} noManageChildProps>
        <ReactSelect
          name={name}
          options={options}
          isLoading={loading}
          isDisabled={!objectsApiGroup}
          required
          onChange={async selectedOption => {
            const hasChanged = selectedOption.value !== value;
            // don't trigger Formik state changes and dependent effects if the user
            // selects the same value that's already selected.
            if (!hasChanged) return;

            const okToProceed = onChangeCheck === undefined || (await onChangeCheck());
            if (okToProceed) {
              // flush sync needed to ensure that onApiGroupChange gets the updated
              // state
              flushSync(() => {
                setValue(selectedOption.value);
              });
              if (onObjectTypeChange) setValues(onObjectTypeChange);
            }
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
   * return `false` to abort it. The callback function must be async.
   */
  onChangeCheck: PropTypes.func,
  /**
   * The label that will be shown before the field
   */
  label: PropTypes.node.isRequired,
  /**
   * The help text to explain what the field is for
   */
  helpText: PropTypes.node.isRequired,
  /**
   * Callback to invoke when the object type value changes, e.g. to reset any dependent
   * fields.
   *
   * The function will be called with Formik's previous values so you can construct a new
   * values state from that.
   *
   * **NOTE**
   *
   * It's best to define this callback at the module level, or make use of `useCallback`
   * to obtain a stable reference to the callback, otherwise the callback will likely
   * fire unexpectedly during re-renders.
   */
  onObjectTypeChange: PropTypes.func,

  /**
   * Name of the field holding the selected API group. The value is used in the API
   * call to get the available object types.
   */
  apiGroupFieldName: PropTypes.string,
};

export default ObjectTypeSelect;
