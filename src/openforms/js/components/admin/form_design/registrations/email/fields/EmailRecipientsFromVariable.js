import {useField} from 'formik';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import VariableSelection from 'components/admin/forms/VariableSelection';

const EmailRecipientsFromVariable = () => {
  const [fieldProps, , fieldHelpers] = useField('toEmailsFromVariable');
  const {setValue} = fieldHelpers;
  return (
    <FormRow>
      <Field
        name="toEmailsFromVariable"
        label={
          <FormattedMessage
            description="Email registration options 'toEmailsFromVariable' label"
            defaultMessage="Using a variable to decide to which email address the
            submission details will be sent"
          />
        }
        helpText={
          <FormattedMessage
            description="Email registration options 'toEmailsFromVariable' helpText"
            defaultMessage="The email address described in this variable will be used
            for the mailing. If a variable is selected, the general registration
            addresses will be used as fallback option. "
          />
        }
      >
        <VariableSelection
          name="toEmailsFromVariable"
          value={fieldProps.value}
          onChange={event => {
            setValue(event.target.value);
          }}
        />
      </Field>
    </FormRow>
  );
};

EmailRecipientsFromVariable.propTypes = {};

export default EmailRecipientsFromVariable;
