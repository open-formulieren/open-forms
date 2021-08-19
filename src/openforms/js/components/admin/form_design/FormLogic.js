import React from 'react';
import PropTypes from 'prop-types';
import FormioUtils from 'formiojs/utils';
import FAIcon from '../FAIcon';
import Trigger from './logic/Trigger';
import {ComponentsContext} from './logic/Context';
import {ActionSet} from './logic/ActionSet';


const EMPTY_RULE = {
    uuid: '',
    form: '',
    jsonLogicTrigger: '',
    actions: [],
};


const FormLogic = ({ logicRules=[], availableComponents={}, onChange, onDelete, onAdd }) => {
    return (
        <ComponentsContext.Provider value={availableComponents}>
            {logicRules.map((rule, i) => (
                <Rule
                    key={i}
                    {...rule}
                    onChange={onChange.bind(null, i)}
                    onDelete={onDelete.bind(null, i)}
                />
            ))}
            <button type="button" onClick={onAdd}>
                Add rule
            </button>
        </ComponentsContext.Provider>
    );
};

FormLogic.propTypes = {
    logicRules: PropTypes.arrayOf(PropTypes.object).isRequired,
    availableComponents: PropTypes.objectOf(
        PropTypes.object, // Formio component objects
    ).isRequired,
    onChange: PropTypes.func.isRequired,
    onDelete: PropTypes.func.isRequired,
    onAdd: PropTypes.func.isRequired,
};


const Rule = ({jsonLogicTrigger, actions, onChange, onDelete}) => {
    const confirmDelete = () => {
        if(window.confirm('Are you sure you want to delete this rule?')){
            onDelete();
        }
    };

    return (
        <div className="logic-rule">

            <Trigger name="jsonLogicTrigger" logic={jsonLogicTrigger} onChange={onChange} />
            <ActionSet name="actions" actions={actions} onChange={onChange} />

            <div className="actions">
                <FAIcon icon="trash" extraClassname="icon icon--danger actions__action" title="Delete" onClick={confirmDelete} />
            </div>
        </div>
    );
};


Rule.propTypes = {
    jsonLogicTrigger: PropTypes.object,
    actions: PropTypes.arrayOf(PropTypes.object),
    onChange: PropTypes.func.isRequired,
    onDelete: PropTypes.func.isRequired,
};

export {FormLogic, EMPTY_RULE};
