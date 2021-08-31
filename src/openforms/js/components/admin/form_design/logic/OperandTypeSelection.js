import React from 'react';
import PropTypes from 'prop-types';
import {defineMessage, useIntl} from 'react-intl';

import {getTranslatedChoices} from '../../../../utils/i18n';
import Select from '../../forms/Select';

const OPERAND_TYPES = {
    literal: defineMessage({description: '"literal" operand type', defaultMessage: 'value'}),
    component: defineMessage({description: '"component" operand type', defaultMessage: 'the field'}),
    today: defineMessage({description: '"today" operand type', defaultMessage: 'today'}),
    array: defineMessage({description: '"array" operand type', defaultMessage: 'the array'}),
};

const COMPONENT_TYPE_TO_OPERAND_TYPE = {
    number: {
        literal: OPERAND_TYPES.literal,
        component: OPERAND_TYPES.component,
    },
    textfield: {
        literal: OPERAND_TYPES.literal,
        component: OPERAND_TYPES.component,
        array: OPERAND_TYPES.array,
    },
    iban: {
        literal: OPERAND_TYPES.literal,
        component: OPERAND_TYPES.component,
    },
    date: {...OPERAND_TYPES},
};


const OperandTypeSelection = ({name, operandType, operator, componentType, onChange}) => {
    const intl = useIntl();
    const choices = Object.entries(COMPONENT_TYPE_TO_OPERAND_TYPE[componentType]).filter(
        // we only want to compare with an array of values if the operator is 'in'
        ([literalValueType, msg]) => {
            if (operator === 'in') return true;
            return operator !== 'in' && literalValueType !== 'array';
        }
    ).map(
        ([operandType, msg]) => [operandType, intl.formatMessage(msg)]
    );
    return (
        <Select
            name={name}
            choices={getTranslatedChoices(intl, choices)}
            allowBlank
            onChange={onChange}
            value={operandType}
        />
    );
};

OperandTypeSelection.propTypes = {
    name: PropTypes.string.isRequired,
    operator: PropTypes.string,
    operandType: PropTypes.oneOf(
        [''].concat(Object.keys(OPERAND_TYPES))
    ).isRequired,
    componentType: PropTypes.string.isRequired,
    onChange: PropTypes.func.isRequired,
};

export default OperandTypeSelection;
