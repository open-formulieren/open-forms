import React from 'react';
import {useImmerReducer} from 'use-immer';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';
import _ from 'lodash';

import ButtonContainer from '../../../forms/ButtonContainer';
import Action from './Action';
import {useOnChanged} from '../hooks';


const EMPTY_ACTION = {
    component: '',
    formStep: '',
    action: {
        type: '',
        property: {type: '', value: ''},
        value: '',
        state: '',
    },
};


const ACTION_SELECTION_ORDER = [
    'action.type',
    'formStep',
    'component',
    'action.property',
    'action.state',
    'action.value',
];


const reducer = (draft, action) => {
    switch(action.type) {
        case 'ACTION_CHANGED': {
            const {value, name, index} = action.payload;
            _.set(draft.actions[index], name, value);

            // clear the dependent fields if needed - e.g. if the component changes, all fields to the right change
            if (ACTION_SELECTION_ORDER.includes(name)) {
                const currentFieldIndex = ACTION_SELECTION_ORDER.indexOf(name);
                const nextFieldNames = ACTION_SELECTION_ORDER.slice(currentFieldIndex + 1);
                let emptyValue;
                for (const name of nextFieldNames) {
                    emptyValue = _.get(EMPTY_ACTION, name);
                    _.set(draft.actions[index], name, emptyValue);
                }
            }
            break;
        }
        case 'ACTION_ADDED': {
            draft.actions.push(EMPTY_ACTION);
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


const ActionSet = ({name, actions, onChange}) => {
    const [state, dispatch] = useImmerReducer(reducer, {
        actions: actions || []
    });

    useOnChanged(
        state.actions,
        () => onChange({target: {name, value: state.actions}}),
    );

    const onActionChange = (index, event) => {
        const {name, value} = event.target;
        dispatch({
            type: 'ACTION_CHANGED',
            payload: {index, name, value},
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
    actions: PropTypes.arrayOf(PropTypes.object),
    onChange: PropTypes.func.isRequired,
};


export default ActionSet;
