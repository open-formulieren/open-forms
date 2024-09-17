import PropTypes from 'prop-types';
import React, {useContext} from 'react';

import {FormContext} from 'components/admin/form_design/Context';

import {SelectWithoutFormik} from './ReactSelect';

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

  let formDefinitionsNames = {};
  formSteps.forEach(step => {
    formDefinitionsNames[step.formDefinition || step._generatedId] = step.internalName || step.name;
  });

  const allFormVariables = (includeStaticVariables ? staticVariables : []).concat(formVariables);
  const choices = allFormVariables
    .filter(variable => filter(variable))
    .map(variable => {
      const label = formDefinitionsNames[variable.formDefinition]
        ? `${formDefinitionsNames[variable.formDefinition]}: ${variable.name} (${variable.key})`
        : `${variable.name} (${variable.key})`;
      return {value: variable.key, label};
    });

  return (
    <SelectWithoutFormik
      id={id}
      className="form-variable-dropdown"
      name={name}
      options={choices}
      onChange={newValue => onChange({target: {name, value: newValue}})}
      value={value}
      {...props}
    />
  );
};

VariableSelection.propTypes = {
  id: PropTypes.string,
  name: PropTypes.string,
  value: PropTypes.string,
  onChange: PropTypes.func.isRequired,
  includeStaticVariables: PropTypes.bool,
  filter: PropTypes.func,
};

export default VariableSelection;
