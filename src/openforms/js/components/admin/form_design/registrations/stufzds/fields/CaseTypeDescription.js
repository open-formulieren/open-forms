import {useField} from 'formik';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';

const CaseTypeDescription = () => {
  const [fieldProps] = useField('zdsZaaktypeOmschrijving');
  return (
    <FormRow>
      <Field
        name="zdsZaaktypeOmschrijving"
        label={
          <FormattedMessage
            description="StUF-ZDS registration options 'zdsZaaktypeOmschrijving' label"
            defaultMessage="Zds zaaktype omschrijving"
          />
        }
        helpText={
          <FormattedMessage
            description="StUF-ZDS registration options 'zdsZaaktypeOmschrijving' helpText"
            defaultMessage="Zaaktype description for newly created Zaken in StUF-ZDS"
          />
        }
      >
        <TextInput id="id_zdsZaaktypeOmschrijving" {...fieldProps} />
      </Field>
    </FormRow>
  );
};

CaseTypeDescription.propTypes = {};

export default CaseTypeDescription;
