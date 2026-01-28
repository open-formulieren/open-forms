import {useField} from 'formik';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import FormRow from 'components/admin/forms/FormRow';
import {Checkbox} from 'components/admin/forms/Inputs';

const VisibleField = () => {
  const [fieldProps] = useField({name: 'visible', type: 'checkbox'});
  return (
    <FormRow>
      <Checkbox
        label={<FormattedMessage description="Visible field label" defaultMessage="Visible" />}
        helpText={
          <FormattedMessage
            description="Visible field text"
            defaultMessage="Whether to always show this plugin when the form starts."
          />
        }
        {...fieldProps}
      />
    </FormRow>
  );
};

VisibleField.propTypes = {};

export default VisibleField;
