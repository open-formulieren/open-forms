import React, {useContext} from 'react';
import Select from '../../forms/Select';
import {ACTION_TYPES, ACTIONS_WITH_OPTIONS, MODIFIABLE_PROPERTIES, PROPERTY_VALUES} from './constants';
import ComponentSelection from './ComponentSelection';
import LiteralValueInput from './LiteralValueInput';
import {ComponentsContext} from './Context';
import OperandTypeSelection from './OperandTypeSelection';
import FAIcon from "../../FAIcon";


const Action = ({action, onChange, onDelete}) => {
    const allComponents = useContext(ComponentsContext);
    const componentType = allComponents[action.componentToChange]?.type;

    const jsonAction = {
        component: action.componentToChange,
        action: {
            type: action.actionType,
            property: {value: action.componentProperty},
            // The data in 'value' needs to be valid jsonLogic
            value: action.componentLiteralValue || {var: action.componentVariableValue},
            state: action.componentPropertyValue,
        }
    };

    const confirmDelete = (index) => {
        if(window.confirm('Are you sure you want to delete this action?')){
            onDelete(index);
        }
    };


    return (
        <div className="action">
            <div className="actions">
                <FAIcon icon="trash" extraClassname="icon icon--danger actions__action" title="Delete" onClick={confirmDelete} />
            </div>
            Then,
            <div className="action-choices">
            <Select
                name="actionType"
                choices={ACTION_TYPES}
                allowBlank
                onChange={onChange}
                value={action.actionType}
            />
            &nbsp;
            {
                ACTIONS_WITH_OPTIONS.includes(action.actionType) ?
                    <ComponentSelection
                        name="componentToChange"
                        value={action.componentToChange}
                        onChange={onChange}
                    /> : null
            }
            {
                action.actionType === 'property' ?
                    <>
                        <Select
                            name="componentProperty"
                            choices={MODIFIABLE_PROPERTIES}
                            allowBlank
                            onChange={onChange}
                            value={action.componentProperty}
                        />
                        &nbsp;
                        <Select
                            name="componentPropertyValue"
                            choices={PROPERTY_VALUES}
                            allowBlank
                            onChange={onChange}
                            value={action.componentPropertyValue}
                        />
                    </> : null
            }
            {
                // Used to pick whether the new value of a component will be a literal or a value from another component
                action.actionType === 'value' ?
                    <OperandTypeSelection
                        name="componentValueSource"
                        onChange={onChange}
                        operandType={action.componentValueSource}
                    /> : null
            }
            {
                action.actionType === 'value' && action.componentValueSource === 'literal' ?
                    <LiteralValueInput
                        name="componentLiteralValue"
                        componentType={componentType}
                        value={action.componentLiteralValue}
                        onChange={onChange}
                    /> : null
            }
            {
                action.actionType === 'value' && action.componentValueSource === 'component' ?
                    <ComponentSelection
                        name="componentVariableValue"
                        value={action.componentVariableValue}
                        onChange={event => {
                            const fakeEvent = {target: {name: 'componentLiteralValue', value: ''}};
                            onChange(fakeEvent);
                            onChange(event);
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
