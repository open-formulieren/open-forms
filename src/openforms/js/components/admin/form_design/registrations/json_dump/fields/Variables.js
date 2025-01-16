import {useField} from 'formik';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import VariableSelection from 'components/admin/forms/VariableSelection';

const Variables = () => {
  const [fieldProps] = useField('variables');

  return (
    <FormRow>
      <Field
        name="variables"
        label={
          <FormattedMessage
            description="JSON registration options 'variables' label"
            defaultMessage="Variables"
          />
        }
        helpText={
          <FormattedMessage
            description="JSON registration options 'variables' helpText"
            defaultMessage="Which variables to include in the data to be sent"
          />
        }
        required
        noManageChildProps
      >
        <VariableSelection
          {...fieldProps}
          isMulti
          required
          closeMenuOnSelect={false}
          includeStaticVariables={true}
        />
      </Field>
    </FormRow>
  );
};

export default Variables;
