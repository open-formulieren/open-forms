import React, {useContext, useState} from 'react';
import PropTypes from 'prop-types';

import Select from '../../forms/Select';

const OPERAND_TYPES = {
    literal: 'value',
    component: 'the field',
};


const OperandTypeSelection = ({name, operandType, onChange}) => {
    const choices = Object.entries(OPERAND_TYPES);
    return (
        <Select
            name={name}
            choices={choices}
            allowBlank
            onChange={onChange}
            value={operandType}
        />
    );
};

OperandTypeSelection.propTypes = {
    name: PropTypes.string.isRequired,
    operandType: PropTypes.oneOf(
        [''].concat(Object.keys(OPERAND_TYPES))
    ).isRequired,
    onChange: PropTypes.func.isRequired,
};

export default OperandTypeSelection;
