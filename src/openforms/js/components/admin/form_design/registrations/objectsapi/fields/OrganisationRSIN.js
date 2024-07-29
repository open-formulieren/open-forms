import {useField} from 'formik';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';

const OrganisationRSIN = () => {
  const [fieldProps] = useField('organisatieRsin');
  return (
    <FormRow>
      <Field
        name="organisatieRsin"
        label={
          <FormattedMessage
            description="Objects API registration options 'organisationRSIN' label"
            defaultMessage="Organisation RSIN"
          />
        }
        helpText={
          <FormattedMessage
            description="Objects API registration options 'organisationRSIN' helpText"
            defaultMessage="RSIN of the organization, which creates and owns the INFORMATIEOBJECTs."
          />
        }
      >
        <TextInput id="id_organisatieRsin" {...fieldProps} />
      </Field>
    </FormRow>
  );
};

OrganisationRSIN.propTypes = {};

export default OrganisationRSIN;
