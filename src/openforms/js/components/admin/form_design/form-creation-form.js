import zip from 'lodash/zip';
import getObjectValue from 'lodash/get';
import set from 'lodash/set';
import groupBy from 'lodash/groupBy';
import React from 'react';
import {useImmerReducer} from 'use-immer';
import PropTypes from 'prop-types';
import useAsync from 'react-use/esm/useAsync';
import {Tab as ReactTab, Tabs, TabList, TabPanel} from 'react-tabs';
import {FormattedMessage, useIntl} from 'react-intl';

import {apiDelete, get, post, put, ValidationErrors} from '../../../utils/fetch';
import FAIcon from '../FAIcon';
import Fieldset from '../forms/Fieldset';
import ValidationErrorsProvider from '../forms/ValidationErrors';
import Loader from '../Loader';
import {FormContext, FormDefinitionsContext, PluginsContext, FormStepsContext} from './Context';
import FormSteps from './FormSteps';
import {
    FORM_ENDPOINT,
    FORM_DEFINITIONS_ENDPOINT,
    REGISTRATION_BACKENDS_ENDPOINT,
    AUTH_PLUGINS_ENDPOINT,
    PREFILL_PLUGINS_ENDPOINT,
    PAYMENT_PLUGINS_ENDPOINT,
    LOGICS_ENDPOINT,
    PRICE_RULES_ENDPOINT,
} from './constants';
import {
    loadPlugins,
    updateOrCreateFormSteps,
    saveLogicRules,
    savePriceRules,
} from './data';
import Appointments, {KEYS as APPOINTMENT_CONFIG_KEYS} from './Appointments';
import FormMetaFields from './FormMetaFields';
import FormObjectTools from './FormObjectTools';
import FormSubmit from './FormSubmit';
import RegistrationFields from './RegistrationFields';
import PaymentFields from './PaymentFields';
import ProductFields from './ProductFields';
import TextLiterals from './TextLiterals';
import DataRemoval from './DataRemoval';
import Confirmation from './Confirmation';
import {FormLogic, EMPTY_RULE} from './FormLogic';
import {PriceLogic, EMPTY_PRICE_RULE} from './PriceLogic';
import {getFormComponents} from './utils';

const initialFormState = {
    form: {
        name: '',
        internalName: '',
        uuid: '',
        url: '',
        slug: '',
        showProgressIndicator: true,
        active: true,
        isDeleted: false,
        maintenanceMode: false,
        submissionConfirmationTemplate: '',
        submissionAllowed: 'yes',
        registrationBackend: '',
        registrationBackendOptions: {},
        product: null,
        paymentBackend: '',
        paymentBackendOptions: {},
        submissionsRemovalOptions: {},
        confirmationEmailTemplate: null,
        confirmationEmailOption: 'global_email',
        explanationTemplate: '',
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
    priceRules: [],
    priceRulesToDelete: [],
    // backend error handling
    validationErrors: [],
    tabsWithErrors: [],
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
    validationErrors: [],
};

// Maps in which Tab the different form fields are displayed.
const FORM_FIELDS_TO_TAB_NAMES = {
    name: 'form',
    internalName: 'form',
    uuid: 'form',
    slug: 'form',
    showProgressIndicator: 'form',
    active: 'form',
    isDeleted: 'form',
    maintenanceMode: 'form',
    submissionConfirmationTemplate: 'submission-confirmation',
    confirmationEmailTemplate: 'submission-confirmation',
    submissionAllowed: 'form',
    registrationBackend: 'registration',
    registrationBackendOptions: 'registration',
    product: 'product-payment',
    paymentBackend: 'product-payment',
    paymentBackendOptions: 'product-payment',
    submissionsRemovalOptions: 'submission-removal-options',
    literals: 'literals',
    explanationTemplate: 'form',
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
            const [prefix, ...rest] = name.split('.');
            const fieldName = rest.join('.');

            switch (prefix) {
                case 'form': {
                    set(draft.form, fieldName, value);
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

            // remove any validation errors
            draft.validationErrors = draft.validationErrors.filter(([key]) => !key.startsWith(name));

            // check which tabs still need the marker and which don't
            const errorsPerTab = groupBy(draft.validationErrors, ([key]) => {
                const [prefix, fieldPrefix] = key.split('.');
                return FORM_FIELDS_TO_TAB_NAMES[fieldPrefix];
            });
            draft.tabsWithErrors = draft.tabsWithErrors.filter(tabId => tabId in errorsPerTab);
            break;
        }
        case 'PLUGINS_LOADED': {
            const {stateVar, data} = action.payload;
            draft[stateVar] = data;
            break;
        }
        case 'FORM_STEPS_LOADED': {
            draft.formSteps = action.payload;
            for (const step of draft.formSteps) {
                step.validationErrors = [];
            }
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
                const { configuration, name, internalName, isReusable, slug } = draft.formDefinitions.find( fd => fd.url === formDefinitionUrl);
                const { url } = draft.formSteps[index];
                draft.formSteps[index] = {
                    configuration,
                    formDefinition: formDefinitionUrl,
                    index,
                    name,
                    internalName,
                    isReusable,
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
                    validationErrors: [],
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
            const step = draft.formSteps[index];
            step[name] = value;
            step.validationErrors = step.validationErrors.filter(([key]) => key !== name);

            const anyStepHasErrors = draft.formSteps.some( step => step.validationErrors.length > 0);
            if (!anyStepHasErrors && draft.tabsWithErrors.includes('form-steps')) {
                draft.tabsWithErrors = draft.tabsWithErrors.filter(tab => tab !== 'form-steps');
            }
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
        case 'APPOINTMENT_CONFIGURATION_CHANGED': {
            // deconstruct the 'event' which holds the information on which config param
            // was changed and to which component it is (now) set.
            const {target: {name, value: selectedComponentKey}} = action.payload;

            // name is in the form "appointments.<key>"
            const [prefix, configKey] = name.split('.');
            const allComponents = Object.values(getFormComponents(draft.formSteps));

            // utility to find the component for a given appointment config option
            const findComponentForConfigKey = (configKey) => {
                const name = `${prefix}.${configKey}`;
                return allComponents.find(component => getObjectValue(component, name, false));
            };

            // first, ensure that if the value was changed, the old component is cleared
            const currentComponentForConfigKey = findComponentForConfigKey(configKey);
            if (currentComponentForConfigKey) {
                // wipe the entire appointments configuration
                set(currentComponentForConfigKey, prefix, {});
            }

            // next, handle setting the config to the new component
            const selectedComponent = allComponents.find(component => component.key === selectedComponentKey);
            set(selectedComponent, name, true);

            // finally, handle the dependencies of all appointment configuration - we need
            // to check and update all keys, even the one that wasn't change, because options
            // can be set in non-logical order in the UI.
            for (const otherConfigKey of APPOINTMENT_CONFIG_KEYS) {
                const relevantComponent = findComponentForConfigKey(otherConfigKey);
                if (!relevantComponent) continue;

                switch (otherConfigKey) {
                    // no dependencies, do nothing
                    case 'showProducts':
                    case 'lastName':
                    case 'birthDate':
                    case 'phoneNumber':
                        break
                    // reverse order without breaks, since every component builds on top of
                    // the others
                    case 'showTimes': {
                        // add the date selection component information
                        const dateComponent = findComponentForConfigKey('showDates');
                        if (dateComponent) set(relevantComponent, `${prefix}.dateComponent`, dateComponent.key);
                    }
                    case 'showDates': {
                        // add the location selection component information
                        const locationComponent = findComponentForConfigKey('showLocations');
                        if (locationComponent) set(relevantComponent, `${prefix}.locationComponent`, locationComponent.key);
                    }
                    case 'showLocations': {
                        // add the product selection component information
                        const productComponent = findComponentForConfigKey('showProducts');
                        if (productComponent) set(relevantComponent, `${prefix}.productComponent`, productComponent.key);
                        break;
                    }
                    default: {
                        throw new Error(`Unknown config key: ${configKey}`);
                    }
                }
            }
            break;
        }
        case 'PROCESS_STEP_VALIDATION_ERRORS': {
            const {index, errors} = action.payload;
            draft.formSteps[index].validationErrors = errors.map(err => [err.name, err.reason]);
            if (!draft.tabsWithErrors.includes('form-steps')) {
                draft.tabsWithErrors.push('form-steps');
            }
            draft.submitting = false;
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
         * Price rules actions
         */
        case 'ADD_PRICE_RULE': {
            const {form: {url}} = draft;
            draft.priceRules.push({
                ...EMPTY_PRICE_RULE,
                form: url
            });
            break;
        }
        case 'CHANGED_PRICE_RULE': {
            const {index, name, value} = action.payload;
            draft.priceRules[index][name] = value;
            break;
        }
        case 'DELETED_PRICE_RULE': {
            const {index} = action.payload;
            const ruleUuid = draft.priceRules[index].uuid;

            // delete object from state
            const updatedRules = [...draft.priceRules];
            updatedRules.splice(index, 1);
            draft.priceRules = updatedRules;
            break;
        }
        case 'PRICE_RULES_SAVED': {
            // set the generated UUID from the backend for created rules
            const createdRules = action.payload;
            for (const rule of createdRules) {
                const {uuid, index} = rule;
                draft.priceRules[index].uuid = uuid;
            }

            // clear the state of rules to delete, as they have been deleted
            draft.priceRulesToDelete = [];
            break;
        }

        /**
         * Validation error handling
         */
        case 'PROCESS_VALIDATION_ERRORS': {
            const {fieldPrefix, errors} = action.payload;
            // process the errors with their field names
            const tabsWithErrors = []
            const prefixedErrors = errors.map( err => {
                const fieldName = err.name.split('.')[0];
                if (!tabsWithErrors.includes(fieldName)) tabsWithErrors.push(FORM_FIELDS_TO_TAB_NAMES[fieldName]);
                let key;
                // literals are tracked separately in the state
                if (fieldPrefix === 'form' && fieldName === 'literals') {
                    key = err.name;
                } else {
                    key = `${fieldPrefix}.${err.name}`;
                }
                return [key, err.reason];
            });
            draft.validationErrors = [...draft.validationErrors, ...prefixedErrors];
            // keep track of which tabs have errors
            draft.tabsWithErrors = [...draft.tabsWithErrors, ...tabsWithErrors];
            draft.submitting = false;
            break;
        }
        /**
         * Misc
         */
        case 'SUBMIT_STARTED': {
            draft.submitting = true;
            draft.errors = {};
            draft.validationErrors = [];
            draft.tabsWithErrors = [];
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
        pluginsToLoad.push({endpoint: `${PRICE_RULES_ENDPOINT}?form=${formUuid}`, stateVar: 'priceRules'});
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

    const onPriceRuleChange = (index, event) => {
        const { name, value } = event.target;
        dispatch({
            type: 'CHANGED_PRICE_RULE',
            payload: {name, value, index},
        });
    };

    const onSubmit = async (event) => {
        const { name: submitAction } = event.target;
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
            var formResponse = await createOrUpdate(endPoint, csrftoken, formData, true);
            // unexpected error
            if (!formResponse.ok) {
                dispatch({type: 'SET_FETCH_ERRORS', payload: `Error ${formResponse.status} from backend`});
                return;
            }
            // ok, good to go
            var {uuid: formUuid, url: formUrl} = formResponse.data;
            dispatch({type: 'FORM_CREATED', payload: formResponse.data});
        } catch (e) {
            if (e instanceof ValidationErrors) {
                dispatch({
                    type: 'PROCESS_VALIDATION_ERRORS',
                    payload: {
                        fieldPrefix: 'form',
                        errors: e.errors,
                    },
                });
                return;
            } else {
                throw e; // re-throw unchanged error, this is unexpected.
            }
        }

        try {
            var stepValidationErrors = await updateOrCreateFormSteps(csrftoken, formUrl, state.formSteps);
        } catch (e) {
            dispatch({type: 'SET_FETCH_ERRORS', payload: {submissionError: e.message}});
            window.scrollTo(0, 0);
            return;
        }

        // dispatch validation errors for errored steps so that they are displayed
        const erroredSteps = stepValidationErrors.filter( erroredStep => !!erroredStep);
        for (const erroredStep of erroredSteps) {
            const {step, error} = erroredStep;
            dispatch({
                type: 'PROCESS_STEP_VALIDATION_ERRORS',
                payload: {
                    index: state.formSteps.indexOf(step),
                    errors: error.errors,
                },
            });
        }
        // stop processing if there are errored steps
        if (erroredSteps.length) {
            return;
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
            const createdRules = await saveLogicRules(formUrl, csrftoken, logicRules, logicRulesToDelete);
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

        // Update/create price rules
        try {
            const {priceRules, priceRulesToDelete} = state;
            const createdPriceRules = await savePriceRules(formUrl, csrftoken, priceRules, priceRulesToDelete);
            dispatch({
                type: 'PRICE_RULES_SAVED',
                payload: createdPriceRules,
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

        // finalize the "transacton".
        //
        // * schedule a success message
        // * obtain the admin URL to redirect to (detail if editing again, add if creating
        //   another object or list page for simple save)
        const messageData = {
            isCreate: state.newForm,
            submitAction: submitAction,
        };
        const messageResponse = await post(`${formUrl}/admin-message`, csrftoken, messageData);
        // this full-page reload ensures that the admin messages are displayed
        window.location = messageResponse.data.redirectUrl;
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

    const availableComponents = getFormComponents(state.formSteps);

    return (
        <ValidationErrorsProvider errors={state.validationErrors}>
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
                    <Tab hasErrors={state.tabsWithErrors.includes('form')}>
                        <FormattedMessage defaultMessage="Form" description="Form fields tab title" />
                    </Tab>
                    <Tab hasErrors={state.tabsWithErrors.includes('form-steps')}>
                        <FormattedMessage defaultMessage="Steps and fields" description="Form design tab title" />
                    </Tab>
                    <Tab hasErrors={state.tabsWithErrors.includes('submission-confirmation')}>
                        <FormattedMessage defaultMessage="Confirmation" description="Form confirmation options tab title" />
                    </Tab>
                    <Tab hasErrors={state.tabsWithErrors.includes('registration')}>
                        <FormattedMessage defaultMessage="Registration" description="Form registration options tab title" />
                    </Tab>
                    <Tab hasErrors={state.tabsWithErrors.includes('literals')}>
                        <FormattedMessage defaultMessage="Literals" description="Form literals tab title" />
                    </Tab>
                    <Tab hasErrors={state.tabsWithErrors.includes('product-payment')}>
                        <FormattedMessage defaultMessage="Product & payment" description="Product & payments tab title" />
                    </Tab>
                    <Tab hasErrors={state.tabsWithErrors.includes('submission-removal-options')}>
                        <FormattedMessage defaultMessage="Data removal" description="Data removal tab title" />
                    </Tab>
                    <Tab>
                        <FormattedMessage defaultMessage="Logic" description="Form logic tab title" />
                    </Tab>
                    <Tab>
                        <FormattedMessage defaultMessage="Appointments" description="Appointments tab title" />
                    </Tab>
                </TabList>

                <TabPanel>
                    <FormMetaFields
                        form={state.form}
                        literals={state.literals}
                        onChange={onFieldChange}
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
                                <FormContext.Provider value={{url: state.form.url}}>
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
                                    />
                                </FormContext.Provider>
                            </PluginsContext.Provider>
                        </FormDefinitionsContext.Provider>
                    </Fieldset>
                </TabPanel>

                <TabPanel>
                    <Confirmation
                        pageTemplate={state.form.submissionConfirmationTemplate}
                        emailOption={state.form.confirmationEmailOption}
                        emailTemplate={state.form.confirmationEmailTemplate || {}}
                        onChange={onFieldChange}
                    />
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
                    <PaymentFields
                        backends={state.availablePaymentBackends}
                        selectedBackend={state.form.paymentBackend}
                        backendOptions={state.form.paymentBackendOptions}
                        onChange={onFieldChange}
                    />
                    <PriceLogic
                        rules={state.priceRules}
                        availableComponents={availableComponents}
                        onChange={onPriceRuleChange}
                        onDelete={(index) => dispatch({type: 'DELETED_PRICE_RULE', payload: {index: index}})}
                        onAdd={() => dispatch({type: 'ADD_PRICE_RULE'})}
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
                        <FormStepsContext.Provider value={state.formSteps}>
                            <FormLogic
                                logicRules={state.logicRules}
                                availableComponents={availableComponents}
                                onChange={onRuleChange}
                                onDelete={(index) => dispatch({type: 'DELETED_RULE', payload: {index: index}})}
                                onAdd={() => dispatch({type: 'ADD_RULE'})}
                            />
                        </FormStepsContext.Provider>
                    </Fieldset>
                </TabPanel>

                <TabPanel>
                    <Appointments
                        availableComponents={availableComponents}
                        onChange={(event) => {
                            dispatch({
                                type: 'APPOINTMENT_CONFIGURATION_CHANGED',
                                payload: event,
                            });
                        }} />
                </TabPanel>
            </Tabs>

            <FormSubmit onSubmit={onSubmit} displayActions={!state.newForm} />

        </ValidationErrorsProvider>
    );
};


const Tab = ({ hasErrors=false, children, ...props }) => {
    const intl = useIntl();
    const customProps = {
        className: [
            'react-tabs__tab',
            {'react-tabs__tab--has-errors': hasErrors},
        ]
    };
    const allProps = {...props, ...customProps};
    const title = intl.formatMessage({
        defaultMessage: 'There are validation errors',
        description: 'Tab validation errors icon title',
    });
    return (
        <ReactTab {...allProps}>
            {children}
            { hasErrors ? <FAIcon icon="exclamation-circle" title={title} /> : null}
        </ReactTab>
    );
};
Tab.tabsRole = 'Tab';

Tab.propTypes = {
    hasErrors: PropTypes.bool,
};


FormCreationForm.propTypes = {
    csrftoken: PropTypes.string.isRequired,
    formUuid: PropTypes.string.isRequired,
    formHistoryUrl: PropTypes.string.isRequired,
};

export { FormCreationForm };
