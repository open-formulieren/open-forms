import {useField} from 'formik';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';

const StatusTypeDescription = () => {
  const [fieldProps] = useField('zdsZaaktypeStatusOmschrijving');
  return (
    <FormRow>
      <Field
        name="zdsZaaktypeStatusOmschrijving"
        label={
          <FormattedMessage
            description="StUF-ZDS registration options 'zdsZaaktypeStatusOmschrijving' label"
            defaultMessage="Zds zaaktype status omschrijving"
          />
        }
        helpText={
          <FormattedMessage
            description="StUF-ZDS registration options 'zdsZaaktypeStatusOmschrijving' helpText"
            defaultMessage="Zaaktype status omschrijving for newly created zaken in StUF-ZDS"
          />
        }
      >
        <TextInput id="id_zdsZaaktypeStatusOmschrijving" {...fieldProps} />
      </Field>
    </FormRow>
  );
};

StatusTypeDescription.propTypes = {};

export default StatusTypeDescription;
