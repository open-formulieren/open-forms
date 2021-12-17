import React, {useContext} from 'react';
import PropTypes from 'prop-types';
import {useIntl, FormattedMessage} from 'react-intl';

import DeleteIcon from '../DeleteIcon';
import Trigger from './logic/Trigger';
import {ComponentsContext} from '../forms/Context';
import ActionSet from './logic/ActionSet';
import Fieldset from '../forms/Fieldset';
import AdvancedTrigger from './logic/AdvancedTrigger';
import {ValidationErrorContext} from '../forms/ValidationErrors';


const EMPTY_RULE = {
    uuid: '',
    form: '',
    jsonLogicTrigger: {},
    isAdvanced: false,
    actions: [],
};

const parseValidationErrors = (errors) => {
    let parsedErrors = {};
    for (const [errorName, errorReason] of errors) {
        const errorNameBits = errorName.split('.');
        if (errorNameBits[0] === 'logicRules') {
            const ruleIndex = Number(errorNameBits[1]);
            if (parsedErrors[ruleIndex]) {
                parsedErrors[ruleIndex][errorNameBits[2]] = errorReason;
            } else {
                parsedErrors[ruleIndex] = {};
                parsedErrors[ruleIndex][errorNameBits[2]] = errorReason;
            }
        }
    }
    return parsedErrors;
};


const FormLogic = ({ logicRules=[], availableComponents={}, onChange, onDelete, onAdd }) => {
    return (
        <ComponentsContext.Provider value={availableComponents}>
            <Fieldset title={<FormattedMessage description="Logic fieldset title" defaultMessage="Logic" />}>
                <FormLogicRules
                    rules={logicRules}
                    advanced={false}
                    onAdd={onAdd}
                    onChange={onChange}
                    onDelete={onDelete}
                />
            </Fieldset>
            <Fieldset title={<FormattedMessage description="Advanced logic fieldset title" defaultMessage="Advanced Logic" />}>
                <FormLogicRules
                    rules={logicRules}
                    advanced={true}
                    onAdd={onAdd}
                    onChange={onChange}
                    onDelete={onDelete}
                />
            </Fieldset>
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


const FormLogicRules = ({rules, advanced, onAdd, onChange, onDelete}) => {
    const validationErrors = parseValidationErrors(useContext(ValidationErrorContext));
    return (
        <>
            {
                rules.map((rule, i) => {
                    if (rule.isAdvanced === advanced) {
                        return (
                            <Rule
                                key={i}
                                {...rule}
                                onChange={onChange.bind(null, i)}
                                onDelete={onDelete.bind(null, i)}
                                errors={validationErrors[i]}
                            />
                        );
                    }
                })
            }
            <div className="button-container button-container--padded">
                <button
                    type="button"
                    className="button button--plain"
                    onClick={() => {
                        onAdd({...EMPTY_RULE, isAdvanced: advanced});
                    }}
                >
                    <span className="addlink">
                        <FormattedMessage description="Add form logic rule button" defaultMessage="Add rule" />
                    </span>
                </button>
            </div>
      </>
  );
};

FormLogicRules.propTypes = {
    rules:  PropTypes.arrayOf(PropTypes.object).isRequired,
    advanced: PropTypes.bool.isRequired,
    onChange: PropTypes.func.isRequired,
    onDelete: PropTypes.func.isRequired,
    onAdd: PropTypes.func.isRequired,
};


const Rule = ({jsonLogicTrigger, actions, isAdvanced, onChange, onDelete, errors={}}) => {
    const intl = useIntl();
    const deleteConfirmMessage = intl.formatMessage({
        description: 'Logic rule deletion confirm message',
        defaultMessage: 'Are you sure you want to delete this rule?',
    });
    return (
        <div className="logic-rule">
            <div className="logic-rule__actions">
                <DeleteIcon onConfirm={onDelete} message={deleteConfirmMessage} />
            </div>

            <div className="logic-rule__rule">
                {
                    isAdvanced
                    ? (<AdvancedTrigger name="jsonLogicTrigger" logic={jsonLogicTrigger} onChange={onChange} error={errors['jsonLogicTrigger']}/>)
                    : (<Trigger name="jsonLogicTrigger" logic={jsonLogicTrigger} onChange={onChange} />)
                }
                <ActionSet name="actions" actions={actions} onChange={onChange} />
            </div>
        </div>
    );
};

Rule.propTypes = {
    jsonLogicTrigger: PropTypes.object,
    actions: PropTypes.arrayOf(PropTypes.object),
    isAdvanced: PropTypes.bool.isRequired,
    onChange: PropTypes.func.isRequired,
    onDelete: PropTypes.func.isRequired,
    errors: PropTypes.object,
};


export {FormLogic, EMPTY_RULE};
