import _ from 'lodash';
import PropTypes from 'prop-types';
import {useContext, useState} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import {FormContext} from 'components/admin/form_design/Context';
import RegistrationBackendSelection from 'components/admin/form_design/RegistrationBackendSelection';
import StepSelection from 'components/admin/form_design/StepSelection';
import DSLEditorNode from 'components/admin/form_design/logic/DSLEditorNode';
import {
  MODIFIABLE_PROPERTIES,
  STRING_TO_TYPE,
  TYPE_TO_STRING,
} from 'components/admin/form_design/logic/constants';
import ServiceFetchConfigurationPicker from 'components/admin/form_design/variables/ServiceFetchConfigurationPicker';
import ActionButton from 'components/admin/forms/ActionButton';
import ComponentSelection from 'components/admin/forms/ComponentSelection';
import JsonWidget from 'components/admin/forms/JsonWidget';
import Select from 'components/admin/forms/Select';
import VariableSelection from 'components/admin/forms/VariableSelection';
import Modal from 'components/admin/modals/Modal';

import DMNActionConfig from './dmn/DMNActionConfig';
import {detectMappingProblems as detectDMNMappingProblems} from './dmn/utils';
import {SynchronizeVariablesActionConfig} from './synchronize_variable/SynchronizeVariablesConfigModal';
import {ActionError, Action as ActionType} from './types';

const ActionProperty = ({action, errors, onChange}) => {
  const modifiablePropertyChoices = Object.entries(MODIFIABLE_PROPERTIES).map(([key, info]) => [
    key,
    info.label,
  ]);

  const castValueTypeToString = action => {
    const valueType = action.action.property.type;
    const value = action.action.state;
    return TYPE_TO_STRING[valueType](value);
  };

  const castValueStringToType = value => {
    const valueType = action.action.property.type;
    return STRING_TO_TYPE[valueType](value);
  };

  return (
    <>
      <DSLEditorNode errors={errors.component}>
        <ComponentSelection name="component" value={action.component} onChange={onChange} />
      </DSLEditorNode>
      <DSLEditorNode errors={errors.action?.property?.value}>
        <Select
          name="action.property"
          choices={modifiablePropertyChoices}
          translateChoices
          allowBlank
          onChange={e => {
            const propertySelected = e.target.value;
            const fakeEvent = {
              target: {
                name: e.target.name,
                value: {
                  type: MODIFIABLE_PROPERTIES[propertySelected]?.type || '',
                  value: propertySelected,
                },
              },
            };
            onChange(fakeEvent);
          }}
          value={action.action.property.value}
        />
      </DSLEditorNode>
      {MODIFIABLE_PROPERTIES[action.action.property.value] && (
        <DSLEditorNode errors={errors.action?.state}>
          <Select
            name="action.state"
            choices={MODIFIABLE_PROPERTIES[action.action.property.value].options}
            translateChoices
            allowBlank
            onChange={event => {
              onChange({
                target: {
                  name: event.target.name,
                  value: castValueStringToType(event.target.value),
                },
              });
            }}
            value={castValueTypeToString(action)}
          />
        </DSLEditorNode>
      )}
    </>
  );
};

const ActionVariableValue = ({action, errors, onChange}) => (
  <>
    <DSLEditorNode errors={errors.variable}>
      <VariableSelection name="variable" onChange={onChange} value={action.variable} />
    </DSLEditorNode>
    <DSLEditorNode errors={errors.action?.value}>
      <JsonWidget name="action.value" logic={action.action.value} onChange={onChange} />
    </DSLEditorNode>
  </>
);

const ActionSynchronizeVariables = ({action, errors, onChange}) => {
  const intl = useIntl();
  const [isModalOpen, setIsModalOpen] = useState(false);

  const config = {
    sourceVariable: '',
    destinationVariable: '',
    identifierVariable: '',
    dataMappings: [],
    ...(action?.action?.config || {}),
  };

  const onConfigSave = values => {
    onChange({target: {name: 'action.config', value: values}});
    setIsModalOpen(false);
  };

  const getRelevantErrors = errors => {
    const relevantErrors = errors.action?.value ? [errors.action.value] : [];
    if (!errors.action?.config) {
      return relevantErrors;
    }

    // Global errors about the config should be shown at the top level.
    // Otherwise, there are some errors in the config, that should be announced.
    relevantErrors.push(
      typeof errors.action.config === 'string'
        ? errors.action.config
        : intl.formatMessage({
            description: 'Synchronize variables configuration errors message',
            defaultMessage: 'There are errors in the Synchronize variables configuration.',
          })
    );
    return relevantErrors;
  };

  return (
    <>
      <DSLEditorNode errors={getRelevantErrors(errors)}>
        <label className="required" htmlFor="sync_variables_config_button">
          <FormattedMessage
            description="Configuration button Synchronize variables label"
            defaultMessage="Synchronize variables configuration:"
          />
        </label>
        {!(
          config.sourceVariable &&
          config.destinationVariable &&
          Object.keys(config.dataMappings || []).length !== 0
        )
          ? intl.formatMessage({
              description: 'Synchronize variables not configured yet message',
              defaultMessage: '(not configured yet or partially configured)',
            })
          : null}
        <ActionButton
          id="sync_variables_config_button"
          name="sync_variables_config_button"
          onClick={event => {
            event.preventDefault();
            setIsModalOpen(true);
          }}
          text={intl.formatMessage({
            description: 'Button to open Synchronize variables configuration modal',
            defaultMessage: 'Configure',
          })}
        />
      </DSLEditorNode>

      <Modal
        isOpen={isModalOpen}
        closeModal={() => {
          setIsModalOpen(false);
        }}
        title={
          <FormattedMessage
            description="Synchronizing variables configuration modal title"
            defaultMessage="Synchronize variables configuration"
          />
        }
        contentModifiers={['with-form', 'large']}
      >
        <SynchronizeVariablesActionConfig
          initialValues={config}
          onSave={onConfigSave}
          errors={errors.action?.config}
        />
      </Modal>
    </>
  );
};

const ActionFetchFromService = ({action, errors, onChange}) => {
  const intl = useIntl();
  const [isModalOpen, setIsModalOpen] = useState(false);

  const closeModal = () => {
    setIsModalOpen(false);
  };

  const formContext = useContext(FormContext);

  const serviceFetchConfigFromVar =
    _.cloneDeep(formContext.formVariables.find(element => element.key === action.variable))
      ?.serviceFetchConfiguration || undefined;

  if (serviceFetchConfigFromVar) {
    if (!Array.isArray(serviceFetchConfigFromVar.headers)) {
      serviceFetchConfigFromVar.headers = Object.entries(serviceFetchConfigFromVar.headers || {});
    }

    if (!Array.isArray(serviceFetchConfigFromVar.queryParams)) {
      serviceFetchConfigFromVar.queryParams = Object.entries(
        serviceFetchConfigFromVar.queryParams || {}
      );
    }

    switch (serviceFetchConfigFromVar.dataMappingType) {
      case 'JsonLogic':
        serviceFetchConfigFromVar.jsonLogicExpression = serviceFetchConfigFromVar.mappingExpression;
        break;
      case 'jq':
        serviceFetchConfigFromVar.jqExpression = serviceFetchConfigFromVar.mappingExpression;
        break;
      default:
        serviceFetchConfigFromVar.jqExpression = serviceFetchConfigFromVar.mappingExpression;
    }
  }

  const actionButtonId = `open_service_fetch_modal_for_${action.variable}`;
  return (
    <>
      <DSLEditorNode errors={errors.variable}>
        <VariableSelection
          name="variable"
          value={action.variable}
          onChange={onChange}
          // Only values of user defined values can be set
          filter={variable => variable.source === 'user_defined'}
        />
      </DSLEditorNode>
      <DSLEditorNode errors={errors.action?.value}>
        <label className="required" htmlFor={actionButtonId}>
          <FormattedMessage
            description="Currently selected service fetch configuration label"
            defaultMessage="Fetch configuration:"
          />
        </label>
        {serviceFetchConfigFromVar?.name ||
          intl.formatMessage({
            description: 'No service fetch configuration configured yet message',
            defaultMessage: '(not configured yet)',
          })}
        <ActionButton
          id={actionButtonId}
          name="_open_service_fetch_modal"
          onClick={event => {
            event.preventDefault();
            setIsModalOpen(true);
          }}
          text={intl.formatMessage({
            description: 'Button to open service fetch configuration modal',
            defaultMessage: 'Configure',
          })}
        />
      </DSLEditorNode>

      <Modal
        isOpen={isModalOpen}
        closeModal={closeModal}
        title={
          <FormattedMessage
            description="Service fetch configuration selection modal title"
            defaultMessage="Service fetch configuration"
          />
        }
        contentModifiers={['with-form', 'large']}
      >
        <ServiceFetchConfigurationPicker
          initialValues={serviceFetchConfigFromVar}
          variableName={action.variable}
          onFormSave={closeModal}
          onChange={onChange}
        />
      </Modal>
    </>
  );
};

const ActionStepNotApplicable = ({action, errors, onChange}) => {
  return (
    <DSLEditorNode errors={errors.formStepUuid}>
      <StepSelection name="formStepUuid" value={action.formStepUuid} onChange={onChange} />
    </DSLEditorNode>
  );
};

const ActionStepApplicable = ({action, errors, onChange}) => {
  return (
    <DSLEditorNode errors={errors.formStepUuid}>
      <StepSelection name="formStepUuid" value={action.formStepUuid} onChange={onChange} />
    </DSLEditorNode>
  );
};

const ActionSetRegistrationBackend = ({action, errors, onChange}) => {
  return (
    <DSLEditorNode errors={errors.value}>
      <RegistrationBackendSelection
        name="action.value"
        value={action.action.value}
        onChange={onChange}
      />
    </DSLEditorNode>
  );
};

const ActionEvaluateDMN = ({action, errors, onChange}) => {
  const intl = useIntl();
  const [isModalOpen, setIsModalOpen] = useState(false);

  const onConfigSave = values => {
    onChange({target: {name: 'action.config', value: values}});

    setIsModalOpen(false);
  };

  const config = {
    pluginId: '',
    decisionDefinitionId: '',
    decisionDefinitionVersion: '',
    inputMapping: [],
    outputMapping: [],
    ...(action?.action?.config || {}),
  };

  const getRelevantErrors = errors => {
    const relevantErrors = errors.action?.value ? [errors.action.value] : [];
    if (!errors.action?.config) {
      return relevantErrors;
    }

    // Global errors about the config should be shown at the top level.
    // Otherwise, there are some errors in the config, that should be announced.
    relevantErrors.push(
      typeof errors.action.config === 'string'
        ? errors.action.config
        : intl.formatMessage({
            description: 'DMN evaluation configuration errors message',
            defaultMessage: 'There are errors in the DMN configuration.',
          })
    );
    return relevantErrors;
  };

  return (
    <>
      <DSLEditorNode errors={getRelevantErrors(errors)}>
        <label className="required" htmlFor="dmn_config_button">
          <FormattedMessage
            description="Configuration button DMN label"
            defaultMessage="DMN configuration:"
          />
        </label>
        {config.pluginId ||
          intl.formatMessage({
            description: 'DMN evaluation not configured yet message',
            defaultMessage: '(not configured yet)',
          })}
        <ActionButton
          id="dmn_config_button"
          name="dmn_config_button"
          onClick={event => {
            event.preventDefault();
            setIsModalOpen(true);
          }}
          text={intl.formatMessage({
            description: 'Button to open DMN configuration modal',
            defaultMessage: 'Configure',
          })}
        />
      </DSLEditorNode>

      <Modal
        isOpen={isModalOpen}
        closeModal={event => {
          setIsModalOpen(false);
        }}
        title={
          <FormattedMessage
            description="DMN configuration selection modal title"
            defaultMessage="DMN configuration"
          />
        }
        contentModifiers={['with-form', 'large']}
      >
        <DMNActionConfig
          initialValues={config}
          onSave={onConfigSave}
          errors={errors.action?.config}
        />
      </Modal>
    </>
  );
};

const ActionComponent = ({action, errors, onChange}) => {
  let Component;
  switch (action.action.type) {
    case 'property': {
      Component = ActionProperty;
      break;
    }
    case 'variable': {
      Component = ActionVariableValue;
      break;
    }
    case 'fetch-from-service': {
      Component = ActionFetchFromService;
      break;
    }
    case '':
    case 'disable-next': {
      return null;
    }
    case 'step-not-applicable': {
      Component = ActionStepNotApplicable;
      break;
    }
    case 'step-applicable': {
      Component = ActionStepApplicable;
      break;
    }
    case 'set-registration-backend': {
      Component = ActionSetRegistrationBackend;
      break;
    }
    case 'evaluate-dmn': {
      Component = ActionEvaluateDMN;
      break;
    }
    case 'synchronize-variables': {
      Component = ActionSynchronizeVariables;
      break;
    }
    default: {
      throw new Error(`Unknown action type: ${action.action.type}`);
    }
  }

  return <Component action={action} errors={errors} onChange={onChange} />;
};

ActionComponent.propTypes =
  ActionProperty.propTypes =
  ActionVariableValue.propTypes =
  ActionFetchFromService.propTypes =
  ActionStepNotApplicable.propTypes =
  ActionEvaluateDMN.propTypes =
    {
      action: ActionType.isRequired,
      errors: ActionError,
      onChange: PropTypes.func.isRequired,
    };

export const detectProblems = (action, intl) => {
  switch (action.action.type) {
    case 'evaluate-dmn': {
      const problems = [];

      const hasInputMappingProblems = action.action.config?.inputMapping?.some(
        mapping => detectDMNMappingProblems(intl, mapping).length > 0
      );
      if (hasInputMappingProblems) {
        problems.push(
          intl.formatMessage({
            description: 'Warning message: DMN input mapping problems detected',
            defaultMessage: 'invalid input mapping(s)',
          })
        );
      }
      const hasOutputMappingProblems = action.action.config?.outputMapping?.some(
        mapping => detectDMNMappingProblems(intl, mapping).length > 0
      );
      if (hasOutputMappingProblems) {
        problems.push(
          intl.formatMessage({
            description: 'Warning message: DMN output mapping problems detected',
            defaultMessage: 'invalid output mapping(s)',
          })
        );
      }
      return problems;
    }
  }
  return [];
};

export {ActionComponent};
