import React, {useContext, useState} from 'react';
import PropTypes from 'prop-types';
import {defineMessage, useIntl} from 'react-intl';

import {getTranslatedChoices} from '../../../../utils/i18n'
import Select from '../../forms/Select';

const OPERAND_TYPES = {
    literal: defineMessage({description: '"literal" operand type', defaultMessage: 'value'}),
    component: defineMessage({description: '"component" operand type', defaultMessage: 'the field'}),
};


const OperandTypeSelection = ({name, operandType, onChange}) => {
    const intl = useIntl();
    return (
        <Select
            name={name}
            choices={getTranslatedChoices(intl, OPERAND_TYPES)}
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
