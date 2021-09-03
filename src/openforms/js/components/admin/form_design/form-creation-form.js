import zip from 'lodash/zip';
import React from 'react';
import {useImmerReducer} from 'use-immer';
import PropTypes from 'prop-types';
import useAsync from 'react-use/esm/useAsync';
import {Tab, Tabs, TabList, TabPanel} from 'react-tabs';
import {FormattedMessage, useIntl} from 'react-intl';

import {FormException} from '../../../utils/exception';
import {apiDelete, get, post, put} from '../../../utils/fetch';
import Field from '../forms/Field';
import FormRow from '../forms/FormRow';
import Fieldset from '../forms/Fieldset';
import SubmitRow from '../forms/SubmitRow';
import Loader from '../Loader';
import {FormDefinitionsContext, PluginsContext} from './Context';
import FormSteps from './FormSteps';
import {
    FORM_ENDPOINT,
    FORM_DEFINITIONS_ENDPOINT,
    ADMIN_PAGE,
    REGISTRATION_BACKENDS_ENDPOINT,
    AUTH_PLUGINS_ENDPOINT,
    PREFILL_PLUGINS_ENDPOINT,
    PAYMENT_PLUGINS_ENDPOINT,
    LOGICS_ENDPOINT,
} from './constants';
import {loadPlugins, PluginLoadingError, saveLogicRules} from './data';
import TinyMCEEditor from './Editor';
import FormMetaFields from './FormMetaFields';
import FormObjectTools from './FormObjectTools';
import RegistrationFields from './RegistrationFields';
import PaymentFields from './PaymentFields';
import ProductFields from './ProductFields';
import TextLiterals from './TextLiterals';
import DataRemoval from './DataRemoval';
import {FormLogic, EMPTY_RULE} from './FormLogic';
import {getFormComponents} from './utils';

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
        registrationBackend: '',
        registrationBackendOptions: {},
        product: null,
        paymentBackend: '',
        paymentBackendOptions: {},
        submissionsRemovalOptions: {},
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
    formSteps: [],
    errors: {},
    formDefinitions: [],
    availableRegistrationBackends: [],
    availableAuthPlugins: [],
    availablePrefillPlugins: [],
    selectedAuthPlugins: [],
    availablePaymentBackends: [],
    stepsToDelete: [],
    submitting: false,
    logicRules: [],
    logicRulesToDelete: [],
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
                case 'submissionsRemovalOptions':
                    draft.form.submissionsRemovalOptions[fieldName] = value;
                    break;
                default: {
                    throw new Error(`Unknown prefix: ${prefix}`);
                }
            }
            break;
        }
        case 'PLUGINS_LOADED': {
            const {stateVar, data} = action.payload;
            draft[stateVar] = data;
            break;
        }
        case 'FORM_STEPS_LOADED': {
            draft.formSteps = action.payload;
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
            draft.stepsToDelete.push(draft.formSteps[index].url);

            const unchangedSteps = draft.formSteps.slice(0, index);
            const updatedSteps = draft.formSteps.slice(index+1).map((step) => {
                step.index = step.index - 1;
                return step;
            });
            draft.formSteps = [...unchangedSteps, ...updatedSteps];
            break;
        }
        case 'ADD_STEP': {
            const newIndex = draft.formSteps.length;
            const emptyStep = {
                ...newStepData,
                index: newIndex,
                name: `Stap ${newIndex + 1}`,
            };
            draft.formSteps = draft.formSteps.concat([emptyStep]);
            break;
        }
        case 'FORM_DEFINITION_CHOSEN': {
            const {index, formDefinitionUrl} = action.payload;
            if (!formDefinitionUrl) {
                draft.formSteps[index] = {
                    ...draft.formSteps[index],
                    ...newStepData,
                    // if we're creating a new form definition, mark the step no longer as new since a decision
                    // was made (re-use one or create a new one)
                    isNew: false,
                };
            } else {
                const { configuration, name, slug } = draft.formDefinitions.find( fd => fd.url === formDefinitionUrl);
                const { url } = draft.formSteps[index];
                draft.formSteps[index] = {
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
            // const currentConfiguration = original(draft.formSteps[index].configuration);
            draft.formSteps[index].configuration = configuration;
            break;
        }
        case 'STEP_FIELD_CHANGED': {
            const {index, name, value} = action.payload;
            draft.formSteps[index][name] = value;
            break;
        }
        case 'STEP_LITERAL_FIELD_CHANGED': {
            const {index, name, value} = action.payload;
            draft.formSteps[index]['literals'][name]['value'] = value;
            break;
        }
        case 'MOVE_UP_STEP': {
            const index = action.payload;
            if (index <= 0 || index >= draft.formSteps.length) break;

            let updatedSteps = draft.formSteps.slice(0, index-1);
            updatedSteps = updatedSteps.concat([{...draft.formSteps[index], ...{index: index-1}}]);
            updatedSteps = updatedSteps.concat([{...draft.formSteps[index-1], ...{index: index}}]);

            draft.formSteps = [...updatedSteps, ...draft.formSteps.slice(index+1)];
            break;
        }
        /**
         * Form Logic rules actions
         */
        case 'ADD_RULE': {
            const {form: {url}} = draft;
            draft.logicRules.push({
                ...EMPTY_RULE,
                form: url
            });
            break;
        }
        case 'CHANGED_RULE': {
            const {index, name, value} = action.payload;
            draft.logicRules[index][name] = value;
            break;
        }
        case 'DELETED_RULE': {
            const {index} = action.payload;
            const ruleUuid = draft.logicRules[index].uuid;
            draft.logicRulesToDelete.push(ruleUuid);

            // delete object from state
            const updatedRules = [...draft.logicRules];
            updatedRules.splice(index, 1);
            draft.logicRules = updatedRules;
            break;
        }
        case 'RULES_SAVED': {
            // set the generated UUID from the backend for created rules
            const createdRules = action.payload;
            for (const rule of createdRules) {
                const {uuid, index} = rule;
                draft.logicRules[index].uuid = uuid;
            }

            // clear the state of rules to delete, as they have been deleted
            draft.logicRulesToDelete = [];
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
        // do the requests in parallel
        const requests = [
            get(`${FORM_ENDPOINT}/${formUuid}`),
            getFormStepsData(formUuid, dispatch),
        ];
        const [response, formStepsData] = await Promise.all(requests);
        if (!response.ok) {
            throw new Error('An error occurred while fetching the form.');
        }

        // Set the loaded form data as state.
        const { literals, ...form } = response.data;
        dispatch({
            type: 'FORM_LOADED',
            payload: {
                selectedAuthPlugins: form.loginOptions.map((plugin, index) => plugin.identifier),
                form: form,
                literals: literals,
            },
        });
        dispatch({
            type: 'FORM_STEPS_LOADED',
            payload: formStepsData,
        });
    } catch (e) { // TODO: convert to ErrorBoundary
        dispatch({type: 'SET_FETCH_ERRORS', payload: {loadingErrors: e.message}});
    }
};

const StepsFieldSet = ({ submitting=false, loadingErrors, steps=[], ...props }) => {
    if (loadingErrors) {
        return (
            <div className="fetch-error">{loadingErrors}</div>
        );
    }
    return (
        <FormSteps steps={steps} submitting={submitting} {...props} />
    );
};

StepsFieldSet.propTypes = {
    loadingErrors: PropTypes.node,
    steps: PropTypes.arrayOf(PropTypes.object),
    submitting: PropTypes.bool,
};

/**
 * Component to render the form edit page.
 */
const FormCreationForm = ({csrftoken, formUuid, formHistoryUrl }) => {
    const intl = useIntl();
    const initialState = {
        ...initialFormState,
        form: {
            ...initialFormState.form,
            uuid: formUuid,
        },
        newForm: !formUuid,
    };
    const [state, dispatch] = useImmerReducer(reducer, initialState);

    // load all these plugin registries in parallel
    const pluginsToLoad = [
        {endpoint: PAYMENT_PLUGINS_ENDPOINT, stateVar: 'availablePaymentBackends'},
        {endpoint: FORM_DEFINITIONS_ENDPOINT, stateVar: 'formDefinitions'},
        {endpoint: REGISTRATION_BACKENDS_ENDPOINT, stateVar: 'availableRegistrationBackends'},
        {endpoint: AUTH_PLUGINS_ENDPOINT, stateVar: 'availableAuthPlugins'},
        {endpoint: PREFILL_PLUGINS_ENDPOINT, stateVar: 'availablePrefillPlugins'},
    ];

    // only load rules if we're dealing with an existing form rather than when we're creating
    // a new form.
    if (formUuid) {
        pluginsToLoad.push({endpoint: `${LOGICS_ENDPOINT}?form=${formUuid}`, stateVar: 'logicRules'});
    }

    const {loading} = useAsync(async () => {
        const promises = [
            // TODO: this is a bad function name, refactor
            loadPlugins(pluginsToLoad),
            getFormData(formUuid, dispatch),
        ];
        const [
            pluginsData,
        ] = await Promise.all(promises);

        // load various module plugins & update the state
        for (const group of zip(pluginsToLoad, pluginsData) ) {
            const [plugin, data] = group;
            dispatch({
                type: 'PLUGINS_LOADED',
                payload: {
                    stateVar: plugin.stateVar,
                    data: data,
                }
            });
        }
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

    const onRuleChange = (index, event) => {
        const { name, value } = event.target;
        dispatch({
            type: 'CHANGED_RULE',
            payload: {name, value, index},
        });
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
        for ( let index = 0; index < state.formSteps.length; index++) {
            const step = state.formSteps[index];
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
                        isReusable: step.isReusable,
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
                let formStepsErrors = new Array(state.formSteps.length);
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

        // Update/create logic rules
        try {
            const {logicRules, logicRulesToDelete} = state;
            const createdRules = await saveLogicRules(csrftoken, logicRules, logicRulesToDelete);
            dispatch({
                type: 'RULES_SAVED',
                payload: createdRules,
            });
        } catch (e) {
            console.error(e);
            dispatch({type: 'SET_FETCH_ERRORS', payload: {submissionError: e.message}});
            window.scrollTo(0, 0);
            return;
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

    const onAuthPluginChange = (event) => {
        const pluginId = event.target.value;
        dispatch({
            type: 'TOGGLE_AUTH_PLUGIN',
            payload: pluginId,
        })
    };

    if (loading || state.submitting) {
        return (<Loader />);
    }

    return (
        <>
            <FormObjectTools isLoading={loading} historyUrl={formHistoryUrl} />

            <h1>
                <FormattedMessage defaultMessage="Change form" description="Change form page title" />
            </h1>

            { Object.keys(state.errors).length
                ? (<div className="fetch-error">
                     <FormattedMessage defaultMessage="The form is invalid. Please correct the errors below." description="Generic error message" />
                   </div>)
                : null
            }

            <Tabs>
                <TabList>
                    <Tab>
                        <FormattedMessage defaultMessage="Form" description="Form fields tab title" />
                    </Tab>
                    <Tab>
                        <FormattedMessage defaultMessage="Steps and fields" description="Form design tab title" />
                    </Tab>
                    <Tab>
                        <FormattedMessage defaultMessage="Confirmation" description="Form confirmation options tab title" />
                    </Tab>
                    <Tab>
                        <FormattedMessage defaultMessage="Registration" description="Form registration options tab title" />
                    </Tab>
                    <Tab>
                        <FormattedMessage defaultMessage="Literals" description="Form literals tab title" />
                    </Tab>
                    <Tab>
                        <FormattedMessage defaultMessage="Product" description="Product tab title" />
                    </Tab>
                    <Tab>
                        <FormattedMessage defaultMessage="Payment" description="Payment tab title" />
                    </Tab>
                    <Tab>
                        <FormattedMessage defaultMessage="Data removal" description="Data removal tab title" />
                    </Tab>
                    <Tab>
                        <FormattedMessage defaultMessage="Logic" description="Form logic tab title" />
                    </Tab>
                </TabList>

                <TabPanel>
                    <FormMetaFields
                        form={state.form}
                        literals={state.literals}
                        onChange={onFieldChange}
                        errors={state.error}
                        availableAuthPlugins={state.availableAuthPlugins}
                        selectedAuthPlugins={state.selectedAuthPlugins}
                        onAuthPluginChange={onAuthPluginChange}
                    />
                </TabPanel>

                <TabPanel>
                    <Fieldset title={<FormattedMessage defaultMessage="Form design" description="Form design/editor fieldset title" />}>
                        <FormDefinitionsContext.Provider value={state.formDefinitions}>
                            <PluginsContext.Provider value={{
                                availableAuthPlugins: state.availableAuthPlugins,
                                selectedAuthPlugins: state.selectedAuthPlugins,
                                availablePrefillPlugins: state.availablePrefillPlugins
                            }}>
                                <StepsFieldSet
                                    steps={state.formSteps}
                                    loadingErrors={state.errors.loadingErrors}
                                    onEdit={onStepEdit}
                                    onFieldChange={onStepFieldChange}
                                    onLiteralFieldChange={onStepLiteralFieldChange}
                                    onDelete={onStepDelete}
                                    onReorder={onStepReorder}
                                    onReplace={onStepReplace}
                                    onAdd={ (e) => {
                                        e.preventDefault();
                                        dispatch({type: 'ADD_STEP'});
                                    }}
                                    submitting={state.submitting}
                                    errors={state.errors.formSteps}
                                />
                            </PluginsContext.Provider>
                        </FormDefinitionsContext.Provider>
                    </Fieldset>
                </TabPanel>

                <TabPanel>
                    <Fieldset title={<FormattedMessage defaultMessage="Submission confirmation template" description="Submission confirmation fieldset title" />}>
                        <FormRow>
                            <Field
                                name="SubmissionConfirmationTemplate"
                                label={<FormattedMessage defaultMessage="Submission page content" description="Confirmation template label" />}
                                helpText={
                                    <FormattedMessage
                                        defaultMessage="The content of the submission confirmation page. It can contain variables that will be templated from the submitted form data. If not specified, the global template will be used."
                                        description="Confirmation template help text"
                                    />
                                }
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
                </TabPanel>

                <TabPanel>
                    <RegistrationFields
                        backends={state.availableRegistrationBackends}
                        selectedBackend={state.form.registrationBackend}
                        backendOptions={state.form.registrationBackendOptions}
                        onChange={onFieldChange}
                    />
                </TabPanel>

                <TabPanel>
                    <TextLiterals literals={state.literals} onChange={onFieldChange} />
                </TabPanel>

                <TabPanel>
                    <ProductFields selectedProduct={state.form.product} onChange={onFieldChange} />
                </TabPanel>

                <TabPanel>
                    <PaymentFields
                        backends={state.availablePaymentBackends}
                        selectedBackend={state.form.paymentBackend}
                        backendOptions={state.form.paymentBackendOptions}
                        onChange={onFieldChange}
                    />
                </TabPanel>

                <TabPanel>
                    <DataRemoval
                        submissionsRemovalOptions={state.form.submissionsRemovalOptions}
                        onChange={onFieldChange}
                    />
                </TabPanel>

                <TabPanel>
                    <Fieldset title={<FormattedMessage description="Logic fieldset title" defaultMessage="Logic" />}>
                        <FormLogic
                            logicRules={state.logicRules}
                            availableComponents={getFormComponents(state.formSteps)}
                            onChange={onRuleChange}
                            onDelete={(index) => dispatch({type: 'DELETED_RULE', payload: {index: index}})}
                            onAdd={() => dispatch({type: 'ADD_RULE'})}
                        />
                    </Fieldset>
                </TabPanel>
            </Tabs>

            <SubmitRow onSubmit={onSubmit} isDefault />
            { !state.newForm ?
                <SubmitRow extraClassName="submit-row-extended">
                    <input
                        type="submit"
                        value={intl.formatMessage({defaultMessage: 'Copy', description: 'Copy form button'})}
                        name="_copy"
                        title={intl.formatMessage({defaultMessage: 'Duplicate this form', description: 'Copy form button title'})}
                    />
                    <input
                        type="submit"
                        value={intl.formatMessage({defaultMessage: 'Export', description: 'Export form button'})}
                        name="_export"
                        title={intl.formatMessage({defaultMessage: 'Export this form', description: 'Export form button title'})}
                    />
                </SubmitRow> : null
            }
        </>
    );
};


FormCreationForm.propTypes = {
    csrftoken: PropTypes.string.isRequired,
    formUuid: PropTypes.string.isRequired,
    formHistoryUrl: PropTypes.string.isRequired,
};

export { FormCreationForm };
