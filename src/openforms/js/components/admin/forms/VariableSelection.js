import PropTypes from 'prop-types';
import React, {useContext} from 'react';

import {FormContext} from 'components/admin/form_design/Context';

import Select from './Select';

const allowAny = () => true;

const VariableSelection = ({name, value, onChange, filter = allowAny}) => {
  const formContext = useContext(FormContext);

  let formDefinitionsNames = {};
  formContext.formSteps.map(step => {
    formDefinitionsNames[step.formDefinition || step._generatedId] = step.internalName || step.name;
  });

  const allFormVariables = formContext.staticVariables.concat(formContext.formVariables);
  const choices = allFormVariables
    .filter(variable => filter(variable))
    .map(variable => {
      const label = formDefinitionsNames[variable.formDefinition]
        ? `${formDefinitionsNames[variable.formDefinition]}: ${variable.name} (${variable.key})`
        : `${variable.name} (${variable.key})`;
      return [variable.key, label];
    });

  return <Select name={name} choices={choices} allowBlank onChange={onChange} value={value} />;
};

VariableSelection.propTypes = {
  name: PropTypes.string,
  value: PropTypes.string,
  onChange: PropTypes.func.isRequired,
  filter: PropTypes.func,
};

export default VariableSelection;
