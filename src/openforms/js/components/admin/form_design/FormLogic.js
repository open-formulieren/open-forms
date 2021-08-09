import React from 'react';
import PropTypes from 'prop-types';
import FormioUtils from 'formiojs/utils';
import {useImmerReducer} from 'use-immer';
import {TextArea} from "../forms/Inputs";
import Select from "../forms/Select";
import {LOGICS_ENDPOINT} from './constants';
import {get, post, put} from "../../../utils/fetch";
import useAsync from "react-use/esm/useAsync";


const initialState = {
    components: {
        loading: true,
        choices: []
    },
    rules: [],
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
            payload: Object.entries(allComponents).map( ([key, comp]) => [key, comp.label || comp.key] )
        });
    };

    const loadExistingRules = async () => {
        const rulesResponse = await get(`${LOGICS_ENDPOINT}?form=${formUuid}`);
        if (rulesResponse.ok) {
            dispatch({
                type: 'LOADED_RULES',
                payload: rulesResponse.data
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
    }

    const getFormStepChoices = (formSteps) => {
        return formSteps.map((formStep, index) => [formStep.url, formStep.name]);
    };

    useAsync(async () => {
        getComponentsChoices();
        await loadExistingRules();
    }, [formSteps]);

    return (
        <>
            {state.rules.map((rule, i) => (
                <Rule
                    key={i}
                    {...rule}
                    formStepsChoices={getFormStepChoices(formSteps)}
                    components={state.components}
                    onChange={onRuleChange.bind(null, i)}
                />
            ))}
            <button type="button" onClick={ () => dispatch({type: 'ADD_RULE'}) }>
                Add rule
            </button>
             <button type="button" onClick={onSubmit}>
                Save logic
            </button>
        </>
    );
};

FormLogic.propTypes = {
    formSteps: PropTypes.arrayOf(PropTypes.object).isRequired,
};


const Rule = ({components, formStepsChoices, uuid, component, formStep, jsonLogicTrigger, actions, onChange}) => {
    const onChangeJsonFields = (event) => {
        const jsonField = JSON.parse(event.target.value);
        console.log(jsonField);
        onChange({target: {name: event.target.name, value: jsonField}});
    }
    return (
        <div>
            When the following logic evaluates to true
            <TextArea
                name='jsonLogicTrigger'
                rows={7}
                cols={20}
                value={JSON.stringify(jsonLogicTrigger)}
                onChange={onChangeJsonFields}
            />
            update the field
            <Select
                name="component"
                choices={EMPTY_CHOICE.concat(components.choices)}
                value={component}
                onChange={onChange}
            />
            of the form step
            <Select
                name="formStep"
                choices={EMPTY_CHOICE.concat(formStepsChoices)}
                value={formStep}
                onChange={onChange}
            />
            with the following actions
            <TextArea
                name='actions'
                rows={7}
                cols={20}
                value={JSON.stringify(actions)}
                onChange={onChangeJsonFields}
            />
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
