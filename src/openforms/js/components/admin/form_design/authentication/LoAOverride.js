import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import Select from 'components/admin/forms/Select';

const LoAOverride = ({name, plugin, loa, onChange}) => (
  <FormRow>
    <Field
      name={name}
      label={
        <FormattedMessage
          description="Minimal levels of assurance label"
          defaultMessage="Minimal levels of assurance"
        />
      }
      helpText={
        <FormattedMessage
          defaultMessage="Override the minimum Level of Assurance. This is not supported by all authentication plugins."
          description="Minimal LoA override help text"
        />
      }
    >
      <Select
        value={loa}
        onChange={onChange}
        allowBlank={true}
        choices={plugin.assuranceLevels.map(loa => [loa.value, loa.label])}
      />
    </Field>
  </FormRow>
);

export default LoAOverride;

LoAOverride.propTypes = {
  name: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  plugin: PropTypes.shape({
    id: PropTypes.string,
    label: PropTypes.string,
    providesAuth: PropTypes.string,
    assuranceLevels: PropTypes.arrayOf(
      PropTypes.shape({
        label: PropTypes.string.isRequired,
        value: PropTypes.string.isRequired,
      })
    ),
    schema: PropTypes.object,
  }).isRequired,
  loa: PropTypes.string,
};
