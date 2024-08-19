import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';

const ConfidentialityLevel = ({options}) => (
  <FormRow>
    <Field
      name="zaakVertrouwelijkheidaanduiding"
      label={
        <FormattedMessage
          description="ZGW APIs registration options 'zaakVertrouwelijkheidaanduiding' label"
          defaultMessage="Confidentiality"
        />
      }
      helpText={
        <FormattedMessage
          description="ZGW APIs registration options 'zaakVertrouwelijkheidaanduiding' help text"
          defaultMessage={`Indication of the level to which extent the case is meant
          to be public. The value selected here will override the default configured on the case type.`}
        />
      }
    >
      <ReactSelect
        name="zaakVertrouwelijkheidaanduiding"
        options={options.map(([value, label]) => ({
          value,
          label,
        }))}
        isClearable
      />
    </Field>
  </FormRow>
);

ConfidentialityLevel.propTypes = {
  options: PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.string)),
};

export default ConfidentialityLevel;
