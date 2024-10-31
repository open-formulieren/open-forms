import {useField} from 'formik';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';

const DocumentTypeDescription = () => {
  const [fieldProps] = useField('zdsDocumenttypeOmschrijvingInzending');
  return (
    <FormRow>
      <Field
        name="zdsDocumenttypeOmschrijvingInzending"
        label={
          <FormattedMessage
            description="StUF-ZDS registration options 'zdsDocumenttypeOmschrijvingInzending' label"
            defaultMessage="Zds documenttype omschrijving inzending"
          />
        }
        helpText={
          <FormattedMessage
            description="StUF-ZDS registration options 'zdsDocumenttypeOmschrijvingInzending' helpText"
            defaultMessage="Documenttype description for newly created zaken in StUF-ZDS"
          />
        }
      >
        <TextInput id="id_zdsDocumenttypeOmschrijvingInzending" {...fieldProps} />
      </Field>
    </FormRow>
  );
};

DocumentTypeDescription.propTypes = {};

export default DocumentTypeDescription;
