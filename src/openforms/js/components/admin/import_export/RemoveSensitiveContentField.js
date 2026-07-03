import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import {Checkbox} from 'components/admin/forms/Inputs';

const RemoveSensitiveContentField = ({value, onChange}) => (
  <Checkbox
    name="removeSensitiveContent"
    label={
      <FormattedMessage
        defaultMessage="Anonymize form configuration"
        description="Form export options 'removeSensitiveContent' field label"
      />
    }
    helpText={
      <FormattedMessage
        defaultMessage="Whether sensative form configuration should be anonymized during exporting."
        description="Form export options 'removeSensitiveContent' help text"
      />
    }
    checked={value}
    onChange={() => onChange({target: {name: 'removeSensitiveContent', value: !value}})}
  />
);

RemoveSensitiveContentField.prototype = {
  value: PropTypes.bool,
  onChange: PropTypes.func,
};

export default RemoveSensitiveContentField;
