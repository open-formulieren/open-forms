import React from 'react';
import PropTypes from 'prop-types';
import {defineMessage, useIntl} from 'react-intl';

import {getTranslatedChoices} from '../../../../utils/i18n';
import Select from '../../forms/Select';

const OPERAND_TYPES = {
    literal: defineMessage({description: '"literal" operand type', defaultMessage: 'value'}),
    component: defineMessage({description: '"component" operand type', defaultMessage: 'the field'}),
    today: defineMessage({description: '"today" operand type', defaultMessage: 'today'})
};

const COMPONENT_TYPE_TO_OPERAND_TYPE = {
    number: {
        literal: OPERAND_TYPES.literal,
        component: OPERAND_TYPES.component,
    },
    textfield: {
        literal: OPERAND_TYPES.literal,
        component: OPERAND_TYPES.component,
    },
    iban: {
        literal: OPERAND_TYPES.literal,
        component: OPERAND_TYPES.component,
    },
    date: {...OPERAND_TYPES},
};


const OperandTypeSelection = ({name, operandType, componentType, onChange}) => {
    const intl = useIntl();
    const choices = Object.entries(COMPONENT_TYPE_TO_OPERAND_TYPE[componentType]);
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
    operandType: PropTypes.oneOf(
        [''].concat(Object.keys(OPERAND_TYPES))
    ).isRequired,
    componentType: PropTypes.string.isRequired,
    onChange: PropTypes.func.isRequired,
};

export default OperandTypeSelection;
