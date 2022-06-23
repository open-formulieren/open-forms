import React, {useContext} from 'react';
import PropTypes from 'prop-types';

import Select from './Select';
import {FormContext} from '../form_design/Context';

const allowAny = () => true;

const ComponentSelection = ({name, value, onChange, filter = allowAny}) => {
  const formContext = useContext(FormContext);
  const allComponents = formContext.components;
  const choices = Object.entries(allComponents)
    // turn components map of {key: component} into choices list [key, component]
    .map(([key, comp]) => [key, comp.stepLabel || comp.label || comp.key])
    // apply passed in filter to restrict valid choices
    .filter(([key]) => filter(allComponents[key]));

  return <Select name={name} choices={choices} allowBlank onChange={onChange} value={value} />;
};

ComponentSelection.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  filter: PropTypes.func,
};

export default ComponentSelection;
