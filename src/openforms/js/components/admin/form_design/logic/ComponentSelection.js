import React, {useContext} from 'react';
import PropTypes from 'prop-types';

import Select from '../../forms/Select';
import {ComponentsContext} from './Context';


const ComponentSelection = ({name, value, onChange}) => {
    const allComponents = useContext(ComponentsContext);
    const choices = Object.entries(allComponents).map( ([key, comp]) => [key, comp.label || comp.key] )
    return (
        <Select
            name={name}
            choices={choices}
            allowBlank
            onChange={onChange}
            value={value}
        />
    );
};

ComponentSelection.propTypes = {
    name: PropTypes.string.isRequired,
    value: PropTypes.string.isRequired,
    onChange: PropTypes.func.isRequired,
};

export default ComponentSelection;
