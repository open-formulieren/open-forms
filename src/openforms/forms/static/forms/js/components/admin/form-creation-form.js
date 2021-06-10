import _ from 'lodash';

import React from 'react';
import {useImmerReducer} from 'use-immer';
import {original} from 'immer';
import PropTypes from 'prop-types';
import { v4 as uuidv4 } from 'uuid';

import Field from '../formsets/Field';
import FormRow from '../formsets/FormRow';
import Fieldset from '../formsets/Fieldset';
import {TextInput} from '../formsets/Inputs';
import useAsync from 'react-use/esm/useAsync';
import {apiDelete, get, post, put} from '../utils/fetch';
import SubmitRow from "../formsets/SubmitRow";
import {getFormDefinitionChoices} from "../utils/form-definition-choices";

import FormSteps from './FormSteps';

const FORM_ENDPOINT = '/api/v1/forms';
const FORM_DEFINITIONS_ENDPOINT = '/api/v1/form-definitions';
const ADMIN_PAGE = '/admin/forms/form';

const initialFormState = {
    formName: '',
    formUuid: '',
    formSlug: '',
    newForm: true,
    formSteps: {
        loading: true,
        data: [],
    },
    errors: {},
    formDefinitions: {},
    stepsToDelete: []
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
            for (const definition of rawFormDefinitions) {
                formDefinitions[definition.url] = definition;
            }
            draft.formDefinitions = formDefinitions;
            break;
        }
        case 'FORM_STEPS_LOADED': {
            draft.formSteps = {
                loading: false,
                data: action.payload,
            };
            break;
        }
        /**
         * FormStep-level actions
         */
        case 'DELETE_STEP': {
            const {index, step} = action.payload;
            draft.stepsToDelete.push(draft.formSteps.data[index].url);

            const unchangedSteps = draft.formSteps.data.slice(0, index);
            const updatedSteps = draft.formSteps.data.slice(index+1).map((step) => {
                step.index = step.index - 1;
                return step;
            });
            draft.formSteps.data = [...unchangedSteps, ...updatedSteps];
            break;
        }
        case 'ADD_STEP': {
            const emptyStep = {
                formDefinition: '',
                configuration:  {display: 'form'},
                // index: draft.formSteps.data.length,
                url: ''
            };
            draft.formSteps.data = draft.formSteps.data.concat([emptyStep]);
            break;
        }
        case 'REPLACE_STEP': {
            const {index, formDefinitionUrl} = action.payload;
            if (!formDefinitionUrl) {
                draft.formSteps.data[index].formDefinition = '';
                draft.formSteps.data[index].configuration = {display: 'form'};
            } else {
                draft.formSteps.data[index].formDefinition = formDefinitionUrl;
                draft.formSteps.data[index].configuration = draft.formDefinitions[formDefinitionUrl].configuration;
            }
            break;
        }
        case 'EDIT_STEP': {
            const {index, configuration} = action.payload;
            // const currentConfiguration = original(draft.formSteps.data[index].configuration);
            draft.formSteps.data[index].configuration = configuration;
            break;
        }
        case 'MOVE_UP_STEP': {
            const index = action.payload;
            if (index <= 0 || index >= draft.formSteps.data.length) break;

            let updatedSteps = draft.formSteps.data.slice(0, index-1);
            updatedSteps = updatedSteps.concat([{...draft.formSteps.data[index], ...{index: index-1}}]);
            updatedSteps = updatedSteps.concat([{...draft.formSteps.data[index-1], ...{index: index}}]);

            draft.formSteps.data = [...updatedSteps, ...draft.formSteps.data.slice(index+1)];
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


/**
 * Functions to fetch data
 */
const getFormStepsData = async (formUuid) => {
    try {
        var response = await get(`${FORM_ENDPOINT}/${formUuid}/steps`);
        if (!response.ok) {
            throw new Error('An error occurred while fetching the form steps.');
        }
    } catch (e) {
        dispatch({type: 'SET_FETCH_ERRORS', payload: {loadingErrors: e.message}});
    }

    return response.data;
};

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
        if (!response.ok) {
            throw new Error('An error occurred while fetching the form.');
        } else {
            // Get the form definition data from the form steps
            const formStepsData = await getFormStepsData(formUuid);
            dispatch({
                type: 'FORM_STEPS_LOADED',
                payload: formStepsData,
            });
        }
    } catch (e) {
        dispatch({type: 'SET_FETCH_ERRORS', payload: {loadingErrors: e.message}});
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
        dispatch({type: 'SET_FETCH_ERRORS', payload: {loadingErrors: e.message}});
    }
};


const StepsFieldSet = ({ loading=true, loadingErrors, steps=[], ...props }) => {
    if (loadingErrors) {
        return (
            <div className="fetch-error">{loadingErrors}</div>
        );
    }

    if (loading) {
        return (
            <div>Loading form steps...</div>
        );
    }

    return (
        // formDefinitionChoices={getFormDefinitionChoices(state.formDefinitions)}
        <FormSteps steps={steps} {...props} />
    );
};

StepsFieldSet.propTypes = {
    loading: PropTypes.bool.isRequired,
    loadingErrors: PropTypes.node,
    steps: PropTypes.arrayOf(PropTypes.object),
};


/**
 * Component to render the form edit page.
 */
const FormCreationForm = ({csrftoken, formUuid, formName, formSlug}) => {
    const initialState = {
        ...initialFormState,
        formUuid: formUuid ? formUuid :  uuidv4(),
        formName: formName,
        formSlug: formSlug,
        newForm: !formUuid,
    };
    const [state, dispatch] = useImmerReducer(reducer, initialState);

    useAsync(async () => {
        const promises = [
            getFormData(formUuid, dispatch),
            getFormDefinitions(dispatch),
        ];
        await Promise.all(promises);
    }, []);

    /**
     * Functions for handling events
     */
    const onFieldChange = (event) => {
        const { name, value } = event.target;
        dispatch({
            type: 'FIELD_CHANGED',
            payload: {name, value},
        });
    };

    const onStepDelete = (index, formStepData) => {
        dispatch({
            type: 'DELETE_STEP',
            payload: {index: index, step: formStepData}
        });
    };

    const addStep = (event) => {
        event.preventDefault();
        dispatch({
            type: 'ADD_STEP',
        });
    };

    const onStepReplace = (index, event) => {
        dispatch({
            type: 'REPLACE_STEP',
            payload: {
                index: index,
                formDefinitionUrl: event.target.value
            }
        })
    };

    const onStepEdit = (index, configuration) => {
        dispatch({
            type: 'EDIT_STEP',
            payload: {
                index: index,
                configuration: configuration
            }
        })
    };

    const onStepReorder = (index, direction) => {
        if (direction === 'up') {
            dispatch({
                type: 'MOVE_UP_STEP',
                payload: index,
            });
        } else if (direction === 'down') {
            dispatch({
                type: 'MOVE_UP_STEP',
                payload: index+1,
            });
        }
    };

    const onSubmit = async () => {
        // Update the form
        const formData = {
            name: state.formName,
            slug: state.formSlug,
        };

        const createOrUpdate = state.newForm ? post : put;
        const endPoint = state.newForm ? FORM_ENDPOINT : `${FORM_ENDPOINT}/${state.formUuid}`;


        try {
            var response = await createOrUpdate(
                endPoint,
                csrftoken,
                formData,
            );

            if (!response.ok) {
                throw new Error('An error occurred while saving the form.');
            }
        } catch (e) {
            dispatch({type: 'SET_FETCH_ERRORS', payload: response.data});
            window.scrollTo(0, 0);
            return;
        }

        // Update the form steps
        await Promise.all(state.formSteps.data.map(async (step, index) => {
            const createOrUpdate = step.url ? put : post;
            const endpoint = step.url ? step.url : `${FORM_ENDPOINT}/${state.formUuid}/steps`;

            try {
                var response = await createOrUpdate(
                    endpoint,
                    csrftoken,
                    {...step, ...{index: index}}
                );
                if (!response.ok) {
                    throw new Error('An error occurred while updating the form steps.');
                }
            } catch (e) {
                dispatch({type: 'SET_FETCH_ERRORS', payload: response.data});
            }
        }));

        if (state.stepsToDelete) {
            await Promise.all(state.stepsToDelete.map(async (step, index) => {
                // Steps that were added but are not saved in the backend yet don't have a URL.
                if (!step) return;

                try {
                     var response = await apiDelete(step, csrftoken);
                     if (!response.ok) {
                         throw new Error('An error occurred while deleting form steps.');
                    }
                } catch (e) {
                    dispatch({type: 'SET_FETCH_ERRORS', payload: response.data});
                }

            }));
        }

        if (Object.keys(state.errors).length) {
            window.scrollTo(0, 0);
            return;
        }

        // redirect back to list/overview page
        window.location = ADMIN_PAGE;
    };

    const onCopy = async (event) => {
        event.preventDefault();
        const response = await post(
            `${FORM_ENDPOINT}/${state.formUuid}/copy_form`,
            csrftoken,
        );

        if (!response.ok) {
            dispatch({type: 'SET_FETCH_ERRORS', payload: response.data});
            window.scrollTo(0, 0);
        }

        window.location = `${ADMIN_PAGE}/${response.data.newPk}/change/`;
    };

    const onExport = async (event) => {
        event.preventDefault();
        window.location = `${FORM_ENDPOINT}/${state.formUuid}/export_form`;
    };

    return (
        <>
            {Object.keys(state.errors).length ? <div className='fetch-error'>The form is invalid. Please correct the errors below.</div> : null}
            <Fieldset>
                <FormRow>
                    <Field
                        name='formUuid'
                        label='Form UUID'
                        helpText='Unique identifier for the form'
                        errors={state.errors.uuid}
                        required
                    >
                        <TextInput value={state.formUuid} onChange={onFieldChange} disabled={true}/>
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
                        errors={state.errors.slug}
                        required
                    >
                        <TextInput value={state.formSlug} onChange={onFieldChange} />
                    </Field>
                </FormRow>
            </Fieldset>

            <Fieldset title='Form steps'>
                <StepsFieldSet
                    steps={state.formSteps.data}
                    loading={state.formSteps.loading}
                    loadingErrors={state.errors.loadingErrors}
                    onEdit={onStepEdit}
                    onDelete={onStepDelete}
                    onReorder={onStepReorder}
                    onReplace={onStepReplace}
                    errors={state.errors.formSteps}
                />
            </Fieldset>

            <div style={{marginBottom: '20px'}}>
                <a href="#" onClick={addStep} className="addlink">
                    Add step
                </a>
            </div>
            <SubmitRow onSubmit={onSubmit} />
            { !state.newForm ?
                <div className="submit-row">
                    <input
                        type="submit"
                        value="Copy"
                        className="default"
                        name="_copy"
                        title="Duplicate this form"
                        onClick={onCopy}
                    />
                    <input
                        type="submit"
                        value="Export"
                        className="default"
                        name="_export"
                        title="Export this form"
                        onClick={onExport}
                    />
                </div> : null
            }
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
