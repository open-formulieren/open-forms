import {useField} from 'formik';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';

/**
 * @todo - convert to omschrijving & use URL-based field as legacy/deprecated option
 */
const DocumentType = () => {
  const [fieldProps] = useField('informatieobjecttype');
  return (
    <FormRow>
      <Field
        name="informatieobjecttype"
        required
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

DocumentType.propTypes = {};

export default DocumentType;
