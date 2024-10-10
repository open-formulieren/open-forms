import {useField} from 'formik';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';

const EmailSubject = () => {
  const [fieldProps] = useField('emailSubject');
  return (
    <FormRow>
      <Field
        name="emailSubject"
        label={
          <FormattedMessage
            description="Email registration options 'emailSubject' label"
            defaultMessage="Email subject"
          />
        }
        helpText={
          <FormattedMessage
            description="Email registration options 'emailSubject' helpText"
            defaultMessage="Subject of the email sent to the registration backend. You can use the expressions '{{ form_name }}' and '{{ public_reference }}' to include the form name and the reference number to the submission in the subject."
          />
        }
      >
        <TextInput id="id_emailSubject" {...fieldProps} />
      </Field>
    </FormRow>
  );
};

EmailSubject.propTypes = {};

export default EmailSubject;
