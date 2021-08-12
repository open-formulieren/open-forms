import React, {useContext, useState} from 'react';
import PropTypes from 'prop-types';

import Select from '../../forms/Select';

import {ComponentsContext} from './Context';
import { OPERATORS, COMPONENT_TYPE_TO_OPERATORS } from './constants';
import ComponentSelection from './ComponentSelection';
import LiteralValueInput from './LiteralValueInput';
import OperandTypeSelection from './OperandTypeSelection';


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


const Trigger = ({ id, name, onChange }) => {
    const [triggerComponent, setTriggerComponent] = useState('');
    const [operator, setOperator] = useState('');
    const [compareValue, setCompareValue] = useState('');
    const [operandType, setOperandType] = useState('');
    const [literalValue, setLiteralValue] = useState('');
    const [componentValue, setComponentValue] = useState('');

    const allComponents = useContext(ComponentsContext);
    const componentType = allComponents[triggerComponent]?.type;

    let valueInput = null;

    switch (operandType) {
        case 'literal': {
            valueInput = (
                <LiteralValueInput
                    name="trigger.literalValue"
                    componentType={componentType}
                    value={literalValue}
                    onChange={event => {
                        const {value} = event.target;
                        setLiteralValue(value);
                        setCompareValue(value);
                    }} />
            );
            break;
        }
        case 'component': {
            valueInput = (
                <ComponentSelection
                    name="trigger.componentValue"
                    value={componentValue}
                    onChange={event => {
                        const {value: componentKey} = event.target;
                        setComponentValue(componentKey);
                        setCompareValue({"var": componentKey});
                    }}
                    // filter components of the same type as the trigger component
                    filter={(comp) => (comp.type === componentType)}
                />
            );
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
                    name="trigger.component"
                    value={triggerComponent}
                    onChange={event => setTriggerComponent(event.target.value)}
                />
                &nbsp;
                {
                    triggerComponent ? (
                        <OperatorSelection
                            selectedComponent={triggerComponent}
                            operator={operator}
                            onChange={event => setOperator(event.target.value)}
                        />
                    )
                    : null
                }
                &nbsp;
                { (triggerComponent && operator)
                    ? (<OperandTypeSelection
                        name="trigger.operandType"
                        operandType={operandType}
                        onChange={event => setOperandType(event.target.value)}
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
