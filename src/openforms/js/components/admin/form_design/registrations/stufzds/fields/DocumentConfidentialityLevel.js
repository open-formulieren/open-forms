import {useField} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';

const DocumentConfidentialityLevel = ({options}) => {
  const [fieldProps, , fieldHelpers] = useField('zdsZaakdocVertrouwelijkheid');
  const {setValue} = fieldHelpers;

  return (
    <FormRow>
      <Field
        name="zdsZaakdocVertrouwelijkheid"
        label={
          <FormattedMessage
            description="StUF-ZDS registration options 'zdsZaakdocVertrouwelijkheid' label"
            defaultMessage="Document confidentiality level"
          />
        }
        helpText={
          <FormattedMessage
            description="StUF-ZDS registration options 'zdsZaakdocVertrouwelijkheid' helpText"
            defaultMessage={`Indication of the level to which extend the dossier of the ZAAK is meant
          to be public. This is set on the documents created for the ZAAK.`}
          />
        }
      >
        <ReactSelect
          name="zdsZaakdocVertrouwelijkheid"
          options={options}
          required
          value={options.find(option => option.value === fieldProps.value)}
          onChange={newValue => {
            setValue(newValue.value);
          }}
        />
      </Field>
    </FormRow>
  );
};

DocumentConfidentialityLevel.propTypes = {
  options: PropTypes.arrayOf(
    PropTypes.shape({
      value: PropTypes.string.isRequired,
      label: PropTypes.node.isRequired,
    })
  ).isRequired,
};

export default DocumentConfidentialityLevel;
