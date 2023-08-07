import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import FormRjsfWrapper from 'components/admin/RJSFWrapper';
import ButtonContainer from 'components/admin/forms/ButtonContainer';
import DeleteIcon from 'components/admin/DeleteIcon';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput, Input} from 'components/admin/forms/Inputs';
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

const backendKeyGenerator = (function* () {
  let i = 1;
  while (true) yield `backend${i++}`;
})();

const BackendOptionsFormRow = ({backend = null, currentOptions = {}, onChange, index}) => {
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
        name={`form.registrationBackends.${index}.options`}
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
          onChange({target: {name: `form.registrationBackends.${index}.options`, value: formData}})
        }
      />
    </FormRow>
  );
};

BackendOptionsFormRow.propTypes = {
  backend: BackendType,
  currentOptions: PropTypes.object,
  onChange: PropTypes.func.isRequired,
  index: PropTypes.number,
};

const RegistrationFieldSet = ({
  index = 0,
  backendKey = '',
  backendName = '',
  backends = [],
  selectedBackend = '',
  backendOptions = {},
  onChange,
  onDelete,
}) => {
  const intl = useIntl();

  const backendChoices = backends.map(backend => [backend.id, backend.label]);
  const backend = backends.find(backend => backend.id === selectedBackend);

  const addAnotherMsg = intl.formatMessage({
    description: 'Button text to add extra item',
    defaultMessage: 'Add another',
  });

  return (
    <Fieldset
      style={{'--of-add-another-text': `"${addAnotherMsg}"`}}
      extraClassName="admin-fieldset"
      title={
        <>
          {backendName || backendKey}
          <DeleteIcon onConfirm={onDelete} />
        </>
      }
    >
      {
        // <FormRow>
        //   <Field
        //     name={`form.registrationBackends.${index}.key`}
        //     label={<FormattedMessage defaultMessage="Key" description="Registration backend key" />}
        //     helpText={
        //       <FormattedMessage
        //         defaultMessage="The key to use to refer to this configuration in form logic."
        //         description="Backend key help text"
        //       />
        //     }
        //     disabled
        //   >
        //   <TextInput onChange={onChange} value={backendKey} />
        //   </Field>
        // </FormRow>
        //
      }
      <FormRow>
        <Input type="hidden" onChange={onChange} value={backendKey} />
        <Field
          name={`form.registrationBackends.${index}.name`}
          label={
            <FormattedMessage defaultMessage="Name" description="Registration backend long name" />
          }
          helpText={
            <FormattedMessage
              defaultMessage="A recognisable name for this backend configuration."
              description="Backend name help text"
            />
          }
        >
          <TextInput onChange={onChange} value={backendName} />
        </Field>
      </FormRow>
      <FormRow>
        <Field
          name={`form.registrationBackends.${index}.backend`}
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
              onChange({target: {name: `form.registrationBackends.${index}.options`, value: {}}});
            }}
            allowBlank={true}
          />
        </Field>
      </FormRow>

      <BackendOptionsFormRow
        index={index}
        backend={backend}
        currentOptions={backendOptions}
        onChange={onChange}
      />
    </Fieldset>
  );
};

RegistrationFieldSet.propTypes = {
  index: PropTypes.number,
  backendKey: PropTypes.string,
  backendName: PropTypes.string,
  backends: PropTypes.arrayOf(BackendType),
  selectedBackend: PropTypes.string,
  backendOptions: PropTypes.object,
  onChange: PropTypes.func.isRequired,
};

const RegistrationFields = ({
  availableBackends = [],
  configuredBackends = [{}],
  onChange,
  addBackend,
  onDelete,
}) => {
  return (
    <>
      {Array.from(configuredBackends.entries()).map(([idx, {key, name, backend, options}]) => (
        <>
          <RegistrationFieldSet
            key={key}
            index={idx}
            backendKey={key}
            backendName={name}
            backends={availableBackends}
            selectedBackend={backend}
            backendOptions={options}
            onChange={onChange}
            onDelete={() => onDelete(key)}
          />
        </>
      ))}
      <ButtonContainer
        onClick={() => {
          // nextKey must be unique and stable
          const usedKeys = Object.fromEntries(configuredBackends.map(({key}) => [key, key]));
          let nextKey = backendKeyGenerator.next().value;
          while (usedKeys[nextKey]) nextKey = backendKeyGenerator.next().value;
          addBackend(nextKey);
        }}
      >
        <FormattedMessage
          description="Button text to add registration backend"
          defaultMessage="Add registration backend"
        />
      </ButtonContainer>
    </>
  );
};

export default RegistrationFields;
