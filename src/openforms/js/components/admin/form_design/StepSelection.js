import React, {useContext} from 'react';
import PropTypes from 'prop-types';

import Select from '../forms/Select';
import {FormContext} from './Context';

const getStepDisplayName = step => step.internalName || step.name;

const StepSelection = ({name, value, onChange}) => {
  const formContext = useContext(FormContext);
  const formSteps = formContext.formSteps;
  const formStepChoices = formSteps.map((step, index) => [step.url, getStepDisplayName(step)]);

  return (
    <Select name={name} choices={formStepChoices} allowBlank onChange={onChange} value={value} />
  );
};

StepSelection.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.string,
  onChange: PropTypes.func,
};

const useFormStep = (formStepUrl = '') => {
  const formContext = useContext(FormContext);
  const formSteps = formContext.formSteps;
  if (!formStepUrl) return null;

  // look up the step from the array of steps in the context
  const step = formSteps.find(element => element.url == formStepUrl);
  return {
    step,
    stepName: getStepDisplayName(step),
  };
};

export default StepSelection;
export {useFormStep, StepSelection};
