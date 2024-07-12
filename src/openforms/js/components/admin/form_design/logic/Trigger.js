import jsonLogic from 'json-logic-js';
import PropTypes from 'prop-types';
import React, {useContext, useState} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';
import {useImmerReducer} from 'use-immer';

import {FormContext} from 'components/admin/form_design/Context';
import {VARIABLE_SOURCES} from 'components/admin/form_design/variables/constants';
import ArrayInput from 'components/admin/forms/ArrayInput';
import Select from 'components/admin/forms/Select';
import VariableSelection from 'components/admin/forms/VariableSelection';
import useOnChanged from 'hooks/useOnChanged';
import {getTranslatedChoices} from 'utils/i18n';

import DSLEditorNode from './DSLEditorNode';
import DataPreview from './DataPreview';
import LiteralValueInput from './LiteralValueInput';
import OperandTypeSelection from './OperandTypeSelection';
import Today from './Today';
import ToggleCodeIcon from './ToggleCodeIcon';
import {OPERATORS, TYPE_TO_OPERAND_TYPE, TYPE_TO_OPERATORS} from './constants';

const OperatorSelection = ({name, selectedVariableType, operator, onChange}) => {
  const intl = useIntl();

  // only keep the relevant choices
  const allowedOperators = TYPE_TO_OPERATORS[selectedVariableType] || TYPE_TO_OPERATORS._default;
  const choices = Object.entries(OPERATORS).filter(([operator]) =>
    allowedOperators.includes(operator)
  );
  if (!choices.length) {
    return null;
  }

  return (
    <Select
      name={name}
      choices={getTranslatedChoices(intl, choices)}
      allowBlank
      onChange={onChange}
      value={operator}
    />
  );
};

OperatorSelection.propTypes = {
  name: PropTypes.string.isRequired,
  selectedVariableType: PropTypes.string.isRequired,
  operator: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
};

const initialState = {
  variable: '',
  operator: '',
  operandType: '',
  operand: '',
};

const TRIGGER_FIELD_ORDER = ['variable', 'operator', 'operandType', 'operand'];

const parseJsonLogic = (logic, allVariablesKeys) => {
  // Algorithm mostly taken from https://github.com/jwadhams/json-logic-js/blob/master/logic.js, combined
  // with our own organization.
  if (!logic || !Object.keys(logic).length) return {};

  // reference for parsing: https://jsonlogic.com/
  // a rule is always in the format {"operator": ["values" ...]} -> so grab the operator
  const operator = jsonLogic.get_operator(logic);
  let values = logic[operator];
  if (!Array.isArray(values)) {
    values = [values];
  }

  // first value should be the reference to the variable
  let variableKey = values[0].date ? values[0].date.var : values[0].var;
  if (Array.isArray(variableKey)) {
    // Case where a default is defined
    variableKey = variableKey[0];
  }

  // check if we're using a literal value, or a variable reference
  let compareValue = values[1];
  let operandType = '';
  let operand = '';

  // Selectboxes case: the variable name contains the reference to which value, e.g. "selectField.option1"
  if (!allVariablesKeys.includes(variableKey)) {
    let variableKeyBits = variableKey.split('.');
    variableKey = variableKeyBits.slice(0, variableKeyBits.length - 1).join('.');
    compareValue = variableKeyBits.slice(variableKeyBits.length - 1).join('.');
  }

  if (jsonLogic.is_logic(compareValue)) {
    const op = jsonLogic.get_operator(compareValue);
    switch (op) {
      case 'var': {
        operandType = 'variable';
        operand = compareValue.var;
        break;
      }
      case 'date': {
        operandType = compareValue.date.var ? 'variable' : 'literal';
        operand = compareValue.date.var ? compareValue.date.var : compareValue.date;
        break;
      }
      case 'datetime': {
        operandType = compareValue.datetime.var ? 'variable' : 'literal';
        operand = compareValue.datetime.var ? compareValue.datetime.var : compareValue.datetime;
        break;
      }
      case '+':
      case '-': {
        operandType = 'today';
        operand = compareValue;
        break;
      }
      default:
        console.warn(`Unsupported operator: ${op}, can't derive operandType`);
    }
  } else if (compareValue != null) {
    if (Array.isArray(compareValue)) {
      operandType = 'array';
    } else {
      operandType = 'literal';
    }
    operand = compareValue;
  }

  return {
    variable: variableKey,
    operator,
    operandType,
    operand,
  };
};

const reducer = (draft, action) => {
  switch (action.type) {
    case 'TRIGGER_CONFIGURATION_CHANGED': {
      const {name, value} = action.payload;
      draft[name] = value;

      // clear the dependent fields if needed - e.g. if the component changes, all fields to the right change
      const currentFieldIndex = TRIGGER_FIELD_ORDER.indexOf(name);
      const nextFieldNames = TRIGGER_FIELD_ORDER.slice(currentFieldIndex + 1);
      for (const name of nextFieldNames) {
        draft[name] = initialState[name];
      }
      break;
    }
    default: {
      throw new Error(`Unknown action type: ${action.type}`);
    }
  }
};

const Trigger = ({name, logic, onChange, error, children}) => {
  const intl = useIntl();
  const formContext = useContext(FormContext);
  const [viewMode, setViewMode] = useState('ui');
  const allVariables = formContext.staticVariables.concat(formContext.formVariables);
  const allVariablesObj = allVariables.reduce((obj, variable) => {
    obj[variable.key] = variable;
    return obj;
  }, {});

  // break down the json logic back into variables that can be managed by components state
  const parsedLogic = parseJsonLogic(logic, Object.keys(allVariablesObj));
  const [state, dispatch] = useImmerReducer(reducer, {...initialState, ...parsedLogic});

  // event handlers
  const onTriggerChange = event => {
    const {name, value} = event.target;
    dispatch({
      type: 'TRIGGER_CONFIGURATION_CHANGED',
      payload: {
        name,
        value,
      },
    });
  };

  // rendering logic
  const {variable: triggerVariableKey, operator, operandType, operand} = state;
  const triggerVariable = allVariablesObj[triggerVariableKey];

  let compareValue = null;
  let valueInput = null;

  switch (operandType) {
    case 'literal': {
      valueInput = (
        <LiteralValueInput
          name="operand"
          type={triggerVariable?.dataType}
          value={operand.toString()}
          onChange={onTriggerChange}
        />
      );

      const dataType = triggerVariable?.dataType;
      switch (dataType) {
        case 'date': {
          compareValue = {date: operand};
          break;
        }
        case 'datetime': {
          compareValue = {datetime: operand};
          break;
        }
        default: {
          compareValue = operand;
        }
      }
      break;
    }
    case 'variable': {
      valueInput = (
        <VariableSelection
          name="operand"
          value={operand}
          onChange={onTriggerChange}
          includeStaticVariables
          // filter variables of the same type as the trigger variable
          filter={variable => variable.dataType === triggerVariable?.dataType}
        />
      );
      if (triggerVariable?.dataType === 'datetime') {
        compareValue = {date: {var: operand}};
      } else {
        compareValue = {var: operand};
      }
      break;
    }
    case 'today': {
      valueInput = <Today name="operand" onChange={onTriggerChange} value={operand} />;

      let sign, relativeDelta;
      if (operand) {
        sign = jsonLogic.get_operator(operand);
        relativeDelta = operand[sign][1].rdelta || [0, 0, 0];
      } else {
        sign = '+';
        relativeDelta = [0, 0, 0];
      }
      compareValue = {};
      compareValue[sign] = [{today: []}, {rdelta: relativeDelta}];
      break;
    }
    case 'array': {
      valueInput = (
        <ArrayInput
          name="operand"
          inputType="text"
          values={operand}
          onChange={value => {
            const fakeEvent = {target: {name: 'operand', value: value}};
            onTriggerChange(fakeEvent);
          }}
        />
      );
      compareValue = operand;
      break;
    }
    case '': {
      // nothing selected yet
      break;
    }
    default: {
      throw new Error(`Unknown operand type: ${operandType}`);
    }
  }

  let firstOperand;
  if (triggerVariable?.source === VARIABLE_SOURCES.component) {
    const triggerComponent = formContext.components[triggerVariableKey];
    // Handling components special cases
    switch (triggerComponent.type) {
      case 'date': {
        firstOperand = {date: {var: triggerVariableKey}};
        break;
      }
      case 'selectboxes': {
        firstOperand = {var: `${triggerVariableKey}.${compareValue}`};
        compareValue = true;
        break;
      }
      case 'checkbox': {
        firstOperand = {var: triggerVariableKey};
        // cast from string to actual boolean
        if (compareValue === 'true') compareValue = true;
        if (compareValue === 'false') compareValue = false;
        break;
      }
      default:
        firstOperand = {var: triggerVariableKey};
    }
  } else if (
    triggerVariable?.source === VARIABLE_SOURCES.userDefined &&
    triggerVariable.dataType === 'boolean'
  ) {
    firstOperand = {var: triggerVariableKey};
    // cast from string to actual boolean
    if (compareValue === 'true') compareValue = true;
    if (compareValue === 'false') compareValue = false;
  } else {
    firstOperand = {var: triggerVariableKey};
  }

  const jsonLogicFromState = {
    [operator]: [firstOperand, compareValue],
  };

  // whenever we get a change in the jsonLogic definition, relay that back to the
  // parent component
  useOnChanged(jsonLogicFromState, () => onChange({target: {name, value: jsonLogicFromState}}));

  let triggerDisplay;
  switch (viewMode) {
    case 'ui': {
      triggerDisplay = (
        <div className="dsl-editor">
          <DSLEditorNode errors={null}>
            <FormattedMessage description="Logic trigger prefix" defaultMessage="When" />
          </DSLEditorNode>
          <DSLEditorNode errors={null}>
            <VariableSelection
              name="variable"
              value={triggerVariableKey}
              onChange={onTriggerChange}
              includeStaticVariables
            />
          </DSLEditorNode>
          {triggerVariableKey ? (
            <DSLEditorNode errors={null}>
              <OperatorSelection
                name="operator"
                selectedVariableType={triggerVariable?.dataType}
                operator={operator}
                onChange={onTriggerChange}
              />
            </DSLEditorNode>
          ) : null}
          {triggerVariableKey && operator ? (
            <DSLEditorNode errors={null}>
              <OperandTypeSelection
                name="operandType"
                operandType={operandType}
                onChange={onTriggerChange}
                filter={([choiceKey, choiceLabel]) => {
                  if (!triggerVariable.dataType) return true;
                  return getOperandTypesForVariableType(triggerVariable.dataType).includes(
                    choiceKey
                  );
                }}
              />
            </DSLEditorNode>
          ) : null}
          {triggerVariableKey && operator && operandType ? (
            <DSLEditorNode errors={null}>{valueInput}</DSLEditorNode>
          ) : null}
        </div>
      );
      break;
    }
    case 'json': {
      triggerDisplay = <DataPreview data={logic} />;
      break;
    }
    default: {
      throw new Error(`Unknown viewMode '${viewMode}'.`);
    }
  }

  return (
    <div className="logic-trigger">
      <div className="logic-trigger__editor">
        {error && <div className="logic-trigger__error">{error}</div>}
        {triggerDisplay}
      </div>

      {children ? <div className="logic-trigger__children">{children}</div> : null}

      <div>
        <ToggleCodeIcon viewMode={viewMode} setViewMode={setViewMode} />
      </div>
    </div>
  );
};

Trigger.propTypes = {
  name: PropTypes.string.isRequired,
  logic: PropTypes.object,
  onChange: PropTypes.func.isRequired,
  error: PropTypes.string,
  children: PropTypes.node,
};

const getOperandTypesForVariableType = componentType => {
  return TYPE_TO_OPERAND_TYPE[componentType] || TYPE_TO_OPERAND_TYPE._default;
};

export default Trigger;
