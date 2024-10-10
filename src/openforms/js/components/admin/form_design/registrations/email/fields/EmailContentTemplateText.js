import {useField} from 'formik';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {TextArea} from 'components/admin/forms/Inputs';

const EmailContentTemplateText = () => {
  const [fieldProps] = useField('emailContentTemplateText');
  return (
    <FormRow>
      <Field
        name="emailContentTemplateText"
        label={
          <FormattedMessage
            description="Email registration options 'emailContentTemplateText' label"
            defaultMessage="Email content template text"
          />
        }
        helpText={
          <FormattedMessage
            description="Email registration options 'emailContentTemplateText' helpText"
            defaultMessage="Content of the registration email message (as text)."
          />
        }
      >
        <TextArea
          id="id_emailContentTemplateText"
          rows={5}
          cols={85}
          {...fieldProps}
          style={{fontFamily: 'monospace'}}
        />
      </Field>
    </FormRow>
  );
};

EmailContentTemplateText.propTypes = {};

export default EmailContentTemplateText;
