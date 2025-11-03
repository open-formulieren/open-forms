import {useField} from 'formik';
import {FormattedMessage} from 'react-intl';

import FormRow from 'components/admin/forms/FormRow';
import {Checkbox} from 'components/admin/forms/Inputs';

const PhoneNumberField = () => {
  const [fieldProps] = useField({name: 'options.phoneNumber', type: 'checkbox'});
  return (
    <FormRow>
      <Checkbox
        name="options.phoneNumber"
        label={
          <FormattedMessage
            description="Klantinteracties options: 'PhoneNumber' label"
            defaultMessage="Include phone number"
          />
        }
        helpText={
          <FormattedMessage
            description="Klantinteracties options: 'PhoneNumber' helpText"
            defaultMessage={`If enabled, phone numbers are included in the prefill`}
          />
        }
        {...fieldProps({name: 'options.phoneNumber', type: 'checkbox'})}
      />
    </FormRow>
  );
};

PhoneNumberField.propTypes = {};
export default PhoneNumberField;
