import React from 'react';
import PropTypes from 'prop-types';

import {TextInput, NumberInput, DateInput} from 'components/admin/forms/Inputs';
import {COMPONENT_DATATYPES} from 'components/admin/form_design/variables/constants';

const TYPE_TO_INPUT_TYPE = {
  float: NumberInput,
  string: TextInput,
  datetime: DateInput,
};

const LiteralValueInput = ({name, type, value = '', onChange, ...extraProps}) => {
  const InputComponent = TYPE_TO_INPUT_TYPE[type] || TextInput;

  const onInputChange = event => {
    const inputValue = event.target.value;
    let value;

    // do any input type conversions if needed, e.g. date to native datetime/ISO-8601 format
    switch (type) {
      case COMPONENT_DATATYPES.number: {
        value = Number.parseFloat(inputValue);
        break;
      }
      default:
        value = inputValue;
    }

    onChange({
      target: {
        name: event.target.name,
        value: value,
      },
    });
  };

  return <InputComponent name={name} value={value} onChange={onInputChange} {...extraProps} />;
};

LiteralValueInput.propTypes = {
  name: PropTypes.string.isRequired,
  type: PropTypes.string,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  onChange: PropTypes.func.isRequired,
};

export default LiteralValueInput;
