import React, {useContext} from 'react';
import Select from '../../forms/Select';
import {ACTION_TYPES, ACTIONS_WITH_OPTIONS, MODIFIABLE_PROPERTIES, PROPERTY_VALUES} from './constants';
import ComponentSelection from './ComponentSelection';
import LiteralValueInput from './LiteralValueInput';
import {ComponentsContext} from './Context';
import OperandTypeSelection from './OperandTypeSelection';
import {useImmerReducer} from 'use-immer';


const initialState = {
    actionType: '',
    componentToChange: '',
    componentValueSource: '',
    componentProperty: '',
    componentPropertyValue: '',
    componentVariableValue: '',
    componentLiteralValue: '',
};

const ACTION_SELECTION_ORDER = [
    'actionType',
    'componentToChange',
    'componentValueSource',
    'componentProperty',
    'componentPropertyValue',
    'componentVariableValue',
    'componentLiteralValue',
];


const reducer = (draft, action) => {
    switch(action.type) {
        case 'ACTION_CHANGED': {
            const {name, value} = action.payload;
            draft[name] = value;

            // clear the dependent fields if needed - e.g. if the component changes, all fields to the right change
            const currentFieldIndex = ACTION_SELECTION_ORDER.indexOf(name);
            const nextFieldNames = ACTION_SELECTION_ORDER.slice(currentFieldIndex + 1);
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


const Action = ({}) => {
    const [state, dispatch] = useImmerReducer(reducer, initialState);
    const allComponents = useContext(ComponentsContext);
    const componentType = allComponents[state.componentToChange]?.type;

    const jsonAction = {
        component: state.componentToChange,
        action: {
            type: state.actionType,
            property: {value: state.componentProperty},
            // The data in 'value' needs to be valid jsonLogic
            value: state.componentLiteralValue || {var: state.componentVariableValue},
            state: state.componentPropertyValue,
        }
    };

    const onActionChange = (event) => {
        const {name, value} = event.target;
        dispatch({
            type: 'ACTION_CHANGED',
            payload: {
                name,
                value
            },
        });
    };

    return (
        <div className="action">
            Then,
            <div className="action-choices">
            <Select
                name="actionType"
                choices={ACTION_TYPES}
                allowBlank
                onChange={onActionChange}
                value={state.actionType}
            />
            &nbsp;
            {
                ACTIONS_WITH_OPTIONS.includes(state.actionType) ?
                    <ComponentSelection
                        name="componentToChange"
                        value={state.componentToChange}
                        onChange={onActionChange}
                    /> : null
            }
            {
                state.actionType === 'property' ?
                    <>
                        <Select
                            name="componentProperty"
                            choices={MODIFIABLE_PROPERTIES}
                            allowBlank
                            onChange={onActionChange}
                            value={state.componentProperty}
                        />
                        &nbsp;
                        <Select
                            name="componentPropertyValue"
                            choices={PROPERTY_VALUES}
                            allowBlank
                            onChange={onActionChange}
                            value={state.componentPropertyValue}
                        />
                    </> : null
            }
            {
                state.actionType === 'value' ?
                    <OperandTypeSelection
                        name="componentValueSource"
                        onChange={onActionChange}
                        operandType={state.componentValueSource}
                    /> : null
            }
            {
                state.actionType === 'value' && state.componentValueSource === 'literal' ?
                    <LiteralValueInput
                        name="componentLiteralValue"
                        componentType={componentType}
                        value={state.componentLiteralValue}
                        onChange={onActionChange}
                    /> : null
            }
            {
                state.actionType === 'value' && state.componentValueSource === 'component' ?
                    <ComponentSelection
                        name="componentVariableValue"
                        value={state.componentVariableValue}
                        onChange={event => {
                            const fakeEvent = {target: {name: 'componentLiteralValue', value: ''}};
                            onActionChange(fakeEvent);
                            onActionChange(event);
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
