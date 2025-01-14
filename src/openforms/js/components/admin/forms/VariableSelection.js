import classNames from 'classnames';
import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {useIntl} from 'react-intl';
import {components} from 'react-select';

import {FormContext} from 'components/admin/form_design/Context';
import {
  getVariableSourceLabel,
  groupVariablesBySource,
} from 'components/admin/form_design/variables/utils';

import {SelectWithoutFormik} from './ReactSelect';

const VariableOption = props => {
  const {value, label, formDefinitionName} = props.data;
  return (
    <components.Option {...props}>
      <span
        className={classNames('form-variable-dropdown-option', {
          'form-variable-dropdown-option--component-variable': !!formDefinitionName,
        })}
      >
        <span className="form-variable-dropdown-option__label">{label}</span>

        <code className="form-variable-dropdown-option__key">{value}</code>

        {formDefinitionName && (
          <span className="form-variable-dropdown-option__form-definition">
            {formDefinitionName}
          </span>
        )}
      </span>
    </components.Option>
  );
};

const allowAny = () => true;

const VariableSelection = ({
  id,
  name,
  value,
  onChange,
  includeStaticVariables = false,
  filter = allowAny,
  ...props
}) => {
  const {formSteps, formVariables, staticVariables} = useContext(FormContext);
  const intl = useIntl();

  let formDefinitionsNames = {};
  formSteps.forEach(step => {
    formDefinitionsNames[step.formDefinition || step._generatedId] = step.internalName || step.name;
  });

  const allFormVariables = (includeStaticVariables ? staticVariables : []).concat(formVariables);
  const relevantVariables = allFormVariables.filter(variable => filter(variable));

  const choices = groupVariablesBySource(relevantVariables).map(variableGroup => ({
    label: intl.formatMessage(getVariableSourceLabel(variableGroup.source)),
    options: variableGroup.variables.map(variable => ({
      label: variable.name,
      value: variable.key,
      formDefinitionName: variable.formDefinition
        ? formDefinitionsNames[variable.formDefinition]
        : undefined,
    })),
  }));

  return (
    <SelectWithoutFormik
      id={id}
      className="form-variable-dropdown"
      name={name}
      options={choices}
      onChange={newValue => onChange({target: {name, value: newValue}})}
      components={{Option: VariableOption}}
      value={value}
      {...props}
    />
  );
};

VariableSelection.propTypes = {
  id: PropTypes.string,
  name: PropTypes.string,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.arrayOf(PropTypes.string)]),
  onChange: PropTypes.func.isRequired,
  includeStaticVariables: PropTypes.bool,
  filter: PropTypes.func,
};

export default VariableSelection;
