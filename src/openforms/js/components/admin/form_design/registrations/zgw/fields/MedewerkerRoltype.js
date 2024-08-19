import {useField} from 'formik';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';

const MedewerkerRoltype = () => {
  const [fieldProps] = useField('medewerkerRoltype');
  return (
    <FormRow>
      <Field
        name="medewerkerRoltype"
        label={
          <FormattedMessage
            description="Objects API registration options 'medewerkerRoltype' label"
            defaultMessage="Medewerker roltype"
          />
        }
        helpText={
          <FormattedMessage
            description="Objects API registration options 'medewerkerRoltype' help text"
            defaultMessage={`Description (omschrijving) of the ROLTYPE to use for
            employees filling in a form for a citizen/company.`}
          />
        }
      >
        <TextInput id="id_medewerkerRoltype" {...fieldProps} />
      </Field>
    </FormRow>
  );
};

MedewerkerRoltype.propTypes = {};

export default MedewerkerRoltype;
