import {useField} from 'formik';
import {FormattedMessage} from 'react-intl';

import FormRow from 'components/admin/forms/FormRow';
import {Checkbox} from 'components/admin/forms/Inputs';

const EmailField = () => {
  const [fieldProps] = useField({name: 'options.email', type: 'checkbox'});
  return (
    <FormRow>
      <Checkbox
        name="options.email"
        label={
          <FormattedMessage
            description="Klantinteracties options: 'Email' label"
            defaultMessage="Include email"
          />
        }
        helpText={
          <FormattedMessage
            description="Klantinteracties options: 'Email' helpText"
            defaultMessage={`If enabled, emails are included in the prefill`}
          />
        }
        {...fieldProps}
      />
    </FormRow>
  );
};

EmailField.propTypes = {};
export default EmailField;
