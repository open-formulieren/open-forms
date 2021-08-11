import React, {useContext} from 'react';
import PropTypes from 'prop-types';

import { PrefixContext } from './Context';

const Input = ({type="text", name, ...extraProps}) => {
    const prefix = useContext(PrefixContext);
    name = prefix ? `${prefix}-${name}` : name;
    return (
        <input type={type} name={name} {...extraProps} />
    );
};

Input.propTypes = {
    type: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
};

const TextInput = (props) => (<Input type="text" {...props} />);

const NumberInput = (props) => (<Input type="number" {...props} />);

const Checkbox = ({ name, label, helpText, ...extraProps }) => {
    const prefix = useContext(PrefixContext);
    name = prefix ? `${prefix}-${name}` : name;
    const idFor = `id_${name}`;
    return (
        <div className="checkbox-row">
            <input
                type="checkbox"
                name={name}
                id={idFor}
                {...extraProps}
            />
            <label className="vCheckboxLabel inline" htmlFor={idFor}>{label}</label>
            { helpText ? <div className="help">{helpText}</div> : null }
        </div>
    );
};

Checkbox.propTypes = {
    name: PropTypes.string.isRequired,
    label: PropTypes.node.isRequired,
    helpText: PropTypes.node,
};

export { Input, TextInput, NumberInput, Checkbox };
