import React from 'react';
import PropTypes from 'prop-types';
import {useIntl} from 'react-intl';

import DeleteIcon from '../DeleteIcon';
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
    const intl = useIntl();
    const deleteConfirmMessage = intl.formatMessage({
        description: 'Logic rule deletion confirm message',
        defaultMessage: 'Are you sure you want to delete this rule?',
    });
    return (
        <div className="logic-rule">
            <Trigger name="jsonLogicTrigger" logic={jsonLogicTrigger} onChange={onChange} />
            <ActionSet name="actions" actions={actions} onChange={onChange} />
            <div className="actions">
                <DeleteIcon onConfirm={onDelete} message={deleteConfirmMessage} />
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
