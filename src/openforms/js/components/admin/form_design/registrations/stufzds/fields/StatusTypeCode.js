import {useField} from 'formik';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';

const StatusTypeCode = () => {
  const [fieldProps] = useField('zdsZaaktypeStatusCode');
  return (
    <FormRow>
      <Field
        name="zdsZaaktypeStatusCode"
        label={
          <FormattedMessage
            description="StUF-ZDS registration options 'zdsZaaktypeStatusCode' label"
            defaultMessage="Zds zaaktype status code"
          />
        }
        helpText={
          <FormattedMessage
            description="StUF-ZDS registration options 'zdsZaaktypeStatusCode' helpText"
            defaultMessage="Zaaktype status code for newly created zaken in StUF-ZDS"
          />
        }
      >
        <TextInput id="id_zdsZaaktypeStatusCode" {...fieldProps} />
      </Field>
    </FormRow>
  );
};

StatusTypeCode.propTypes = {};

export default StatusTypeCode;
