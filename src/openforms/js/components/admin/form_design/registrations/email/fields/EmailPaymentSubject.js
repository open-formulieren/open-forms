import {useField} from 'formik';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';

const EmailPaymentSubject = () => {
  const [fieldProps] = useField('emailPaymentSubject');
  return (
    <FormRow>
      <Field
        name="emailPaymentSubject"
        label={
          <FormattedMessage
            description="Email registration options 'emailPaymentSubject' label"
            defaultMessage="Email payment subject"
          />
        }
        helpText={
          <FormattedMessage
            description="Email registration options 'emailPaymentSubject' helpText"
            defaultMessage="Subject of the email sent to the registration backend to notify a change in the payment status."
          />
        }
      >
        <TextInput id="id_emailPaymentSubject" {...fieldProps} />
      </Field>
    </FormRow>
  );
};

EmailPaymentSubject.propTypes = {};

export default EmailPaymentSubject;
