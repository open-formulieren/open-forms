import React from 'react';
import {useImmerReducer} from 'use-immer';
import PropTypes from 'prop-types';
import useAsync from 'react-use/esm/useAsync';

import {FormException} from "../../../utils/exception";
import {apiDelete, get, post, put} from '../../../utils/fetch';
import Field from '../forms/Field';
import FormRow from '../forms/FormRow';
import Fieldset from '../forms/Fieldset';
import SubmitRow from "../forms/SubmitRow";
import Loader from '../Loader';
import {FormDefinitionsContext, PluginsContext} from './Context';
import FormSteps from './FormSteps';
import { FORM_ENDPOINT, FORM_DEFINITIONS_ENDPOINT, ADMIN_PAGE,
            REGISTRATION_BACKENDS_ENDPOINT, AUTH_PLUGINS_ENDPOINT, PREFILL_PLUGINS_ENDPOINT } from './constants';
import TinyMCEEditor from "./Editor";
import FormMetaFields from './FormMetaFields';
import FormObjectTools from "./FormObjectTools";

const initialFormState = {
    form: {
        name: '',
        uuid: '',
        slug: '',
        showProgressIndicator: true,
        active: true,
        isDeleted: false,
        maintenanceMode: false,
        submissionConfirmationTemplate: '',
        canSubmit: true,
    },
    literals: {
        beginText: {
            value: ''
        },
        previousText: {
            value: ''
        },
        changeText: {
            value: ''
        },
        confirmText: {
            value: ''
        },
    },
    newForm: true,
    formSteps: {
        loading: true,
        data: [],
    },
    errors: {},
    formDefinitions: {},
    availableRegistrationBackends: {
        loading: true,
        data: []
    },
    availableAuthPlugins: {
        loading: true,
        data: {}
    },
    availablePrefillPlugins: {
        loading: true,
        data: {}
    },
    selectedRegistrationBackend: '',
    selectedAuthPlugins: [],
    stepsToDelete: [],
    submitting: false,
};

const newStepData = {
    configuration:  {display: 'form'},
    formDefinition: '',
    slug: '',
    url: '',
    literals: {
        previousText: {
            value: ''
        },
        saveText: {
            value: ''
        },
        nextText: {
            value: ''
        },
    },
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
        case 'FORM_CREATED': {
            draft.newForm = false;
            draft.form = action.payload;
            break;
        }
        case 'FIELD_CHANGED': {
            const { name, value } = action.payload;
            // names are prefixed like `form.foo` and `literals.bar`
            const [prefix, fieldName] = name.split('.');

            switch (prefix) {
                case 'form': {
                    draft.form[fieldName] = value;
                    break;
                }
                case 'literals': {
                    draft.literals[fieldName].value = value;
                    break;
                }
                default: {
                    throw new Error(`Unknown prefix: ${prefix}`);
                }
            }
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
        case 'REGISTRATION_BACKENDS_LOADED': {
            const data = action.payload.map(backend => [backend.id, backend.label]);
            draft.availableRegistrationBackends = {
                loading: false,
                data
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
        case 'CHANGE_REGISTRATION_BACKEND': {
            draft.selectedRegistrationBackend = action.payload;
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
                    literals: {
                        previousText: {
                            value: ''
                        },
                        saveText: {
                            value: ''
                        },
                        nextText: {
                            value: ''
                        },
                    },
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
                    form: response.data,
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

const getRegistrationBackends = async (dispatch) => {
    try {
        const response = await get(REGISTRATION_BACKENDS_ENDPOINT);
        dispatch({
            type: 'REGISTRATION_BACKENDS_LOADED',
            payload: response.data
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
const FormCreationForm = ({csrftoken, formUuid, formName, formSlug,
                              formBeginText, formPreviousText, formChangeText, formConfirmText, formHistoryUrl }) => {
    const initialState = {
        ...initialFormState,
        form: {
            ...initialFormState.form,
            uuid: formUuid,
            name: formName,
            slug: formSlug,
        },
        literals: {
            beginText: {
                value: formBeginText
            },
            previousText: {
                value: formPreviousText
            },
            changeText: {
                value: formChangeText
            },
            confirmText: {
                value: formConfirmText
            },
        },
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
            getRegistrationBackends(dispatch),
        ];
        await Promise.all(promises);
        // We want the data of all available plugins to be loaded after the form data has been loaded,
        // so that once the checkboxes are rendered they are directly checked/unchecked
        await getAuthPlugins(dispatch);
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
            ...state.form,
            literals: {
                beginText: {
                    value: state.literals.beginText.value
                },
                previousText: {
                    value: state.literals.previousText.value
                },
                changeText: {
                    value: state.literals.changeText.value
                },
                confirmText: {
                    value: state.literals.confirmText.value
                }
            },
            registrationBackend: state.selectedRegistrationBackend,
            authenticationBackends: state.selectedAuthPlugins,
        };

        const createOrUpdate = state.newForm ? post : put;
        const endPoint = state.newForm ? FORM_ENDPOINT : `${FORM_ENDPOINT}/${state.form.uuid}`;

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
            dispatch({type: 'FORM_CREATED', payload: formResponse.data});

        } catch (e) {
            dispatch({type: 'SET_FETCH_ERRORS', payload: e.message});
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

        // Save this new version of the form in the "form version control"
        try {
            var versionResponse = await post(
                `${FORM_ENDPOINT}/${formUuid}/versions`,
                csrftoken
            );
            if (!versionResponse.ok) {
                throw new Error('An error occurred while saving the form version.');
            }
        } catch (e) {
            dispatch({type: 'SET_FETCH_ERRORS', payload: e.message});
            window.scrollTo(0, 0);
            return;
        }

        // redirect back to list/overview page
        window.location = ADMIN_PAGE;
    };

    const onRegistrationBackendChange = (event) => {
        const registrationBackend = event.target.value;
        dispatch({
            type: 'CHANGE_REGISTRATION_BACKEND',
            payload: registrationBackend,
        })
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
            <FormObjectTools
                isLoading={state.formSteps.loading || state.availableAuthPlugins.loading ||
                            state.availableRegistrationBackends.loading || state.availablePrefillPlugins.loading}
                historyUrl={formHistoryUrl}
            />

            <h1>Form wijzigen</h1>

            {Object.keys(state.errors).length ? <div className='fetch-error'>The form is invalid. Please correct the errors below.</div> : null}
            <FormMetaFields
                form={state.form}
                literals={state.literals}
                onChange={onFieldChange}
                errors={state.error}
                availableRegistrationBackends={state.availableRegistrationBackends}
                selectedRegistrationBackend={state.selectedRegistrationBackend}
                onRegistrationBackendChange={onRegistrationBackendChange}
                availableAuthPlugins={state.availableAuthPlugins}
                selectedAuthPlugins={state.selectedAuthPlugins}
                onAuthPluginChange={onAuthPluginChange}
            />

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

            <Fieldset title="Submission confirmation template">
                <FormRow>
                    <Field
                        name="SubmissionConfirmationTemplate"
                        label="Submission page content"
                        helpText="The content of the submission confirmation page. It can contain variables that will be templated from the submitted form data. If not specified, the global template will be used."
                        errors={state.errors.submissionConfirmationTemplate}
                    >
                        <TinyMCEEditor
                            content={state.form.submissionConfirmationTemplate}
                            onEditorChange={(newValue, editor) => onFieldChange(
                                {target: {name: 'form.submissionConfirmationTemplate', value: newValue}}
                            )}
                        />
                    </Field>
                </FormRow>
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
    formBeginText: PropTypes.string.isRequired,
    formPreviousText: PropTypes.string.isRequired,
    formChangeText: PropTypes.string.isRequired,
    formConfirmText: PropTypes.string.isRequired,
    formHistoryUrl: PropTypes.string.isRequired,
};

export { FormCreationForm };
