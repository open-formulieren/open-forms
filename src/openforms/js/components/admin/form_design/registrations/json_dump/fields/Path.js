import {useField} from 'formik';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';

const Path = () => {
  const [fieldProps] = useField('path');
  return (
    <FormRow>
      <Field
        name="path"
        label={
          <FormattedMessage
            description="JSON registration options 'path' label"
            defaultMessage="Path"
          />
        }
        helpText={
          <FormattedMessage
            description="JSON registration options 'path' helpText"
            defaultMessage="Path relative to the Service API root."
          />
        }
      >
        <TextInput {...fieldProps} />
      </Field>
    </FormRow>
  );
};

export default Path;
