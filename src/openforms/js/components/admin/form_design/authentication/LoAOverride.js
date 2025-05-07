import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import Select from 'components/admin/forms/Select';

const LoAOverride = ({name, plugin, loa, onChange}) => {
  const {enum: enumValue, enumNames} = plugin.schema.properties.loa;
  const LoaChoices = enumValue.map((value, index) => [value, enumNames[index] || '------']);
  return (
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
        <Select value={loa} onChange={onChange} choices={LoaChoices} />
      </Field>
    </FormRow>
  );
};

LoAOverride.propTypes = {
  name: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  plugin: PropTypes.shape({
    id: PropTypes.string,
    label: PropTypes.string,
    providesAuth: PropTypes.string,
    schema: PropTypes.exact({
      type: PropTypes.oneOf(['object']).isRequired,
      properties: PropTypes.shape({
        loa: PropTypes.exact({
          type: PropTypes.oneOf(['string']).isRequired,
          title: PropTypes.string.isRequired,
          description: PropTypes.string.isRequired,
          enum: PropTypes.arrayOf(PropTypes.string).isRequired,
          enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
        }).isRequired,
      }),
    }),
  }).isRequired,
  loa: PropTypes.string,
};

export default LoAOverride;
