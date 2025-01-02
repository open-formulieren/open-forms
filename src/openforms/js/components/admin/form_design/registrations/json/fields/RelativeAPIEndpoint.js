import {useField} from 'formik';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';

const RelativeAPIEndpoint = () => {
  const [fieldProps] = useField('relativeApiEndpoint');
  return (
    <FormRow>
      <Field
        name="relativeApiEndpoint"
        label={
          <FormattedMessage
            description="JSON registration options 'relativeApiEndpoint' label"
            defaultMessage="Relative API Endpoint"
          />
        }
        helpText={
          <FormattedMessage
            description="JSON registration options 'relativeApiEndpoint' helpText"
            defaultMessage="Relative endpoint to send the data to (will be added to the root endpoint of the service)."
          />
        }
      >
        <TextInput id="id_relativeApiEndpoint" {...fieldProps} />
      </Field>
    </FormRow>
  );
};

export default RelativeAPIEndpoint;
