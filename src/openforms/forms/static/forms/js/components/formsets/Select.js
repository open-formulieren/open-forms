import React, {useContext} from 'react';
import PropTypes from 'prop-types';

import { PrefixContext } from './Context';


const BLANK_OPTION = ['', '------'];


const Select = ({ name, choices, allowBlank=false, ...extraProps }) => {
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


Select.propTypes = {
    name: PropTypes.string.isRequired,
    allowBlank: PropTypes.bool,
    choices: PropTypes.arrayOf(
        PropTypes.arrayOf(PropTypes.string),
    ).isRequired,
};


export default Select;
