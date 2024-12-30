import {useField} from 'formik';
import PropTypes from 'prop-types';
import React from 'react';

import {FormattedMessage} from 'react-intl';
import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {Checkbox} from 'components/admin/forms/Inputs';


const JSONVariableConfigurationEditor = ({variable}) => {
  const [fieldProps, , fieldHelpers] = useField('formVariables');
  const {setValue} = fieldHelpers;

  const formVariables = fieldProps.value
  const isIncluded = formVariables.includes(variable.key);

  return (
    <FormRow>
      <Field name="includeVariable">
        <Checkbox
          name="includeVariableCheckbox"
          label={
            <FormattedMessage
              description="'Include variable' checkbox label"
              defaultMessage="Include variable"
            />
          }
          helpText={
            <FormattedMessage
              description="'Include variable' checkbox help text"
              defaultMessage="Whether to include this variable in the data to be sent."
            />
          }
          checked={isIncluded}
          onChange={event => {
            const index = formVariables.indexOf(variable.key);
            if (event.target.checked) {
              if (index !== -1) {throw new Error(
                "This form variable is already on the list of " +
                "form variables to include. This shouldn't happen."
              );}
              formVariables.push(variable.key);
            } else {
              if (index === -1) {throw new Error(
                "This form variable is not yet on the list of " +
                "form variables to include. This shouldn't happen."
              );}
              formVariables.splice(index, 1);
            }
            setValue(formVariables);
          }}
        />
      </Field>
    </FormRow>
  )
}

JSONVariableConfigurationEditor.propTypes = {
  variable: PropTypes.shape({
    key: PropTypes.string.isRequired,
  }).isRequired,
};


export default JSONVariableConfigurationEditor
