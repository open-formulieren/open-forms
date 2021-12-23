import React from 'react';
import PropTypes from 'prop-types';


const ALL_COMPONENTS = [
    {
        type: 'textfield',
        key: 'text1',
        label: 'Textfield 1',
        stepLabel: 'Stap 1',
    },
    {
        type: 'textfield',
        key: 'text2',
        label: 'Textfield 2',
        stepLabel: 'Stap 2',
    },
    {
        type: 'select',
        key: 'select1',
        label: 'Dropdown',
        stepLabel: 'Stap 2',
    },
];



const SelectProcessVariables = ({ onChange }) => {
    return (
        null
    );
};

SelectProcessVariables.propTypes = {
    onChange: PropTypes.func.isRequired,
};


export default SelectProcessVariables;
