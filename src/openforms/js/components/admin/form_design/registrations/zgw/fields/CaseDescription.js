import {useField} from 'formik';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';

const CaseDescription = () => {
  const [fieldProps] = useField('zaakOmschrijving');
  return (
    <FormRow>
      <Field
        name="zaakOmschrijving"
        label={
          <FormattedMessage
            description="ZGW APIs registration options 'zaakOmschrijving' label"
            defaultMessage="Case description"
          />
        }
        helpText={
          <FormattedMessage
            description="ZGW APIs registration options 'zaakOmschrijving' help text"
            defaultMessage={`Description of the case. You can use the expressions like '{{ form_name }}'
            or other variables here. The resolved string is limited to 80 chars. If empty, the form name is used.`}
          />
        }
      >
        <TextInput id="id_zaakOmschrijving" {...fieldProps} />
      </Field>
    </FormRow>
  );
};

CaseDescription.propTypes = {};

export default CaseDescription;
