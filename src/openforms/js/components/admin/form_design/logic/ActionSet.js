import React, {useEffect} from 'react';
import {Action} from './Action';
import {useImmerReducer} from "use-immer";
import usePrevious from "react-use/esm/usePrevious";
import isEqual from 'lodash/isEqual';


const emptyAction = {
    actionType: '',
    componentToChange: '',
    componentValueSource: '',
    componentProperty: '',
    componentPropertyValue: '',
    componentVariableValue: '',
    componentLiteralValue: '',
};

const initialState = {
    actions: []
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
            const {name, value, index} = action.payload;
            draft.actions[index][name] = value;

            // clear the dependent fields if needed - e.g. if the component changes, all fields to the right change
            const currentFieldIndex = ACTION_SELECTION_ORDER.indexOf(name);
            const nextFieldNames = ACTION_SELECTION_ORDER.slice(currentFieldIndex + 1);
            for (const name of nextFieldNames) {
                draft.actions[index][name] = emptyAction[name];
            }
            break;
        }
        case 'PROCESS_ACTIONS': {
            let parsedActions = [];
            for (const jsonAction of action.payload) {

                let componentValueSource, componentLiteralValue, componentVariableValue;
                if (jsonAction.action.value.var === undefined) {
                    componentValueSource = 'literal';
                    componentLiteralValue = jsonAction.action.value;
                    componentVariableValue = '';
                } else {
                    if (!jsonAction.action.value.var.length) {
                        componentValueSource = '';
                    } else {
                        componentValueSource = 'component';
                    }
                    componentLiteralValue = '';
                    componentVariableValue = jsonAction.action.value.var;
                }
                if (!!jsonAction.action.source) componentValueSource = jsonAction.action.source;

                parsedActions.push({
                    componentToChange: jsonAction.component,
                    actionType: jsonAction.action.type,
                    componentValueSource: componentValueSource,
                    componentProperty: jsonAction.action.property.value,
                    componentLiteralValue: componentLiteralValue,
                    componentVariableValue: componentVariableValue,
                    componentPropertyValue: jsonAction.action.state,
                });
            }
            draft.actions = parsedActions;
            break;
        }
        case 'ACTION_ADDED': {
            draft.actions.push(emptyAction);
            break;
        }
        case 'ACTION_DELETED': {
            const {index} = action.payload;
            const updatedActions = [...draft.actions];
            updatedActions.splice(index, 1);
            draft.actions = updatedActions;
            break;
        }
        default: {
            throw new Error(`Unknown action type: ${action.type}`);
        }
    }
};

const convertActionToJson = (action) => {
        return {
            component: action.componentToChange,
            action: {
                type: action.actionType,
                property: {value: action.componentProperty},
                // The data in 'value' needs to be valid jsonLogic
                value: action.componentLiteralValue || {var: action.componentVariableValue},
                state: action.componentPropertyValue,
                // Selecting if the new component value should come from a literal or another component doesn't
                // change anything in the JSON, only entering the literal or picking the component does.
                // So, this 'source' attribute is here only to keep track of the value for the OperandTypeSelection
                // dropdown, but is not used in the backend
                source: action.componentValueSource
        }
    };
};

const ActionSet = ({name, actions, onChange}) => {
    const [state, dispatch] = useImmerReducer(reducer, {...initialState, actions: actions || []});

    // whenever we get a change in the actions, relay that back to the
    // parent component
    const previousActions = usePrevious(actions);
    useEffect(
        () => {
            // if nothing changed, do not fire an update
            if (!(previousActions && isEqual(previousActions, actions))) return;
            onChange({
                target: {
                    name: name,
                    value: actions.map((action, index) => convertActionToJson(action)),
                }
            });
        },
        [actions]
    );

    // Parse the actions (expressed in JSON) to the variables that can be handled in the state
    useEffect(
        () => dispatch({
            type: 'PROCESS_ACTIONS',
            payload: actions,
        }),
        [actions]
    );

    const onActionChange = (index, event) => {
        const {name, value} = event.target;
        dispatch({
            type: 'ACTION_CHANGED',
            payload: {
                name,
                value,
                index
            },
        });
    };

    const onActionDelete = (index) => {
        dispatch({
            type: 'ACTION_DELETED',
            payload: {index: index}
        });
    };

    return (
        <>
            {state.actions.map((action, index) => (
                <Action
                    key={index}
                    action={action}
                    onChange={onActionChange.bind(null, index)}
                    onDelete={onActionDelete.bind(null, index)}
                />
            ))}
            <button type="button" onClick={ () => dispatch({type: 'ACTION_ADDED'}) }>
                Add action
            </button>
        </>
    );
};

export {ActionSet};
