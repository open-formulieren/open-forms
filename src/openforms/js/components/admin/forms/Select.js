import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import {PrefixContext} from './Context';

const BLANK_OPTION = [['', '------']];
export const LOADING_OPTION = [
  [
    '...',
    <FormattedMessage defaultMessage="loading..." description="Loading select option label" />,
  ],
];

const capfirst = text => `${text[0].toUpperCase()}${text.slice(1)}`;

const Select = ({
  name = 'select',
  choices,
  allowBlank = false,
  translateChoices = false,
  capfirstChoices = false,
  ...extraProps
}) => {
  // normalize to array of choices
  if (!Array.isArray(choices)) {
    choices = Object.entries(choices);
  }

  const intl = useIntl();
  if (translateChoices) {
    choices = choices.map(([value, msg]) => [value, intl.formatMessage(msg)]);
  }
  if (capfirstChoices) {
    choices = choices.map(([value, label]) => [value, capfirst(label)]);
  }

  const prefix = useContext(PrefixContext);
  name = prefix ? `${prefix}-${name}` : name;
  const options = allowBlank ? BLANK_OPTION.concat(choices) : choices;

  extraProps.value = extraProps.value || '';

  return (
    <select name={name} {...extraProps}>
      {options.map(([value, label]) => (
        <option value={value} key={value}>
          {label}
        </option>
      ))}
    </select>
  );
};

const Message = PropTypes.shape({
  id: PropTypes.string,
  defaultMessage: PropTypes.oneOfType([PropTypes.string, PropTypes.object, PropTypes.array]),
});

const Label = PropTypes.oneOfType([PropTypes.string, Message]);
const Value = PropTypes.oneOfType([PropTypes.string, PropTypes.number]);

// Not excatly the 2-tuple we mean, but hey...
const Choice = PropTypes.arrayOf(PropTypes.oneOfType([Value, Label]));

export const SelectChoicesType = PropTypes.oneOfType([
  PropTypes.arrayOf(Choice),
  PropTypes.objectOf(Label),
]);

Select.propTypes = {
  name: PropTypes.string, // typically injected by the wrapping <Field> component
  allowBlank: PropTypes.bool,
  choices: SelectChoicesType.isRequired,
  translateChoices: PropTypes.bool,
};

export default Select;
