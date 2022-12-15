import PropTypes from 'prop-types';
import React from 'react';
import {defineMessage, useIntl} from 'react-intl';

import Select from 'components/admin/forms/Select';
import {getTranslatedChoices} from 'utils/i18n';

const OPERAND_TYPES = {
  literal: defineMessage({description: '"literal" operand type', defaultMessage: 'value'}),
  variable: defineMessage({description: '"variable" operand type', defaultMessage: 'the variable'}),
  today: defineMessage({description: '"today" operand type', defaultMessage: 'today'}),
  array: defineMessage({description: '"array" operand type', defaultMessage: 'the array'}),
};

const allowAny = () => true;

const OperandTypeSelection = ({name, operandType, onChange, filter = allowAny}) => {
  const intl = useIntl();
  const choices = getTranslatedChoices(intl, OPERAND_TYPES);

  return (
    <Select
      name={name}
      choices={choices.filter(filter)}
      allowBlank
      onChange={onChange}
      value={operandType}
    />
  );
};

OperandTypeSelection.propTypes = {
  name: PropTypes.string.isRequired,
  operandType: PropTypes.oneOf([''].concat(Object.keys(OPERAND_TYPES))).isRequired,
  onChange: PropTypes.func.isRequired,
  filter: PropTypes.func,
};

export default OperandTypeSelection;
