import React, {useContext} from 'react';
import PropTypes from 'prop-types';
import {useIntl} from 'react-intl';

import { PrefixContext } from './Context';
import {getTranslatedChoices} from '../../../utils/i18n';


const BLANK_OPTION = ['', '------'];


const Select = ({ name='select', choices, allowBlank=false, translateChoices=false, ...extraProps }) => {
    // normalize to array of choices
    if (!Array.isArray(choices)) {
        choices = Object.entries(choices);
    }

    const intl = useIntl();
    if (translateChoices) {
        choices = choices.map(([value, msg]) => [value, intl.formatMessage(msg)]);
    }

    const prefix = useContext(PrefixContext);
    name = prefix ? `${prefix}-${name}` : name;
    const options = allowBlank ? [BLANK_OPTION].concat(choices) : choices;

    return (
        <select name={name} {...extraProps}>
        {
            options.map(([value, label]) => (
                <option value={value} key={value}>{label}</option>
            ))
        }
        </select>
    );
};


const Message = PropTypes.shape({
    id: PropTypes.string,
    defaultMessage: PropTypes.oneOfType([
        PropTypes.string,
        PropTypes.object,
        PropTypes.array,
    ]),
});


const Label = PropTypes.oneOfType([
    PropTypes.string,
    Message,
]);


Select.propTypes = {
    name: PropTypes.string, // typically injected by the wrapping <Field> component
    allowBlank: PropTypes.bool,
    choices: PropTypes.oneOfType([
        PropTypes.arrayOf(PropTypes.arrayOf(PropTypes.string)),
        PropTypes.arrayOf(PropTypes.arrayOf(Label)),
        PropTypes.objectOf(Label),
    ]).isRequired,
    translateChoices: PropTypes.bool,
};


export default Select;
