import React, {useContext, useState} from 'react';
import Select from '../../forms/Select';
import {ACTION_TYPES, ACTIONS_WITH_OPTIONS, MODIFIABLE_PROPERTIES, PROPERTY_VALUES} from './constants';
import ComponentSelection from './ComponentSelection';
import LiteralValueInput from './LiteralValueInput';
import {ComponentsContext} from './Context';
import OperandTypeSelection from "./OperandTypeSelection";

const Action = ({}) => {
    const [actionType, setActionType] = useState('');
    // componentToChange should change a field directly on the Rule and not the action
    const [componentToChange, setComponentToChange] = useState('');
    const [valueSource, setValueSource] = useState('');
    const [componentProperty, setComponentProperty] = useState('');
    const [componentPropertyValue, setComponentPropertyValue] = useState('');
    const [componentValueSource, setComponentValueSource] = useState('');
    const [componentValue, setComponentValue] = useState('');

    const allComponents = useContext(ComponentsContext);
    const componentType = allComponents[componentToChange]?.type;

    const jsonAction = {
        component: componentToChange,
        action: {
            type: actionType,
            property: {value: componentProperty},
            // The data in 'value' needs to be valid jsonLogic
            value: componentValue || {var: componentValueSource},
            state: componentPropertyValue,
        }
    };

    return (
        <div className="action">
            Then,
            <div className="action-choices">
            <Select
                name="actionType"
                choices={ACTION_TYPES}
                allowBlank
                onChange={event => setActionType(event.target.value)}
                value={actionType}
            />
            &nbsp;
            {
                ACTIONS_WITH_OPTIONS.includes(actionType) ?
                    <ComponentSelection
                        name="componentToChange"
                        value={componentToChange}
                        onChange={event => {
                            setComponentToChange(event.target.value);
                        }}
                    /> : null
            }
            {
                actionType === 'property' ?
                    <>
                        <Select
                            name="componentProperty"
                            choices={MODIFIABLE_PROPERTIES}
                            allowBlank
                            onChange={event => setComponentProperty(event.target.value)}
                            value={componentProperty}
                        />
                        &nbsp;
                        <Select
                            name="componentPropertyValue"
                            choices={PROPERTY_VALUES}
                            allowBlank
                            onChange={event => setComponentPropertyValue(event.target.value)}
                            value={componentPropertyValue}
                        />
                    </> : null
            }
            {
                actionType === 'value' ?
                    <OperandTypeSelection
                        name="actionValueSource"
                        onChange={event => setValueSource(event.target.value)}
                        operandType={valueSource}
                    /> : null
            }
            {
                actionType === 'value' && valueSource === 'literal' ?
                    <LiteralValueInput
                        name="componentLiteralValue"
                        componentType={componentType}
                        value={componentValue}
                        onChange={event => setComponentValue(event.target.value)}
                    /> : null
            }
            {
                actionType === 'value' && valueSource === 'component' ?
                    <ComponentSelection
                        name="componentValueSource"
                        value={componentValueSource}
                        onChange={event => {
                            setComponentValue('');
                            setComponentValueSource(event.target.value);
                        }}
                        filter={(comp) => (comp.type === componentType)}
                    /> : null
            }
            </div>
            Action:
            <div style={{background: '#eee', border: 'dashed 1px #ccc', 'marginTop': '1em'}}>
                <pre>{JSON.stringify(jsonAction, null, 2)}</pre>
            </div>
        </div>
    );
};

export {Action};
