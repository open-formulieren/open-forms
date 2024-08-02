import {getReactSelectStyles} from '@open-formulieren/formio-builder/esm/components/formio/select';
import {useField, useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';
import ReactSelect from 'react-select';
import {usePrevious, useUpdateEffect} from 'react-use';
import useAsync from 'react-use/esm/useAsync';

import {REGISTRATION_OBJECTTYPES_ENDPOINT} from 'components/admin/form_design/constants';
import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {get} from 'utils/fetch';

import {useSynchronizeSelect} from './hooks';

const getAvailableObjectTypes = async apiGroupID => {
  const response = await get(REGISTRATION_OBJECTTYPES_ENDPOINT, {objects_api_group: apiGroupID});
  if (!response.ok) {
    throw new Error('Loading available object types failed');
  }
  return response.data;
};

const initialStyles = getReactSelectStyles();
const styles = {
  ...initialStyles,
  control: (...args) => ({
    ...initialStyles.control(...args),
    minHeight: '1.875rem',
    height: '1.875rem',
  }),
  valueContainer: (...args) => ({
    ...initialStyles.valueContainer(...args),
    height: 'calc(1.875rem - 2px)',
    padding: '0 6px',
  }),
  input: (...args) => ({
    ...initialStyles.input(...args),
    margin: '0px',
  }),
  indicatorsContainer: baseStyles => ({
    ...baseStyles,
    height: 'calc(1.875rem - 2px)',
    padding: '0 2px',
  }),
  dropdownIndicator: (...args) => ({
    ...initialStyles.dropdownIndicator(...args),
    padding: '5px 2px',
  }),
};

const ObjectTypeSelect = ({onChangeCheck}) => {
  const [fieldProps, , fieldHelpers] = useField('objecttype');
  const {
    values: {objectsApiGroup = null},
    setFieldValue,
    initialValues: {objecttype: initialObjecttype},
  } = useFormikContext();
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

  useSynchronizeSelect('objecttype', loading, choices);

  const previousValue = usePrevious(value);

  // when a different object type is selected, ensure that the version is reset
  useUpdateEffect(() => {
    if (loading) return;
    if (value === initialObjecttype || value === previousValue) return;
    setFieldValue('objecttypeVersion', undefined); // clears the value
  }, [loading, value]);

  return (
    <FormRow>
      <Field
        name="objecttype"
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
        {/*https://stackoverflow.com/questions/54218351/changing-height-of-react-select-component*/}
        <ReactSelect
          inputId="id_objecttype"
          className="admin-react-select"
          styles={styles}
          menuPlacement="auto"
          options={options}
          isLoading={loading}
          isDisabled={!objectsApiGroup}
          required
          {...fieldProps}
          value={options.find(opt => opt.value === value)}
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
  onChangeCheck: PropTypes.func,
};

export default ObjectTypeSelect;
