import {useField} from 'formik';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';

const CaseTypeCode = () => {
  const [fieldProps] = useField('zdsZaaktypeCode');
  return (
    <FormRow>
      <Field
        name="zdsZaaktypeCode"
        label={
          <FormattedMessage
            description="StUF-ZDS registration options 'zdsZaaktypeCode' label"
            defaultMessage="Zds zaaktype code"
          />
        }
        helpText={
          <FormattedMessage
            description="StUF-ZDS registration options 'zdsZaaktypeCode' helpText"
            defaultMessage="Zaaktype code for newly created Zaken in StUF-ZDS"
          />
        }
      >
        <TextInput id="id_zdsZaaktypeCode" {...fieldProps} />
      </Field>
    </FormRow>
  );
};

CaseTypeCode.propTypes = {};

export default CaseTypeCode;
