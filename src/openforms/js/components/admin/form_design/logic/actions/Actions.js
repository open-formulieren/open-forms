import React, {useContext} from 'react';
import PropTypes from 'prop-types';

import ComponentSelection from '../../../forms/ComponentSelection';
import Select from '../../../forms/Select';
import {MODIFIABLE_PROPERTIES, STRING_TO_TYPE, TYPE_TO_STRING} from '../constants';
import OperandTypeSelection from '../OperandTypeSelection';
import LiteralValueInput from '../LiteralValueInput';
import StepSelection from '../StepSelection';
import {Action as ActionType, ActionError} from './types';
import DSLEditorNode from '../DSLEditorNode';
import {FormContext} from '../../Context';
import JsonWidget from '../../../forms/JsonWidget';

const ActionProperty = ({action, errors, onChange}) => {
  const modifiablePropertyChoices = Object.entries(MODIFIABLE_PROPERTIES).map(([key, info]) => [
    key,
    info.label,
  ]);

  const castValueTypeToString = action => {
    const valueType = action.action.property.type;
    const value = action.action.state;
    return value ? TYPE_TO_STRING[valueType](value) : value;
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

const ActionValue = ({action, errors, onChange}) => {
  const formContext = useContext(FormContext);
  const allComponents = formContext.components;
  const componentType = allComponents[action.component]?.type;

  const getValueSource = action => {
    if (!action.component) return '';

    return action.action.value.hasOwnProperty('var') ? 'component' : 'literal';
  };

  const valueSource = getValueSource(action);
  return (
    <>
      <DSLEditorNode errors={errors.component}>
        <ComponentSelection name="component" value={action.component} onChange={onChange} />
      </DSLEditorNode>
      <DSLEditorNode errors={null}>
        <OperandTypeSelection
          name="action.value"
          onChange={e => {
            onChange({
              target: {
                name: e.target.name,
                value: e.target.value === 'component' ? {var: ''} : '',
              },
            });
          }}
          operandType={valueSource}
          filter={([choiceKey, choiceLabel]) => ['literal', 'component'].includes(choiceKey)}
        />
      </DSLEditorNode>
      {valueSource === 'literal' && (
        <DSLEditorNode errors={null}>
          <LiteralValueInput
            name="action.value"
            componentType={componentType}
            value={action.action.value}
            onChange={onChange}
          />
        </DSLEditorNode>
      )}
      {valueSource === 'component' && (
        <DSLEditorNode errors={errors.action?.value}>
          <ComponentSelection
            name="action.value.var"
            value={action.action.value.var}
            onChange={onChange}
            filter={comp => comp.type === componentType}
          />
        </DSLEditorNode>
      )}
    </>
  );
};

const ActionVariableValue = ({action, errors, onChange}) => {
  const formContext = useContext(FormContext);
  const allVariables = formContext.formVariables;

  const getVariableChoices = variables => {
    return variables.map(variable => [variable.key, variable.name]);
  };

  return (
    <>
      <DSLEditorNode errors={errors.variable}>
        {/*TODO: This should be a searchable select for when there are a billion variables?*/}
        <Select
          name="variable"
          choices={getVariableChoices(allVariables)}
          allowBlank
          onChange={onChange}
          value={action.variable}
        />
      </DSLEditorNode>
      <DSLEditorNode errors={errors.action?.value}>
        <JsonWidget name="action.value" logic={action.action.value} onChange={onChange} />
      </DSLEditorNode>
    </>
  );
};

const ActionStepNotApplicable = ({action, errors, onChange}) => {
  return (
    <DSLEditorNode errors={errors.formStep}>
      <StepSelection name="formStep" value={action.formStep} onChange={onChange} />
    </DSLEditorNode>
  );
};

const ActionComponent = ({action, errors, onChange}) => {
  let Component;
  switch (action.action.type) {
    case 'property': {
      Component = ActionProperty;
      break;
    }
    case 'value': {
      Component = ActionValue;
      break;
    }
    case 'variable': {
      Component = ActionVariableValue;
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
    default: {
      throw new Error(`Unknown action type: ${action.action.type}`);
    }
  }

  return <Component action={action} errors={errors} onChange={onChange} />;
};

ActionComponent.propTypes = {
  action: ActionType.isRequired,
  errors: ActionError,
  onChange: PropTypes.func.isRequired,
};

export {ActionComponent};
