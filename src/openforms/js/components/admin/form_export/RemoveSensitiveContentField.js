import {useField} from 'formik';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import {Checkbox} from 'components/admin/forms/Inputs';

const RemoveSensitiveContentField = () => {
  const [fieldProps, , fieldHelpers] = useField('removeSensitiveContent');
  const {value} = fieldProps;
  const {setValue} = fieldHelpers;

  return (
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
      onChange={() => setValue(!value)}
    />
  );
};

export default RemoveSensitiveContentField;
