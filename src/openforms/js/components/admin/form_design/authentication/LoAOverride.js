import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import ReactSelect from 'components/admin/forms/ReactSelect';

const LoAOverride = ({name, options}) => (
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
      <ReactSelect name={name} options={options} />
    </Field>
  </FormRow>
);

LoAOverride.propTypes = {
  name: PropTypes.string.isRequired,
  options: PropTypes.arrayOf(
    PropTypes.shape({
      value: PropTypes.string.isRequired,
      label: PropTypes.string.isRequired,
    })
  ).isRequired,
};

export default LoAOverride;
