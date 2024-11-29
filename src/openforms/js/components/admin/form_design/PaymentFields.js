import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import Select from 'components/admin/forms/Select';

import {PAYMENT_OPTIONS_FORMS} from './payments';

const PaymentFields = ({backends = [], selectedBackend = '', backendOptions = {}, onChange}) => {
  const backendChoices = backends.map(backend => [backend.id, backend.label]);
  const backend = backends.find(backend => backend.id === selectedBackend);
  const hasOptionsForm = Boolean(backend && Object.keys(backend.schema.properties).length);

  const OptionsFormComponent = backend ? PAYMENT_OPTIONS_FORMS[backend.id] : null;

  return (
    <Fieldset
      title={
        <FormattedMessage
          description="Payment provider fieldset title"
          defaultMessage="Payment provider"
        />
      }
    >
      <FormRow>
        <Field
          name="form.paymentBackend"
          label={
            <FormattedMessage
              description="Payment backend label"
              defaultMessage="Select payment backend"
            />
          }
        >
          <Select
            choices={backendChoices}
            value={selectedBackend}
            onChange={event => {
              onChange(event);
              // Clear options when changing backend
              onChange({target: {name: 'form.paymentBackendOptions', value: {}}});
            }}
            allowBlank
          />
        </Field>
      </FormRow>
      {hasOptionsForm && (
        <FormRow>
          <OptionsFormComponent
            schema={backend.schema}
            formData={backendOptions}
            onSubmit={values =>
              onChange({target: {name: 'form.paymentBackendOptions', value: values}})
            }
          />
        </FormRow>
      )}
    </Fieldset>
  );
};

PaymentFields.propTypes = {
  backends: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string.isRequired,
      label: PropTypes.string.isRequired,
      schema: PropTypes.shape({
        type: PropTypes.oneOf(['object']), // it's the JSON schema root, it has to be
        properties: PropTypes.object,
        required: PropTypes.arrayOf(PropTypes.string),
      }),
    })
  ),
  selectedBackend: PropTypes.string,
  backendOptions: PropTypes.object,
  onChange: PropTypes.func.isRequired,
};

export default PaymentFields;
