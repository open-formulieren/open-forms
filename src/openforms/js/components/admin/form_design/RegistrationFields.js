import PropTypes from 'prop-types';
import {React, useContext} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import ButtonContainer from 'components/admin/forms/ButtonContainer';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';
import ModalJsonSchemaGeneration from 'components/admin/forms/ModalJsonSchemaGeneration';
import Select from 'components/admin/forms/Select';
import {DeleteIcon} from 'components/admin/icons';

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

const BackendOptionsFormRow = ({backendType = null, currentOptions = {}, onChange, index}) => {
  if (!backendType) return null;
  // if there's no configuration form, there's nothing to do
  if (!Object.keys(backendType.schema.properties).length) return null;

  // Look up the configuration form from the registry
  const OptionsFormComponent = BACKEND_OPTIONS_FORMS[backendType.id]?.form;
  if (!OptionsFormComponent) {
    console.debug(
      `No configuration form known in the registry for plugin with ID '${backendType.id}'.`
    );
    return null;
  }

  return (
    <FormRow>
      <OptionsFormComponent
        index={index}
        name={`form.registrationBackends.${index}.options`}
        label={
          <FormattedMessage
            defaultMessage="Registration backend options"
            description="Registration backend options label"
          />
        }
        schema={backendType.schema}
        formData={currentOptions}
        onChange={({formData}) =>
          onChange({target: {name: `form.registrationBackends.${index}.options`, value: formData}})
        }
      />
    </FormRow>
  );
};

BackendOptionsFormRow.propTypes = {
  backendType: BackendType,
  currentOptions: PropTypes.object,
  onChange: PropTypes.func.isRequired,
  index: PropTypes.number.isRequired,
};

const BackendFields = ({index = 0, backend, availableBackends = [], onChange, onDelete}) => {
  const intl = useIntl();

  const backendChoices = availableBackends.map(backend => [backend.id, backend.label]);
  const selectedBackend = backend.backend || '';
  const selectedBackendType = availableBackends.find(choice => choice.id === selectedBackend);

  let showSchemaButton = ['json_dump', 'objects_api'].includes(backend.backend);
  if (backend.backend === 'objects_api' && backend.options.version === 1) {
    showSchemaButton = false;
  }

  const addAnotherMsg = intl.formatMessage({
    description: 'Button text to add extra item',
    defaultMessage: 'Add another',
  });

  return (
    <Fieldset
      style={{'--of-add-another-text': `"${addAnotherMsg}"`}}
      title={
        <>
          {backend.name || backend.key}
          <DeleteIcon onConfirm={onDelete} />
        </>
      }
    >
      <FormRow>
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
          <TextInput onChange={onChange} value={backend.name || ''} />
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
        backendType={selectedBackendType}
        currentOptions={backend.options || {}}
        onChange={onChange}
      />

      {showSchemaButton && (
        <FormRow>
          <Field
            name={`form.registrationBackends.${index}.schema`}
            label={
              <FormattedMessage
                defaultMessage="Form JSON schema"
                description="Form JSON schema label"
              />
            }
            helpText={
              <FormattedMessage
                defaultMessage={`Before generating a schema, ensure the options are configured and
                 the complete form is saved.`}
                description="Form JSON schema help text"
              />
            }
          >
            <ModalJsonSchemaGeneration
              modalTitle={
                <FormattedMessage
                  description="Generate JSON schema modal title"
                  defaultMessage={`Form JSON schema: {backendLabel}`}
                  values={{backendLabel: selectedBackendType.label}}
                />
              }
              backendKey={backend.key}
            />
          </Field>
        </FormRow>
      )}
    </Fieldset>
  );
};

BackendFields.propTypes = {
  index: PropTypes.number,
  backend: PropTypes.shape({
    key: PropTypes.string.isRequired,
    name: PropTypes.string,
    backend: PropTypes.string,
    options: PropTypes.object,
  }),
  availableBackends: PropTypes.arrayOf(BackendType),
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
      {Array.from(configuredBackends.entries()).map(([idx, backend]) => (
        <BackendFields
          key={backend.key}
          index={idx}
          backend={backend}
          availableBackends={availableBackends}
          onChange={onChange}
          onDelete={() => onDelete(backend.key)}
        />
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
