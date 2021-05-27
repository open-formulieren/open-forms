import React from 'react';
import {useImmerReducer} from 'use-immer';
import PropTypes from 'prop-types';
import Field from '../formsets/Field';
import FormRow from '../formsets/FormRow';
import Fieldset from '../formsets/Fieldset';
import {TextInput} from '../formsets/Inputs';
import useAsync from 'react-use/esm/useAsync';
import {get, post, put} from '../utils/fetch';
import {FormSteps} from './formsteps-formset';
import SubmitRow from "../formsets/SubmitRow";

const FORM_ENDPOINT = '/api/v1/_manage_forms';
const FORM_DEFINITIONS_ENDPOINT = '/api/v1/form-definitions';
const ADMIN_PAGE = '/admin/forms/form';

const initialFormState = {
    formName: '',
    formUuid: '',
    formSlug: '',
    formSteps: {
        loading: true,
        data: []
    },
    errors: {},
    formDefinitions: {},
    formDefinitionChoices: []
};

function reducer(draft, action) {
    switch (action.type) {
        /**
         * Form-level actions
         */
        case 'FIELD_CHANGED': {
            const { name, value } = action.payload;
            draft[name] = value;
            break;
        }
        case 'FORM_DEFINITIONS_LOADED': {
            const rawFormDefinitions = action.payload;
            var formDefinitions = {};
            var formDefinitionChoices = [['', '------']];
            for (const definition of rawFormDefinitions) {
                formDefinitions[definition.uuid] = definition;
                formDefinitionChoices.push([definition.uuid, definition.name]);
            }
            draft.formDefinitions = formDefinitions;
            draft.formDefinitionChoices = formDefinitionChoices;
            break;
        }
        /**
         * FormSteps-level actions
         */
        case 'FORM_STEPS_LOADED': {
            draft.formSteps = {
                loading: false,
                data: action.payload
            };
            break;
        }
        case 'DELETE_STEP': {
            const index = action.payload;
            const unchangedSteps = draft.formSteps.data.slice(0, index);

            const updatedSteps = draft.formSteps.data.slice(index+1).map((step) => {
                step.order = step.order - 1;
                return step;
            });
            draft.formSteps.data = [...unchangedSteps, ...updatedSteps];
            break;
        }
        case 'ADD_STEP': {
            const emptyStep = {
                formDefinition: {
                    configuration: {display: 'form'},
                    uuid: '',
                },
                order: draft.formSteps.data.length,
            };
            draft.formSteps.data = draft.formSteps.data.concat([emptyStep]);
            break;
        }
        case 'CHANGE_STEP': {
            const {index, formDefinitionUuid} = action.payload;
            draft.formSteps.data[index].formDefinition = draft.formDefinitions[formDefinitionUuid];
            break;
        }
        /**
         * Misc
         */
        case 'SET_FETCH_ERRORS': {
            draft.errors = action.payload;
            break;
        }
        default:
            throw new Error(`Unknown action type: ${action.type}`);
    }
}

const getFormData = async (formUuid, dispatch) => {
    if (!formUuid) {
        dispatch({
            type: 'FORM_STEPS_LOADED',
            payload: [],
        });
        return;
    }

    try {
        const response = await get(`${FORM_ENDPOINT}/${formUuid}`);
        if (!response.ok && response.status === 404) {
            // When we are creating a form, the form endpoint doesn't exist yet
            dispatch({
                type: 'FORM_STEPS_LOADED',
                payload: [],
            });
        } else if (!response.ok) {
            throw new Error('An error occurred while fetching the form.');
        } else {
            dispatch({
                type: 'FORM_STEPS_LOADED',
                payload: response.data.formSteps,
            });
        }
    } catch (e) {
        dispatch({type: 'SET_FETCH_ERRORS', payload: e});
    }
};

const getFormDefinitions = async (dispatch) => {
    try {
        const response = await get(FORM_DEFINITIONS_ENDPOINT);
        dispatch({
            type: 'FORM_DEFINITIONS_LOADED',
            payload: response.data.results,
        });
    } catch (e) {
        dispatch({type: 'SET_FETCH_ERRORS', payload: e});
    }
};

const FormCreationForm = ({csrftoken, formUuid, formName, formSlug}) => {
    const initialState = {...initialFormState, formUuid, formName, formSlug};
    const [state, dispatch] = useImmerReducer(reducer, initialState);

    useAsync(async () => {
        await getFormData(formUuid, dispatch);
        await getFormDefinitions(dispatch);
    }, []);

    const onFieldChange = (event) => {
        const { name, value } = event.target;
        dispatch({
            type: 'FIELD_CHANGED',
            payload: {name, value},
        });
    };

    const onStepDelete = (index) => {
        dispatch({
            type: 'DELETE_STEP',
            payload: index
        });
    };

    const addStep = (event) => {
        event.preventDefault();
        dispatch({
            type: 'ADD_STEP',
        });
    };

    const onStepChange = (event, index) => {
        dispatch({
            type: 'CHANGE_STEP',
            payload: {
                index: index,
                formDefinitionUuid: event.target.value
            }
        })
    };

    const onSubmit = async () => {
        const formData = {
            uuid: state.formUuid,
            name: state.formName,
            slug: state.formSlug,
            formSteps: state.formSteps.data
        };

        // Try to update form
        const putResponse = await put(
            `${FORM_ENDPOINT}/${state.formUuid}`,
            csrftoken,
            formData,
        );

        // If the form doesn't exist yet, create it
        if (!putResponse.ok && putResponse.status === 404) {
            const postResponse = await post(
                FORM_ENDPOINT,
                csrftoken,
                formData,
            );
            if (!postResponse.ok) {
                dispatch({type: 'SET_FETCH_ERRORS', payload: postResponse.data});
                return;
            }
        } else if (!putResponse.ok) {
            dispatch({type: 'SET_FETCH_ERRORS', payload: putResponse.data});
            return;
        }

        // redirect back to list/overview page
        window.location = ADMIN_PAGE;
    };

    const hasErrors = state.errors.length;
    return (
        <>
            {hasErrors ? <div className='fetch-error'>Dit formulier is ongeldig. Corrigeer de onderstaande fouten.</div> : null}
            <Fieldset>
                <FormRow>
                    <Field
                        name='formUuid'
                        label='Form UUID'
                        helpText='Unique identifier for the form'
                        errors={state.errors.name}
                        required
                    >
                        <TextInput value={state.formUuid} onChange={onFieldChange} />
                    </Field>
                </FormRow>
                <FormRow>
                    <Field
                        name='formName'
                        label='Form name'
                        helpText='Name of the form'
                        errors={state.errors.name}
                        required
                    >
                        <TextInput value={state.formName} onChange={onFieldChange} />
                    </Field>
                </FormRow>
                <FormRow>
                    <Field
                        name='formSlug'
                        label='Form slug'
                        helpText='Slug of the form'
                        errors={state.errors.name}
                        required
                    >
                        <TextInput value={state.formSlug} onChange={onFieldChange} />
                    </Field>
                </FormRow>
            </Fieldset>
            <Fieldset title='Form steps definitions'>
                { state.formSteps.loading ? <div>Loading form steps...</div> :
                    <FormSteps
                        formSteps={state.formSteps.data}
                        formDefinitionChoices={state.formDefinitionChoices}
                        onChange={onStepChange}
                        onDelete={onStepDelete}
                        errors={state.errors}
                    />
                }
            </Fieldset>
            <div style={{marginBottom: '20px'}}>
                <a href="#" onClick={addStep} className="addlink">
                    Add step
                </a>
            </div>
            <SubmitRow onSubmit={onSubmit} />
        </>
    );
};

FormCreationForm.propTypes = {
    csrftoken: PropTypes.string.isRequired,
    formUuid: PropTypes.string.isRequired,
    formName: PropTypes.string.isRequired,
    formSlug: PropTypes.string.isRequired,
};

export { FormCreationForm };
