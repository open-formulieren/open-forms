import React, {useContext} from 'react';
import PropTypes from 'prop-types';
import {useImmerReducer} from 'use-immer';

import Select from '../../forms/Select';

import {ComponentsContext} from './Context';
import { OPERATORS, COMPONENT_TYPE_TO_OPERATORS } from './constants';
import ComponentSelection from './ComponentSelection';
import LiteralValueInput from './LiteralValueInput';
import OperandTypeSelection from './OperandTypeSelection';


const OperatorSelection = ({name, selectedComponent, operator, onChange}) => {
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
            name={name}
            choices={choices}
            allowBlank
            onChange={onChange}
            value={operator}
        />
    );
};

OperatorSelection.propTypes = {
    name: PropTypes.string.isRequired,
    selectedComponent: PropTypes.string.isRequired,
    operator: PropTypes.string.isRequired,
    onChange: PropTypes.func.isRequired,
};


const initialState = {
    component: '',
    operator: '',
    operandType: '',
    operand: '',
};

const TRIGGER_FIELD_ORDER = [
    'component',
    'operator',
    'operandType',
    'operand',
];

const reducer = (draft, action) => {
    switch(action.type) {
        case 'TRIGGER_CONFIGURATION_CHANGED': {
            const {name, value} = action.payload;
            draft[name] = value;

            // clear the dependent fields if needed - e.g. if the component changes, all fields to the right change
            const currentFieldIndex = TRIGGER_FIELD_ORDER.indexOf(name);
            const nextFieldNames = TRIGGER_FIELD_ORDER.slice(currentFieldIndex + 1);
            for (const name of nextFieldNames) {
                draft[name] = initialState[name];
            }
            break;
        }
        default: {
            throw new Error(`Unknown action type: ${action.type}`);
        }
    }
};

const Trigger = ({ id, name, onChange }) => {
    // hooks
    const [state, dispatch] = useImmerReducer(reducer, initialState);
    const allComponents = useContext(ComponentsContext);

    // event handlers
    const onTriggerChange = (event) => {
        const {name, value} = event.target;
        dispatch({
            type: 'TRIGGER_CONFIGURATION_CHANGED',
            payload: {
                name,
                value
            },
        });
    };

    // rendering logic
    const {
        component: triggerComponent,
        operator,
        operandType,
        operand,
    } = state;

    const componentType = allComponents[triggerComponent]?.type;

    let compareValue = null;
    let valueInput = null;

    switch (operandType) {
        case 'literal': {
            valueInput = (
                <LiteralValueInput
                    name="operand"
                    componentType={componentType}
                    value={operand}
                    onChange={onTriggerChange}
                />
            );
            compareValue = operand;
            break;
        }
        case 'component': {
            valueInput = (
                <ComponentSelection
                    name="operand"
                    value={operand}
                    onChange={onTriggerChange}
                    // filter components of the same type as the trigger component
                    filter={(comp) => (comp.type === componentType)}
                />
            );
            compareValue = {"var": operand};
            break;
        }
        case '': { // nothing selected yet
            break;
        }
        default: {
            throw new Error(`Unknown operand type: ${operandType}`);
        }
    }

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
                    name="component"
                    value={triggerComponent}
                    onChange={onTriggerChange}
                />
                &nbsp;
                {
                    triggerComponent ? (
                        <OperatorSelection
                            name="operator"
                            selectedComponent={triggerComponent}
                            operator={operator}
                            onChange={onTriggerChange}
                        />
                    )
                    : null
                }
                &nbsp;
                { (triggerComponent && operator)
                    ? (<OperandTypeSelection
                        name="operandType"
                        operandType={operandType}
                        onChange={onTriggerChange}
                    /> )
                    : null
                }
                &nbsp;
                { (triggerComponent && operator && operandType)
                    ? valueInput
                    : null
                }
            </div>

            jsonLogic:
            <div style={{background: '#eee', border: 'dashed 1px #ccc', 'marginTop': '1em'}}>
                <pre>{JSON.stringify(jsonLogic, null, 2)}</pre>
            </div>

        </div>
    );
};

Trigger.propTypes = {
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    onChange: PropTypes.func.isRequired,
};


export default Trigger;
