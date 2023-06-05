import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import FormRjsfWrapper from 'components/admin/RJSFWrapper';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import Select from 'components/admin/forms/Select';

import {BACKEND_OPTIONS_FORMS} from './registrations';

const BackendType = PropTypes.shape({
  id: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  schema: PropTypes.shape({
    type: PropTypes.oneOf(['object']), // it's the JSON schema root, it has to be
    properties: PropTypes.object,
    required: PropTypes.arrayOf(PropTypes.string),
  }),
});

const BackendOptionsFormRow = ({backend = null, currentOptions = {}, onChange}) => {
  if (!backend) return null;

  const hasOptionsForm = Boolean(backend && Object.keys(backend.schema.properties).length);
  // either use the custom backend-specific defined form, or fall back to the generic react-json-schema-form
  const OptionsFormComponent = BACKEND_OPTIONS_FORMS[backend.id]?.form ?? FormRjsfWrapper;
  if (!hasOptionsForm && !BACKEND_OPTIONS_FORMS[backend.id]) {
    return null;
  }
  return (
    <FormRow>
      <OptionsFormComponent
        name="form.registrationBackendOptions"
        label={
          <FormattedMessage
            defaultMessage="Registration backend options"
            description="Registration backend options label"
          />
        }
        schema={backend.schema}
        uiSchema={BACKEND_OPTIONS_FORMS[backend.id]?.uiSchema || {}}
        formData={currentOptions}
        onChange={({formData}) =>
          onChange({target: {name: 'form.registrationBackendOptions', value: formData}})
        }
      />
    </FormRow>
  );
};

BackendOptionsFormRow.propTypes = {
  backend: BackendType,
  currentOptions: PropTypes.object,
  onChange: PropTypes.func.isRequired,
};

const RegistrationFields = ({
  backends = [],
  selectedBackend = '',
	backendInstances = [],
	selectedBackendInstance = '',
  backendOptions = {},
  onChange,
}) => {
  const intl = useIntl();

  const backendChoices = backends.map(backend => [backend.id, backend.label]);
  const backend = backends.find(backend => backend.id === selectedBackend);

	// TODO
	const backendInstanceChoices = backendInstances.map(
		backendInstance => [backendInstance.id, backendInstance.label]
	);
  const backendInstance = backendInstances.find(
		backendInstance => backendInstance.id === selectedBackendInstance
	);

  const addAnotherMsg = intl.formatMessage({
    description: 'Button text to add extra item',
    defaultMessage: 'Add another',
  });

  return (
    <Fieldset
      style={{'--of-add-another-text': `"${addAnotherMsg}"`}}
      extraClassName="admin-fieldset"
    >
      <FormRow>
        <Field
          name="form.registrationBackend"
          label={
            <FormattedMessage
              defaultMessage="Select registration backend"
              description="Registration backend label"
            />
          }
        >
          <Select
            choices={backendChoices}
            value={selectedBackend}
            onChange={event => {
              onChange(event);
              // Clear options when changing backend
              onChange({target: {name: 'form.registrationBackendOptions', value: {}}});
            }}
            allowBlank={true}
          />
        </Field>
      </FormRow>

      <FormRow>
        <Field
          name="form.registrationBackendInstance"
          label={
            <FormattedMessage
              defaultMessage="Select registration backend instance"
              description="Registration backend instance label"
            />
          }
        >
          <Select
            choices={backendInstanceChoices}
            value={selectedBackendInstance}
            onChange={event => {
              onChange(event);
              // Clear options when changing backend
              onChange({target: {name: 'form.registrationBackendOptions', value: {}}});
            }}
            allowBlank={true}
          />
        </Field>
      </FormRow>

      <BackendOptionsFormRow
        backend={backend}
        currentOptions={backendOptions}
        onChange={onChange}
      />
    </Fieldset>
  );
};

RegistrationFields.propTypes = {
  backends: PropTypes.arrayOf(BackendType),
  selectedBackend: PropTypes.string,
  backendOptions: PropTypes.object,
  onChange: PropTypes.func.isRequired,
};

export default RegistrationFields;
