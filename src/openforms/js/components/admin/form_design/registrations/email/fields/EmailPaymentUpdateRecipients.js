import {useField} from 'formik';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import ArrayInput from 'components/admin/forms/ArrayInput';
import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';

const EmailPaymentUpdateRecipients = () => {
  const [fieldProps, , fieldHelpers] = useField('paymentEmails');
  const {setValue} = fieldHelpers;
  return (
    <FormRow>
      <Field
        name="paymentEmails"
        label={
          <FormattedMessage
            description="Email registration options 'paymentEmails' label"
            defaultMessage="The email addresses to which the payment status update will be sent (defaults to general registration addresses)"
          />
        }
      >
        <ArrayInput
          name="paymentEmails"
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

EmailPaymentUpdateRecipients.propTypes = {};

export default EmailPaymentUpdateRecipients;
