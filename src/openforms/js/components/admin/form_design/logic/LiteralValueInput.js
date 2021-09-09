import React from 'react';
import PropTypes from 'prop-types';

import {TextInput, NumberInput, DateInput} from '../../forms/Inputs';

const COMPONENT_TYPE_TO_INPUT_TYPE = {
    number: NumberInput,
    textfield: TextInput,
    iban: TextInput,
    date: DateInput,
};

const LiteralValueInput = ({name, componentType, value='', onChange, ...extraProps}) => {
    const InputComponent = COMPONENT_TYPE_TO_INPUT_TYPE[componentType] || TextInput;

    const onInputChange = (event) => {
        const inputValue = event.target.value;
        let value;

        // do any input type conversions if needed, e.g. date to native datetime/ISO-8601 format
        switch (componentType) {
            case 'number': {
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
            }
        });
    };

    return (
        <InputComponent
            name={name}
            value={value}
            onChange={onInputChange}
            {...extraProps}
        />
    );
};

LiteralValueInput.propTypes = {
    name: PropTypes.string.isRequired,
    componentType: PropTypes.string.isRequired,
    value: PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.number,
    ]),
    onChange: PropTypes.func.isRequired,
};

export default LiteralValueInput;
