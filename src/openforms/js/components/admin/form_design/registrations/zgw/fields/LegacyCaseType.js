import {useField, useFormikContext} from 'formik';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';

/**
 * @deprecated
 */
const CaseType = () => {
  const [fieldProps] = useField('zaaktype');
  const {
    values: {caseTypeIdentification},
  } = useFormikContext();
  return (
    <FormRow>
      <Field
        name="zaaktype"
        required={!caseTypeIdentification}
        label={
          <FormattedMessage
            description="ZGW APIs registration options 'CaseType' label"
            defaultMessage="Case type"
          />
        }
        helpText={
          <FormattedMessage
            description="ZGW APIs registration options 'CaseType' help text"
            defaultMessage="Case type API resource URL in the Catalogi API."
          />
        }
      >
        <TextInput id="id_zaaktype" required={!caseTypeIdentification} {...fieldProps} />
      </Field>
    </FormRow>
  );
};

CaseType.propTypes = {};

export default CaseType;
