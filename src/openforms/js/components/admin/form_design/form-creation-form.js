/*
global URLify;
 */
import React from 'react';
import {useImmerReducer} from 'use-immer';
import PropTypes from 'prop-types';
import useAsync from 'react-use/esm/useAsync';

import {FormException} from "../../../utils/exception";
import {apiDelete, get, post, put} from '../../../utils/fetch';
import Field from '../forms/Field';
import FormRow from '../forms/FormRow';
import Fieldset from '../forms/Fieldset';
import {TextInput, Checkbox} from '../forms/Inputs';
import SubmitRow from "../forms/SubmitRow";
import Loader from '../Loader';
import { FormDefinitionsContext, PluginsContext } from './Context';
import FormSteps from './FormSteps';
import { FORM_ENDPOINT, FORM_DEFINITIONS_ENDPOINT, ADMIN_PAGE, AUTH_PLUGINS_ENDPOINT, PREFILL_PLUGINS_ENDPOINT } from './constants';
import AuthPluginField from "./AuthPluginField";

const initialFormState = {
    formName: '',
    formUuid: '',
    formSlug: '',
    formShowProgressIndicator: true,
    newForm: true,
    formSteps: {
        loading: true,
        data: [],
    },
    errors: {},
    formDefinitions: {},
    availableAuthPlugins: {
        loading: true,
        data: {}
    },
    availablePrefillPlugins: {
        loading: true,
        data: {}
    },
    selectedAuthPlugins: [],
    stepsToDelete: [],
    submitting: false,
};

const newStepData = {
    configuration:  {display: 'form'},
    formDefinition: '',
    slug: '',
    url: '',
    isNew: true,
};

function reducer(draft, action) {
    switch (action.type) {
        /**
         * Form-level actions
         */
        case 'FORM_LOADED': {
            return {
                ...draft,
                ...action.payload,
            };
        }
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
        case 'AUTH_PLUGINS_LOADED': {
            var formattedAuthPlugins = {};
            for (const plugin of action.payload) {
                formattedAuthPlugins[plugin.id] = plugin;
            }
            draft.availableAuthPlugins = {
                loading: false,
                data: formattedAuthPlugins,
            };
            break;
        }
        case 'PREFILL_PLUGINS_LOADED': {
            var formattedPrefillPlugins = {};
            for (const plugin of action.payload) {
                formattedPrefillPlugins[plugin.id] = plugin;
            }
            draft.availablePrefillPlugins = {
                loading: false,
                data: formattedPrefillPlugins,
            };
            break;
        }
        case 'TOGGLE_AUTH_PLUGIN': {
            const pluginId = action.payload;
            if (draft.selectedAuthPlugins.includes(pluginId)) {
                draft.selectedAuthPlugins = draft.selectedAuthPlugins.filter(id => id !== pluginId);
            } else {
                draft.selectedAuthPlugins = [...draft.selectedAuthPlugins, pluginId];
            }
            break;
        }
        /**
         * FormStep-level actions
         */
        case 'DELETE_STEP': {
            const {index} = action.payload;
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
            const newIndex = draft.formSteps.data.length;
            const emptyStep = {
                ...newStepData,
                index: newIndex,
                name: `Stap ${newIndex + 1}`,
            };
            draft.formSteps.data = draft.formSteps.data.concat([emptyStep]);
            break;
        }
        case 'FORM_DEFINITION_CHOSEN': {
            const {index, formDefinitionUrl} = action.payload;
            if (!formDefinitionUrl) {
                draft.formSteps.data[index] = {
                    ...draft.formSteps.data[index],
                    ...newStepData,
                    // if we're creating a new form definition, mark the step no longer as new since a decision
                    // was made (re-use one or create a new one)
                    isNew: false,
                };
            } else {
                const { configuration, name, slug } = draft.formDefinitions[formDefinitionUrl];
                const { url } = draft.formSteps.data[index];
                draft.formSteps.data[index] = {
                    configuration,
                    formDefinition: formDefinitionUrl,
                    index,
                    name,
                    slug,
                    url,
                    isNew: false,
                };
            }
            break;
        }
        case 'EDIT_STEP': {
            const {index, configuration} = action.payload;
            // const currentConfiguration = original(draft.formSteps.data[index].configuration);
            draft.formSteps.data[index].configuration = configuration;
            break;
        }
        case 'STEP_FIELD_CHANGED': {
            const {index, name, value} = action.payload;
            draft.formSteps.data[index][name] = value;
            break;
        }
        case 'STEP_LITERAL_FIELD_CHANGED': {
            const {index, name, value} = action.payload;
            draft.formSteps.data[index]['literals'][name]['value'] = value;
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
        case 'SUBMIT_STARTED': {
            draft.submitting = true;
            draft.errors = {};
            break;
        }
        case 'SET_FETCH_ERRORS': {
            draft.errors = action.payload;
            draft.submitting = false;
            break;
        }
        default:
            throw new Error(`Unknown action type: ${action.type}`);
    }
}


/**
 * Functions to fetch data
 */
const getFormStepsData = async (formUuid, dispatch) => {
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
            // Update the selected authentication plugins
            dispatch({
                type: 'FORM_LOADED',
                payload: {
                    selectedAuthPlugins: response.data.loginOptions.map((plugin, index) => plugin.identifier),
                    formShowProgressIndicator: response.data.showProgressIndicator,
                },
            });
            // Get the form definition data from the form steps
            const formStepsData = await getFormStepsData(formUuid, dispatch);
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

const getAuthPlugins = async (dispatch) => {
    try {
        const response = await get(AUTH_PLUGINS_ENDPOINT);
        dispatch({
            type: 'AUTH_PLUGINS_LOADED',
            payload: response.data
        });
    } catch (e) {
        dispatch({type: 'SET_FETCH_ERRORS', payload: {loadingErrors: e.message}});
    }
};

const getPrefillPlugins = async (dispatch) => {
    try {
        const response = await get(PREFILL_PLUGINS_ENDPOINT);
        dispatch({
            type: 'PREFILL_PLUGINS_LOADED',
            payload: response.data
        });
    } catch (e) {
        dispatch({type: 'SET_FETCH_ERRORS', payload: {loadingErrors: e.message}});
    }
};


const StepsFieldSet = ({ loading=true, submitting=false, loadingErrors, steps=[], ...props }) => {
    if (loadingErrors) {
        return (
            <div className="fetch-error">{loadingErrors}</div>
        );
    }

    if (loading && !loadingErrors) {
        return (<Loader />);
    }

    return (
        <FormSteps steps={steps} submitting={submitting} {...props} />
    );
};

StepsFieldSet.propTypes = {
    loading: PropTypes.bool.isRequired,
    loadingErrors: PropTypes.node,
    steps: PropTypes.arrayOf(PropTypes.object),
    submitting: PropTypes.bool,
};


/**
 * Component to render the form edit page.
 */
const FormCreationForm = ({csrftoken, formUuid, formName, formSlug}) => {
    const initialState = {
        ...initialFormState,
        formUuid: formUuid,
        formName: formName,
        formSlug: formSlug,
        newForm: !formUuid,
    };
    const [state, dispatch] = useImmerReducer(reducer, initialState);

    useAsync(async () => {
        // The available prefill plugins should be loaded before the form definitions, because the requiresAuth field
        // is used to check if a form step needs an additional auth plugin (and to generate related warnings)
        await getPrefillPlugins(dispatch);

        const promises = [
            getFormData(formUuid, dispatch),
            getFormDefinitions(dispatch),

        ];
        await Promise.all(promises);
        // We want the data of all available plugins to be loaded after the form data has been loaded,
        // so that once the checkboxes are rendered they are directly checked/unchecked
        await getAuthPlugins(dispatch);
    }, []);

    /**
     * Functions for handling events
     */
    const setFormSlug = (event) => {
        // do nothing if there's already a slug set
        if (formSlug) return;

        // sort-of taken from Django's jquery prepopulate module
        const newSlug = URLify(event.target.value, 100, false);
        onFieldChange({
            target: {
                name: 'formSlug',
                value: newSlug,
            }
        });
    };

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
            payload: {index: index}
        });
    };

    const onAddStep = (event) => {
        event.preventDefault();
        dispatch({
            type: 'ADD_STEP',
        });
    };

    const onStepReplace = (index, formDefinitionUrl) => {
        dispatch({
            type: 'FORM_DEFINITION_CHOSEN',
            payload: {
                index: index,
                formDefinitionUrl,
            }
        });
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

    const onStepFieldChange = (index, event) => {
        const { name, value } = event.target;
        dispatch({
            type: 'STEP_FIELD_CHANGED',
            payload: {name, value, index},
        });
    };

    const onStepLiteralFieldChange = (index, event) => {
        const { name, value } = event.target;
        dispatch({
            type: 'STEP_LITERAL_FIELD_CHANGED',
            payload: {name, value, index},
        });
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
        dispatch({type: 'SUBMIT_STARTED'});

        // Update the form
        const formData = {
            name: state.formName,
            slug: state.formSlug,
            authenticationBackends: state.selectedAuthPlugins,
            showProgressIndicator: state.formShowProgressIndicator,
        };

        const createOrUpdate = state.newForm ? post : put;
        const endPoint = state.newForm ? FORM_ENDPOINT : `${FORM_ENDPOINT}/${state.formUuid}`;

        try {
            var formResponse = await createOrUpdate(
                endPoint,
                csrftoken,
                formData,
            );

            if (!formResponse.ok) {
                throw new Error('An error occurred while saving the form.');
            }
            var formUuid = formResponse.data.uuid;

        } catch (e) {
            dispatch({type: 'SET_FETCH_ERRORS', payload: formResponse.data});
            window.scrollTo(0, 0);
            return;
        }

        // Update/create form definitions and then form steps
        for ( let index = 0; index < state.formSteps.data.length; index++) {
            const step = state.formSteps.data[index];
            try {
                // First update/create the form definitions
                const isNewFormDefinition = !!step.formDefinition;
                const definitionCreateOrUpdate = isNewFormDefinition ? put : post;
                const definitionEndpoint = step.formDefinition ? step.formDefinition : `${FORM_DEFINITIONS_ENDPOINT}`;

                var definitionResponse = await definitionCreateOrUpdate(
                    definitionEndpoint,
                    csrftoken,
                    {
                        name: step.name,
                        slug: step.slug,
                        configuration: step.configuration,
                        loginRequired: step.loginRequired,
                    }
                )
                if (!definitionResponse.ok) {
                    throw new FormException(
                        'An error occurred while updating the form definitions',
                        definitionResponse.data
                    );
                }

                // Then update the form step
                const stepCreateOrUpdate = step.url ? put : post;
                const stepEndpoint = step.url ? step.url : `${FORM_ENDPOINT}/${formUuid}/steps`;

                var stepResponse = await stepCreateOrUpdate(
                    stepEndpoint,
                    csrftoken,
                    {
                        name: step.name,
                        slug: step.slug,
                        index: index,
                        formDefinition: definitionResponse.data.url,
                        literals: {
                            nextText: {
                                value: step.literals.nextText.value
                            },
                            saveText: {
                                value: step.literals.saveText.value
                            },
                            previousText: {
                                value: step.literals.previousText.value
                            },
                        }
                    }
                );
                if (!stepResponse.ok) {
                    throw new FormException('An error occurred while updating the form steps.', stepResponse.data);
                }
            } catch (e) {
                let formStepsErrors = new Array(state.formSteps.data.length);
                formStepsErrors[index] = e.details;
                dispatch({type: 'SET_FETCH_ERRORS', payload: {formSteps: formStepsErrors}});
                window.scrollTo(0, 0);
                return;
            }
        }

        if (state.stepsToDelete.length) {
            for (const step of state.stepsToDelete) {
                // Steps that were added but are not saved in the backend yet don't have a URL.
                if (!step) return;

                try {
                     var response = await apiDelete(step, csrftoken);
                     if (!response.ok) {
                         throw new Error('An error occurred while deleting form steps.');
                    }
                } catch (e) {
                    dispatch({type: 'SET_FETCH_ERRORS', payload: {submissionError: e.message}});
                    window.scrollTo(0, 0);
                    return;
                }

            }
        }

        // redirect back to list/overview page
        window.location = ADMIN_PAGE;
    };

    const onAuthPluginChange = (event) => {
        const pluginId = event.target.value;
        dispatch({
            type: 'TOGGLE_AUTH_PLUGIN',
            payload: pluginId,
        })
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
                        <TextInput value={state.formName} onChange={onFieldChange} onBlur={setFormSlug} />
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
                <FormRow>
                    <AuthPluginField
                        loading={state.availableAuthPlugins.loading}
                        availableAuthPlugins={state.availableAuthPlugins.data}
                        selectedAuthPlugins={state.selectedAuthPlugins}
                        onChange={onAuthPluginChange}
                        errors={state.errors.authPlugins}
                    />
                </FormRow>

                <FormRow>
                    <Checkbox
                        name="formShowProgressIndicator"
                        label="Show progress indicator"
                        helpText="Whether the step progression should be displayed in the UI or not."
                        checked={state.formShowProgressIndicator}
                        errors={state.errors.showProgressIndicator}
                        onChange={ (event) => onFieldChange({target: {name: event.target.name, value: !state.formShowProgressIndicator}}) }
                    />
                </FormRow>
            </Fieldset>

            <Fieldset title="Form design">
                <FormDefinitionsContext.Provider value={state.formDefinitions}>
                    <PluginsContext.Provider value={{
                        availableAuthPlugins: state.availableAuthPlugins,
                        selectedAuthPlugins: state.selectedAuthPlugins,
                        availablePrefillPlugins: state.availablePrefillPlugins
                    }}>
                        <StepsFieldSet
                            steps={state.formSteps.data}
                            loading={state.formSteps.loading}
                            loadingErrors={state.errors.loadingErrors}
                            onEdit={onStepEdit}
                            onFieldChange={onStepFieldChange}
                            onLiteralFieldChange={onStepLiteralFieldChange}
                            onDelete={onStepDelete}
                            onReorder={onStepReorder}
                            onReplace={onStepReplace}
                            onAdd={onAddStep}
                            submitting={state.submitting}
                            errors={state.errors.formSteps}
                        />
                    </PluginsContext.Provider>
                </FormDefinitionsContext.Provider>
            </Fieldset>

            <SubmitRow onSubmit={onSubmit} isDefault />
            { !state.newForm ?
                <SubmitRow extraClassName="submit-row-extended">
                    <input
                        type="submit"
                        value="Kopiëren"
                        name="_copy"
                        title="Duplicate this form"
                    />
                    <input
                        type="submit"
                        value="Exporteren"
                        name="_export"
                        title="Export this form"
                    />
                </SubmitRow> : null
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
