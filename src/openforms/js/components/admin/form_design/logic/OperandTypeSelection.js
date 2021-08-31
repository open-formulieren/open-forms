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


const OperandTypeSelection = ({name, operandType, onChange, filter}) => {
    const intl = useIntl();
    let choices = Object.entries(OPERAND_TYPES).map(
        ([operandType, msg]) => [operandType, intl.formatMessage(msg)]
    );
    if (filter) {
        choices = choices.filter(filter);
    }
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
    onChange: PropTypes.func.isRequired,
    filter: PropTypes.func,
};

export default OperandTypeSelection;
