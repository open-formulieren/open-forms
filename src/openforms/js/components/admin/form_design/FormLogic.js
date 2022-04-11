import React, {useContext} from 'react';
import PropTypes from 'prop-types';
import {useIntl, FormattedMessage} from 'react-intl';

import DeleteIcon from '../DeleteIcon';
import Trigger from './logic/Trigger';
import ActionSet from './logic/actions/ActionSet';
import ButtonContainer from '../forms/ButtonContainer';
import Fieldset from '../forms/Fieldset';
import AdvancedTrigger from './logic/AdvancedTrigger';
import {ValidationErrorContext} from '../forms/ValidationErrors';


const EMPTY_RULE = {
    uuid: '',
    _generatedId: '',  // consumers should generate this, as it's used for the React key prop if no uuid exists
    form: '',
    jsonLogicTrigger: {'': [{'var': ''}, null]},
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


const FormLogic = ({ logicRules=[], onChange, onDelete, onAdd }) => {
    const filterLogicRules = (rules) => {
        let basicRules = [];
        let advancedRules = [];
        rules.map((rule, index) => {
           if (rule.isAdvanced) {
               advancedRules.push([index, rule]);
           } else {
               basicRules.push([index, rule]);
           }
        });

        return [basicRules, advancedRules];
    };

    const [basicLogicRules, advancedLogicRules] = filterLogicRules(logicRules);

    return (
        <>
            <Fieldset title={<FormattedMessage description="Logic fieldset title" defaultMessage="Logic" />}>
                <FormLogicRules
                    rules={basicLogicRules}
                    onAdd={() => onAdd({isAdvanced: false})}
                    onChange={onChange}
                    onDelete={onDelete}
                />
            </Fieldset>
            <Fieldset title={<FormattedMessage description="Advanced logic fieldset title" defaultMessage="Advanced Logic" />}>
                <FormLogicRules
                    rules={advancedLogicRules}
                    onAdd={() => onAdd({isAdvanced: true})}
                    onChange={onChange}
                    onDelete={onDelete}
                />
            </Fieldset>
        </>
    );
};

FormLogic.propTypes = {
    logicRules: PropTypes.arrayOf(PropTypes.object).isRequired,
    onChange: PropTypes.func.isRequired,
    onDelete: PropTypes.func.isRequired,
    onAdd: PropTypes.func.isRequired,
};


const FormLogicRules = ({rules, onAdd, onChange, onDelete}) => {
    const validationErrors = parseValidationErrors(useContext(ValidationErrorContext));
    return (
        <>
            {
                rules.map(([index, rule], _) => {
                    return (
                        <Rule
                            key={rule.uuid || rule._generatedId}
                            {...rule}
                            onChange={onChange.bind(null, index)}
                            onDelete={onDelete.bind(null, index)}
                            errors={validationErrors[index]}
                        />
                    );
                })
            }
            <ButtonContainer onClick={onAdd}>
                <FormattedMessage description="Add form logic rule button" defaultMessage="Add rule" />
            </ButtonContainer>
        </>
  );
};

FormLogicRules.propTypes = {
    rules:  PropTypes.arrayOf(PropTypes.array).isRequired,
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

    const TriggerComponent = isAdvanced ? AdvancedTrigger : Trigger;

    return (
        <div className="logic-rule">
            <div className="logic-rule__actions">
                <DeleteIcon onConfirm={onDelete} message={deleteConfirmMessage} />
            </div>

            <div className="logic-rule__rule">
                <TriggerComponent
                    name="jsonLogicTrigger"
                    logic={jsonLogicTrigger}
                    onChange={onChange}
                    error={errors.jsonLogicTrigger}
                />
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
