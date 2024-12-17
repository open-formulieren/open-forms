import {useField} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';

const FormVariablesSelect = ({options}) => {
  const [fieldProps, , fieldHelpers] = useField('formVariables');
  const {setValue} = fieldHelpers;

  // TODO-4098: what does this do?
  const values = [];
  if (fieldProps.value && fieldProps.value.length) {
    fieldProps.value.forEach(item => {
      const selectedOption = options.find(option => option.value === item);
      if (selectedOption) {
        values.push(selectedOption);
      }
    });
  }

  return (
    <FormRow>
      <Field
        name="formVariables"
        label={
          <FormattedMessage
            description="JSON registration options 'formVariables' label"
            defaultMessage="Form variables"
          />
        }
      >
        <ReactSelect
          name="formVariables"
          options={options}
          isMulti
          required
          value={values}
          // TODO-4098: what does this do?
          onChange={newValue => {
            setValue(newValue.map(item => item.value));
          }}
        />
      </Field>
    </FormRow>
  );
};

FormVariablesSelect.propTypes = {
  options: PropTypes.arrayOf(
    PropTypes.shape({
      value: PropTypes.string.isRequired,
      label: PropTypes.node.isRequired,
    })
  ).isRequired,
};

export default FormVariablesSelect;
