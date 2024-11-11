import {useField, useFormikContext} from 'formik';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';

/**
 * @deprecated
 */
const LegacyDocumentType = () => {
  const [fieldProps] = useField('informatieobjecttype');
  const {
    values: {documentTypeDescription},
  } = useFormikContext();
  return (
    <FormRow>
      <Field
        name="informatieobjecttype"
        required={!documentTypeDescription}
        label={
          <FormattedMessage
            description="ZGW APIs registration options 'DocumentType' label"
            defaultMessage="Document type"
          />
        }
        helpText={
          <FormattedMessage
            description="ZGW APIs registration options 'DocumentType' help text"
            defaultMessage="Document type API resource URL in the Catalogi API."
          />
        }
      >
        <TextInput id="id_informatieobjecttype" required {...fieldProps} />
      </Field>
    </FormRow>
  );
};

LegacyDocumentType.propTypes = {};

export default LegacyDocumentType;
