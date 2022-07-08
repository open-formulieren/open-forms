import React, {useContext} from 'react';
import PropTypes from 'prop-types';

import Select from '../forms/Select';
import {FormContext} from './Context';

const StepSelection = ({name, value, onChange}) => {
  const formContext = useContext(FormContext);
  const formSteps = formContext.formSteps;
  const formStepChoices = formSteps.map((step, index) => [
    step.url,
    step.internalName || step.name,
  ]);

  return (
    <Select name={name} choices={formStepChoices} allowBlank onChange={onChange} value={value} />
  );
};

StepSelection.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.string,
  onChange: PropTypes.func,
};

export default StepSelection;
