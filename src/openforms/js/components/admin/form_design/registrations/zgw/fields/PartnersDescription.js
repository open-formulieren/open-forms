import {useField} from 'formik';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';

const PartnersDescription = () => {
  const [fieldProps] = useField('partnersDescription');
  return (
    <FormRow>
      <Field
        name="partnersDescription"
        label={
          <FormattedMessage
            description="ZGW APIs registration options 'partnersDescription' label"
            defaultMessage="Partners description"
          />
        }
        helpText={
          <FormattedMessage
            description="ZGW APIs registration options 'partnersDescription' help text"
            defaultMessage="The description that will be used in partners registration."
          />
        }
      >
        <TextInput id="id_partnersDescription" {...fieldProps} />
      </Field>
    </FormRow>
  );
};

PartnersDescription.propTypes = {};

export default PartnersDescription;
