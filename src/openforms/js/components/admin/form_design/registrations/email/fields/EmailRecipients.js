import {useField} from 'formik';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import ArrayInput from 'components/admin/forms/ArrayInput';
import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';

const EmailRecipients = () => {
  const [fieldProps, , fieldHelpers] = useField('toEmails');
  const {setValue} = fieldHelpers;
  return (
    <FormRow>
      <Field
        name="toEmails"
        label={
          <FormattedMessage
            description="Email registration options 'toEmails' label"
            defaultMessage="The email addresses to which the submission details will be sent"
          />
        }
        required
      >
        <ArrayInput
          name="toEmails"
          values={fieldProps.value}
          onChange={value => {
            setValue(value);
          }}
          inputType="text"
        />
      </Field>
    </FormRow>
  );
};

EmailRecipients.propTypes = {};

export default EmailRecipients;
