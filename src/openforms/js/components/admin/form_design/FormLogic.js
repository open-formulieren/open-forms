import React from 'react';
import PropTypes from 'prop-types';
import FormioUtils from 'formiojs/utils';
import FAIcon from '../FAIcon';
import Trigger from './logic/Trigger';
import {ComponentsContext} from './logic/Context';
import {ActionSet} from "./logic/ActionSet";


const EMPTY_RULE = {
    uuid: '',
    formStep: '',
    jsonLogicTrigger: '',
    component: '',
    actions: [],
};


const formatRuleComponentChoices = (formSteps, dispatch, eventType) => {
    const allComponents = formSteps.map(
        step => FormioUtils.flattenComponents(step.configuration.components || [], false)
    ).reduce((acc, currentValue) => ({...acc, ...currentValue}), {});
    dispatch({
        type: eventType,
        payload: allComponents,
    });
};


const FormLogic = ({ rules, onChange, onDelete, onAdd }) => {

    return (
        <ComponentsContext.Provider value={rules.components.choices}>
            {rules.rules.map((rule, i) => (
                <Rule
                    key={i}
                    {...rule}
                    components={rules.components}
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

// FormLogic.propTypes = {
//     formSteps: PropTypes.arrayOf(PropTypes.object).isRequired,
// };


const Rule = ({jsonLogicTrigger, actions, onChange, onDelete}) => {
    const confirmDelete = (index) => {
        if(window.confirm('Are you sure you want to delete this rule?')){
            onDelete(index);
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


// Rule.propTypes = {
//     allComponents: PropTypes.object,
//     logic: PropTypes.objects,
//     component: PropTypes.string,
//     actions: PropTypes.arrayOf(PropTypes.object),
// };

export {FormLogic, formatRuleComponentChoices, EMPTY_RULE};
