import {useField} from 'formik';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import VariableSelection from 'components/admin/forms/VariableSelection';

const EmailRecipientsFromVariable = () => {
  const [fieldProps, , {setValue}] = useField('toEmailsFromVariable');
  return (
    <FormRow>
      <Field
        name="toEmailsFromVariable"
        label={
          <FormattedMessage
            description="Email registration options 'toEmailsFromVariable' label"
            defaultMessage="Variable containing email addresses"
          />
        }
        helpText={
          <FormattedMessage
            description="Email registration options 'toEmailsFromVariable' helpText"
            defaultMessage={`If specified, the recipient email addresses will be taken
            from the selected variable. You must still specify 'regular' email addresses
            as a fallback, in case something is wrong with the variable.
            `}
          />
        }
      >
        <VariableSelection
          {...fieldProps}
          isClearable
          onChange={event => {
            const newValue = event.target.value;
            setValue(newValue == null ? '' : newValue);
          }}
          filter={variable => ['string', 'array'].includes(variable.dataType)}
        />
      </Field>
    </FormRow>
  );
};

EmailRecipientsFromVariable.propTypes = {};

export default EmailRecipientsFromVariable;
