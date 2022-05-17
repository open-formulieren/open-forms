import React from 'react';

const VariablesEditor = ({variables}) => {
    return (
        <ul>
            {variables.map((variable, index) => (
                <li key={index}>{variable.name}</li>
            ))}
        </ul>
    );
};

export default VariablesEditor;
