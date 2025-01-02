// TODO-4908: fix imports
import {Checkbox} from 'components/admin/forms/Inputs';
import Field from '../../../forms/Field';
import {FormattedMessage} from 'react-intl';
import FormRow from '../../../forms/FormRow';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {Checkbox} from 'components/admin/forms/Inputs';

const JSONVariableConfigurationEditor = ({variable}) => {
  const [fieldProps, , {setValue}] = useField('formVariables');

  const formVariables = fieldProps.value;
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
            const formVariablesNew = formVariables.slice();
            const index = formVariablesNew.indexOf(variable.key);
            if (event.target.checked) {
              if (index !== -1) {
                throw new Error(
                  'This form variable is already on the list of ' +
                    "form variables to include. This shouldn't happen."
                );
              }
              formVariablesNew.push(variable.key);
            } else {
              if (index === -1) {
                throw new Error(
                  'This form variable is not yet on the list of ' +
                    "form variables to include. This shouldn't happen."
                );
              }
              formVariablesNew.splice(index, 1);
            }
            setValue(formVariablesNew);
          }}
        />
      </Field>
    </FormRow>
  );
};

// TODO-4098: ???
JSONVariableConfigurationEditor.propTypes = {
  variable: PropTypes.shape({
    key: PropTypes.string.isRequired,
  }).isRequired,
};

export default JSONVariableConfigurationEditor;
