import {produce} from 'immer';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import ActionButton, {SubmitAction} from 'components/admin/forms/ActionButton';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import Select from 'components/admin/forms/Select';
import SubmitRow from 'components/admin/forms/SubmitRow';
import {jsonComplex as COMPLEX_JSON_TYPES} from 'components/admin/json_editor/types';
import {FormModal} from 'components/admin/modals';

import ComplexProcessVariables from './ComplexProcessVariables';
import SelectProcessVariables from './SelectProcessVariables';

const EMPTY_PROCESS_VARIABLE = {
  enabled: true,
  componentKey: '',
  alias: '',
};

const EMPTY_COMPLEX_PROCESS_VARIABLE = {
  enabled: true,
  type: 'object',
  definition: {},
  alias: '',
};

const getProcessSelectionChoices = (processDefinitions, processDefinition) => {
  const processDefinitionChoices = Object.entries(processDefinitions).map(
    ([processKey, versions]) => {
      // grab the first version name - it is theoretically possible the process name has changed in
      // another version, but not much we can do about that
      const name = versions[0].name;
      return [processKey, `${name} (${processKey})`];
    }
  );

  const versionChoices = !processDefinition
    ? []
    : processDefinitions[processDefinition].map(version => {
        return [`${version.version}`, `v${version.version}`];
      });

  return [processDefinitionChoices, versionChoices];
};

const ProcessDefinitionFields = ({
  processDefinitionChoices,
  processDefinition,
  versionChoices,
  processDefinitionVersion,
  onChange,
}) => (
  <Fieldset>
    <FormRow>
      <Field
        name="processDefinition"
        label={
          <FormattedMessage
            description="Camunda 'process definition' label"
            defaultMessage="Process"
          />
        }
        helpText={
          <FormattedMessage
            description="Camunda 'process definition' help text"
            defaultMessage="The process definition for which to start a process instance."
          />
        }
        required
      >
        <Select
          name="processDefinition"
          choices={processDefinitionChoices}
          value={processDefinition}
          onChange={onChange}
          allowBlank
        />
      </Field>
    </FormRow>

    <FormRow>
      <Field
        name="processDefinitionVersion"
        label={
          <FormattedMessage
            description="Camunda 'process definition version' label"
            defaultMessage="Version"
          />
        }
        helpText={
          <FormattedMessage
            description="Camunda 'process definition version' help text"
            defaultMessage="Which version of the process definition to start. The latest version is used if not specified."
          />
        }
      >
        <Select
          name="processDefinitionVersion"
          choices={versionChoices}
          value={processDefinitionVersion ? `${processDefinitionVersion}` : ''}
          onChange={onChange}
          allowBlank
        />
      </Field>
    </FormRow>
  </Fieldset>
);

const ManageSimpleVarsButton = ({onClick, numVars}) => {
  const intl = useIntl();
  return (
    <span style={{display: 'flex', flexDirection: 'column', gap: '5px'}}>
      <ActionButton
        text={intl.formatMessage({
          description: 'Open manage camunda process vars modal button',
          defaultMessage: 'Manage process variables',
        })}
        type="button"
        onClick={onClick}
      />
      &nbsp;
      <FormattedMessage
        description="Managed Camunda process vars state feedback"
        defaultMessage="{varCount, plural,
                      =0 {}
                      one {(1 variable mapped)}
                      other {({varCount} variables mapped)}
                  }"
        values={{varCount: numVars}}
      />
    </span>
  );
};

const ManageComplexVarsButton = ({onClick, numVars}) => {
  const intl = useIntl();
  return (
    <span style={{display: 'flex', flexDirection: 'column', gap: '5px'}}>
      <ActionButton
        text={intl.formatMessage({
          description: 'Open manage complex camunda process vars modal button',
          defaultMessage: 'Complex process variables',
        })}
        type="button"
        onClick={onClick}
      />
      &nbsp;
      <FormattedMessage
        description="Managed complex Camunda process vars state feedback"
        defaultMessage="{varCount, plural,
                      =0 {}
                      one {(1 variable defined)}
                      other {({varCount} variables defined)}
                  }"
        values={{varCount: numVars}}
      />
    </span>
  );
};

const FormFields = ({processDefinitions, formData, onChange}) => {
  const {
    processDefinition = '',
    processDefinitionVersion = null,
    processVariables = [],
    complexProcessVariables = [],
  } = formData;

  const intl = useIntl();
  const [baseModalOpen, setBaseModalOpen] = useState(false);
  const [simpleVarsModalOpen, setSimpleVarsModalOpen] = useState(false);
  const [complexVarsModalOpen, setComplexVarsModalOpen] = useState(false);

  const [processDefinitionChoices, versionChoices] = getProcessSelectionChoices(
    processDefinitions,
    processDefinition
  );

  const onFieldChange = event => {
    const {name, value} = event.target;
    const updatedFormData = produce(formData, draft => {
      draft[name] = value;

      switch (name) {
        // if the definition changes, reset the version & mapped variables
        case 'processDefinition': {
          draft.processDefinitionVersion = null;
          // reset variables if a different process is used
          draft.processVariables = [];
          draft.complexProcessVariables = [];
          break;
        }
        // normalize blank option to null
        case 'processDefinitionVersion': {
          if (value === '') {
            draft.processDefinitionVersion = null;
          } else {
            draft.processDefinitionVersion = parseInt(value, 10);
          }
          break;
        }
      }
    });

    // call parent event-handler with fully updated form data object
    onChange(updatedFormData);
  };

  const onAddProcessVariable = () => {
    const nextFormData = produce(formData, draft => {
      if (!draft.processVariables) draft.processVariables = [];
      draft.processVariables.push(EMPTY_PROCESS_VARIABLE);
    });
    onChange(nextFormData);
  };

  const onChangeProcessVariable = (index, event) => {
    const {name, value} = event.target;
    const nextFormData = produce(formData, draft => {
      draft.processVariables[index][name] = value;
    });
    onChange(nextFormData);
  };

  const onDeleteProcessVariable = index => {
    const nextFormData = produce(formData, draft => {
      draft.processVariables.splice(index, 1);
    });
    onChange(nextFormData);
  };

  const onAddComplexProcessVariable = () => {
    const nextFormData = produce(formData, draft => {
      if (!draft.complexProcessVariables) draft.complexProcessVariables = [];
      draft.complexProcessVariables.push(EMPTY_COMPLEX_PROCESS_VARIABLE);
    });
    onChange(nextFormData);
  };
  const onChangeComplexProcessVariable = (index, event) => {
    const {isFullObject = false, name, value, type, definition} = event.target;

    const nextFormData = produce(formData, draft => {
      if (!isFullObject) {
        draft.complexProcessVariables[index][name] = value;
      } else {
        draft.complexProcessVariables[index].type = type;
        draft.complexProcessVariables[index].definition = definition;
      }
    });

    onChange(nextFormData);
  };
  const onDeleteComplexProcessVariable = (index, event) => {
    const nextFormData = produce(formData, draft => {
      draft.complexProcessVariables.splice(index, 1);
    });
    onChange(nextFormData);
  };

  return (
    <>
      <div style={{display: 'flex', gap: '10px', alignItems: 'start'}}>
        <ActionButton
          text={intl.formatMessage({
            description: 'Link label to open registration options modal',
            defaultMessage: 'Configure options',
          })}
          type="button"
          onClick={() => setBaseModalOpen(!baseModalOpen)}
        />

        <ManageSimpleVarsButton
          numVars={processVariables.length}
          onClick={() => setSimpleVarsModalOpen(!simpleVarsModalOpen)}
        />

        <ManageComplexVarsButton
          numVars={complexProcessVariables.length}
          onClick={() => setComplexVarsModalOpen(!complexVarsModalOpen)}
        />
      </div>

      <FormModal
        isOpen={baseModalOpen}
        title={
          <FormattedMessage
            description="Camunda registration options modal title"
            defaultMessage="Plugin configuration: Camunda"
          />
        }
        closeModal={() => setBaseModalOpen(false)}
        extraModifiers={['small']}
      >
        <ProcessDefinitionFields
          processDefinitionChoices={processDefinitionChoices}
          processDefinition={processDefinition}
          versionChoices={versionChoices}
          processDefinitionVersion={processDefinitionVersion}
          onChange={onFieldChange}
        />
      </FormModal>

      <FormModal
        isOpen={simpleVarsModalOpen}
        title={
          <FormattedMessage
            description="Camunda process var selection modal title"
            defaultMessage="Manage process variables"
          />
        }
        closeModal={() => setSimpleVarsModalOpen(false)}
      >
        <SelectProcessVariables
          processVariables={processVariables}
          onChange={onChangeProcessVariable}
          onAdd={onAddProcessVariable}
          onDelete={onDeleteProcessVariable}
        />
        <SubmitRow>
          <SubmitAction
            text={intl.formatMessage({
              description: 'Camunda process variables confirm button',
              defaultMessage: 'Confirm',
            })}
            onClick={event => {
              event.preventDefault();
              setSimpleVarsModalOpen(false);
            }}
          />
        </SubmitRow>
      </FormModal>

      <FormModal
        isOpen={complexVarsModalOpen}
        title={
          <FormattedMessage
            description="Camunda complex process vars modal title"
            defaultMessage="Manage complex process variables"
          />
        }
        closeModal={() => setComplexVarsModalOpen(false)}
      >
        <ComplexProcessVariables
          variables={complexProcessVariables}
          onChange={onChangeComplexProcessVariable}
          onAdd={onAddComplexProcessVariable}
          onDelete={onDeleteComplexProcessVariable}
        />
        <SubmitRow>
          <SubmitAction
            text={intl.formatMessage({
              description: 'Camunda complex process variables confirm button',
              defaultMessage: 'Confirm',
            })}
            onClick={event => {
              event.preventDefault();
              setComplexVarsModalOpen(false);
            }}
          />
        </SubmitRow>
      </FormModal>
    </>
  );
};

FormFields.propTypes = {
  processDefinitions: PropTypes.objectOf(
    PropTypes.arrayOf(
      PropTypes.shape({
        id: PropTypes.string.isRequired,
        key: PropTypes.string.isRequired,
        name: PropTypes.string.isRequired,
        version: PropTypes.number.isRequired,
      })
    )
  ).isRequired,
  formData: PropTypes.shape({
    // matches the backend serializer!
    processDefinition: PropTypes.string,
    processDefinitionVersion: PropTypes.number,
    processVariables: PropTypes.arrayOf(
      PropTypes.shape({
        enabled: PropTypes.bool.isRequired,
        componentKey: PropTypes.string.isRequired,
        alias: PropTypes.string.isRequired,
      })
    ),
    complexProcessVariables: PropTypes.arrayOf(
      PropTypes.shape({
        enabled: PropTypes.bool,
        alias: PropTypes.string,
        type: PropTypes.oneOf(COMPLEX_JSON_TYPES).isRequired,
        definition: PropTypes.oneOfType([PropTypes.object, PropTypes.array]),
      })
    ),
  }),
  onChange: PropTypes.func.isRequired,
};

export default FormFields;
