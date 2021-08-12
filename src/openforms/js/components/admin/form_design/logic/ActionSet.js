import React from 'react';
import {Action} from './Action';
import {useImmerReducer} from "use-immer";

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

const ActionSet = ({actions}) => {
    const [state, dispatch] = useImmerReducer(reducer, {...initialState, actions: actions});

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
