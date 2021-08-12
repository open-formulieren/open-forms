import React from 'react';
import PropTypes from 'prop-types';
import FormioUtils from 'formiojs/utils';
import {useImmerReducer} from 'use-immer';
import {TextArea} from '../forms/Inputs';
import Select from '../forms/Select';
import {LOGICS_ENDPOINT} from './constants';
import {apiDelete, get, post, put} from '../../../utils/fetch';
import useAsync from 'react-use/esm/useAsync';
import FAIcon from '../FAIcon';
import Trigger from './logic/Trigger';
import {ComponentsContext} from './logic/Context';
import {Action} from './logic/Action';
import {ActionSet} from "./logic/ActionSet";


const initialState = {
    components: {
        loading: true,
        choices: []
    },
    rules: [],
    rulesToDelete: []
};

const EMPTY_CHOICE = [['', '-------']];

const EMPTY_RULE = {
    uuid: '',
    formStep: '',
    jsonLogicTrigger: '',
    component: '',
    actions: [],
};

const reducer = (draft, action) => {
    switch (action.type) {
        case 'LOADED_RULES': {
            draft.rules = action.payload;
            break;
        }
        case 'ADD_RULE': {
            draft.rules.push(EMPTY_RULE);
            break;
        }
        case 'CHANGED_RULE': {
            const {index, name, value} = action.payload;
            draft.rules[index][name] = value;
            break;
        }
        case 'DELETED_RULE': {
            const {index} = action.payload;
            draft.rulesToDelete.push(draft.rules[index].uuid);

            const updatedRules = [...draft.rules];
            updatedRules.splice(index, 1);
            draft.rules = updatedRules;
            break;
        }
        case 'FORMATTED_COMPONENTS_CHOICES': {
            draft.components = {
                loading: false,
                choices: action.payload
            };
            break;
        }
        default:
            throw new Error(`Unknown action type: ${action.type}`);
    }
};

// TODO Context for csrftoken
const FormLogic = ({ formUuid, formSteps, csrftoken }) => {
    const [state, dispatch] = useImmerReducer(reducer, initialState);

    // key-value map of component.key: component, flattened from all available steps
    const getComponentsChoices = () => {
        // key-value map of component.key: component, flattened from all available steps
        const allComponents = formSteps.map(
            step => FormioUtils.flattenComponents(step.configuration.components || [], false)
        ).reduce((acc, currentValue) => ({...acc, ...currentValue}), {});
        dispatch({
            type: 'FORMATTED_COMPONENTS_CHOICES',
            payload: allComponents,
        });
    };

    const loadExistingRules = async () => {
        const rulesResponse = await get(`${LOGICS_ENDPOINT}?form=${formUuid}`);
        if (rulesResponse.ok) {
            dispatch({
                type: 'LOADED_RULES',
                payload: rulesResponse.data.length ? rulesResponse.data : [EMPTY_RULE],
            });
        }
    };

    const onRuleChange = (index, event) => {
        const { name, value } = event.target;
        dispatch({
            type: 'CHANGED_RULE',
            payload: {name, value, index},
        });
    };

    const onRuleDelete = (index) => {
        dispatch({
            type: 'DELETED_RULE',
            payload: {index: index}
        });
    };

    const onSubmit = async (event) => {
        event.preventDefault();

        for (let index = 0; index < state.rules.length; index++) {
            const logicRule = state.rules[index];
            const isNewRule = !logicRule.uuid;
            const createOrUpdate = isNewRule ? post : put;
            const endPoint = isNewRule ? LOGICS_ENDPOINT : `${LOGICS_ENDPOINT}/${logicRule.uuid}`;

            var formLogicResponse = await createOrUpdate(
                endPoint,
                csrftoken,
                logicRule
            );

            if (!formLogicResponse.ok) {
                throw new Error('An error occurred while saving the form logic.');
            }
            var ruleUuid = formLogicResponse.data.uuid;
            if (isNewRule){
                dispatch({
                    type: 'CHANGED_RULE',
                    payload: {name: 'uuid', value: ruleUuid, index: index}
                });
            }

        }

        if (state.rulesToDelete.length) {
            for (const ruleUuid of state.rulesToDelete) {
                // Rules that were added but are not saved in the backend yet don't have a UUID.
                if (!ruleUuid) return;

                var response = await apiDelete(`${LOGICS_ENDPOINT}/${ruleUuid}`, csrftoken);
                if (!response.ok) {
                    throw new Error('An error occurred while deleting logic rules.');
                }

            }
        }
    }

    const getFormStepChoices = (formSteps) => {
        return formSteps.map((formStep, index) => [formStep.url, formStep.name]);
    };

    useAsync(async () => {
        getComponentsChoices();
        await loadExistingRules();
    }, [formSteps]);

    return (
        <ComponentsContext.Provider value={state.components.choices}>
            {state.rules.map((rule, i) => (
                <Rule
                    key={i}
                    {...rule}
                    formStepsChoices={getFormStepChoices(formSteps)}
                    components={state.components}
                    onChange={onRuleChange.bind(null, i)}
                    onDelete={onRuleDelete.bind(null, i)}
                />
            ))}
            <button type="button" onClick={ () => dispatch({type: 'ADD_RULE'}) }>
                Add rule
            </button>
             <button type="button" onClick={onSubmit}>
                Save logic
            </button>
        </ComponentsContext.Provider>
    );
};

FormLogic.propTypes = {
    formSteps: PropTypes.arrayOf(PropTypes.object).isRequired,
};


const Rule = ({components, formStepsChoices, uuid, component, formStep, jsonLogicTrigger, actions, onChange, onDelete}) => {
    const confirmDelete = (index) => {
        if(window.confirm('Are you sure you want to delete this rule?')){
            onDelete(index);
        }
    };

    return (
        <div className="logic-rule">

            <Trigger name="jsonLogicTrigger"logic={jsonLogicTrigger} onChange={onChange} />
            <ActionSet actions={[]} />

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

export default FormLogic;
