import React, {useContext, useState} from 'react';
import PropTypes from 'prop-types';

import Select from '../../forms/Select';
import {ComponentsContext} from './Context';


const ComponentSelection = ({value, onChange}) => {
    const allComponents = useContext(ComponentsContext);
    const choices = Object.entries(allComponents).map( ([key, comp]) => [key, comp.label || comp.key] )
    return (
        <Select
            name="trigger.component"
            choices={choices}
            allowBlank
            onChange={onChange}
            value={value}
        />
    );
};

ComponentSelection.propTypes = {
    value: PropTypes.string.isRequired,
    onChange: PropTypes.func.isRequired,
};


// TODO: these are the built in json logic operators, but it's possible to define
// custom operators. See https://jsonlogic.com/operations.html
// We start with a minimal supported set based on the user stories (and common sense).
// The data structure is a mapping of the actual json logic operator as key and the
// human readable label as value.
const OPERATORS = {
    '==': 'is equal to',
    '!=': 'is not equal to',
    '>': 'is greater than',
    '>=': 'is greater than or equal to',
    '<': 'is less than',
    '<=': 'is less than or equal to',
    'in': 'in', // array or string (!)
};


// map the Formio component types to allowed operators. Strings cannot be compared
// against each other for >=,>,<,<= etc., so this includes a logical allow-list to only
// show relevant components.
const COMPONENT_TYPE_TO_OPERATORS = {
    number: [
        '==',
        '!=',
        '>',
        '>=',
        '<',
        '<=',
    ],
    textfield: [
        '==',
        '!=',
        'in',
    ],
    iban: [
        '==',
        '!=',
        'in',
    ],
};


const OperatorSelection = ({selectedComponent, operator, onChange}) => {
    // check the component type, which is used to filter the possible choices
    const allComponents = useContext(ComponentsContext);
    const componentType = allComponents[selectedComponent]?.type;

    // only keep the relevant choices
    const allowedOperators = COMPONENT_TYPE_TO_OPERATORS[componentType] || [];
    const choices = Object.entries(OPERATORS).filter(([operator]) => allowedOperators.includes(operator));

    if (!choices.length) {
        return null;
    }

    return (
        <Select
            name="trigger.operator"
            choices={choices}
            allowBlank
            onChange={onChange}
            value={operator}
        />
    );
};

OperatorSelection.propTypes = {
    selectedComponent: PropTypes.string.isRequired,
    operator: PropTypes.string.isRequired,
    onChange: PropTypes.func.isRequired,
};


const Trigger = ({ id }) => {
    const [triggerComponent, setTriggerComponent] = useState('');
    const [operator, setOperator] = useState('');
    const [compareValue, setCompareValue] = useState('');

    const jsonLogic = {
        [operator]: [
            {var: triggerComponent},
            compareValue,
        ],
    };

    return (
        <div style={{padding: '1em'}}>

            When

            <div>
                <ComponentSelection
                    value={triggerComponent}
                    onChange={event => setTriggerComponent(event.target.value)}
                />
                &nbsp;
                <OperatorSelection
                    selectedComponent={triggerComponent}
                    operator={operator}
                    onChange={event => setOperator(event.target.value)}
                />
            </div>

            <div style={{background: '#eee', border: 'dashed 1px #ccc', 'marginTop': '1em'}}>
                jsonLogic:
                <pre>{JSON.stringify(jsonLogic, null, 2)}</pre>
            </div>

        </div>
    );
};

Trigger.propTypes = {
    id: PropTypes.string.isRequired,
};


export default Trigger;
