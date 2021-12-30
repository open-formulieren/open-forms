import React from 'react';
import {useImmerReducer} from 'use-immer';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import ButtonContainer from '../../forms/ButtonContainer';
import Action from './Action';
import {useOnChanged} from './hooks';


const emptyAction = {
    actionType: '',
    stepToChange: '',
    componentToChange: '',
    componentValueSource: '',
    componentProperty: '',
    componentPropertyType: '',
    componentPropertyValue: '',
    componentVariableValue: '',
    componentLiteralValue: '',
};

const initialState = {
    actions: []
};

const ACTION_SELECTION_ORDER = [
    'actionType',
    'stepToChange',
    'componentToChange',
    'componentValueSource',
    'componentProperty',
    'componentPropertyType',
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

const convertActionToJson = (action) => {
    return {
        component: action.componentToChange,
        formStep: action.stepToChange,
        action: {
            type: action.actionType,
            property: {value: action.componentProperty, type: action.componentPropertyType},
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

const parseJsonAction = (jsonAction) => {
    let componentValueSource = '',
        componentLiteralValue,
        componentVariableValue;

    const { value } = jsonAction.action;

    if (value != null) {
        const actionVar = value?.var;
        if (actionVar == null) {
            componentValueSource = 'literal';
            componentLiteralValue = value;
            componentVariableValue = '';
        } else {
            if (actionVar.length) {
                componentValueSource = 'component';
            }
            componentLiteralValue = '';
            componentVariableValue = actionVar;
        }
    }

    if (!!jsonAction.action.source) componentValueSource = jsonAction.action.source;

    return {
        componentToChange: jsonAction.component,
        actionType: jsonAction.action.type,
        componentValueSource: componentValueSource,
        componentProperty: jsonAction.action.property?.value,
        componentLiteralValue: componentLiteralValue,
        componentVariableValue: componentVariableValue,
        componentPropertyValue: jsonAction.action.state,
        componentPropertyType: jsonAction.action.property?.type,
        stepToChange: jsonAction.formStep,
    };
};

const ActionSet = ({name, actions, onChange}) => {
    const [state, dispatch] = useImmerReducer(reducer, {
        ...initialState,
        actions: actions.map(action => parseJsonAction(action)) || []
    });

    const jsonActions = state.actions.map(action => convertActionToJson(action));
    useOnChanged(
        jsonActions,
        () => onChange({target: {name, value: jsonActions}}),
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

    const firstActionPrefix = (<FormattedMessage description="First logic action prefix" defaultMessage="Then" />);
    const extraActionPrefix = (<FormattedMessage description="Extra logic action prefix" defaultMessage="and" />);
    return (
        <>
            {state.actions.map((action, index) => (
                <Action
                    key={index}
                    prefixText={index === 0 ? firstActionPrefix : extraActionPrefix }
                    action={action}
                    onChange={onActionChange.bind(null, index)}
                    onDelete={() => dispatch({type: 'ACTION_DELETED', payload: {index}})}
                />
            ))}
            <ButtonContainer onClick={ () => dispatch({type: 'ACTION_ADDED'}) }>
                <FormattedMessage description="Add form logic rule action button" defaultMessage="Add action" />
            </ButtonContainer>
        </>
    );
};

ActionSet.propTypes = {
    name: PropTypes.string.isRequired,
    actions: PropTypes.arrayOf(PropTypes.object).isRequired,
    onChange: PropTypes.func.isRequired,
};

export default ActionSet;
