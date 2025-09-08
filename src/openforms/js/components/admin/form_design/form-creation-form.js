import {produce} from 'immer';
import cloneDeep from 'lodash/cloneDeep';
import groupBy from 'lodash/groupBy';
import set from 'lodash/set';
import sortBy from 'lodash/sortBy';
import zip from 'lodash/zip';
import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';
import {TabList, TabPanel, Tabs} from 'react-tabs';
import useAsync from 'react-use/esm/useAsync';
import {useImmerReducer} from 'use-immer';

import Loader from 'components/admin/Loader';
import Fieldset from 'components/admin/forms/Fieldset';
import ValidationErrorsProvider from 'components/admin/forms/ValidationErrors';
import {WarningIcon} from 'components/admin/icons';
import {APIError, NotAuthenticatedError} from 'utils/exception';
import {post} from 'utils/fetch';
import {getUniqueRandomString} from 'utils/random';

import Confirmation from './Confirmation';
import {APIContext, FormContext} from './Context';
import DataRemoval from './DataRemoval';
import FormAdvancedConfiguration from './FormAdvancedConfiguration';
import FormConfigurationFields from './FormConfigurationFields';
import FormDetailFields from './FormDetailFields';
import {EMPTY_RULE, FormLogic, detectLogicProblems} from './FormLogic';
import FormObjectTools from './FormObjectTools';
import FormSteps from './FormSteps';
import FormSubmit from './FormSubmit';
import {DEFAULT_LANGUAGE} from './LanguageTabs';
import PaymentFields from './PaymentFields';
import PriceLogic from './PriceLogic';
import ProductFields from './ProductFields';
import RegistrationFields from './RegistrationFields';
import {SubmissionLimitFields} from './SubmissionFields';
import Tab from './Tab';
import TextLiterals from './TextLiterals';
import {FormWarnings} from './Warnings';
import {
  AUTH_PLUGINS_ENDPOINT,
  CATEGORIES_ENDPOINT,
  DMN_PLUGINS_ENDPOINT,
  FORM_DEFINITIONS_ENDPOINT,
  LANGUAGE_INFO_ENDPOINT,
  PAYMENT_PLUGINS_ENDPOINT,
  PREFILL_PLUGINS_ENDPOINT,
  REGISTRATION_BACKENDS_ENDPOINT,
  REGISTRATION_VARIABLES_ENDPOINT,
  STATIC_VARIABLES_ENDPOINT,
  THEMES_ENDPOINT,
} from './constants';
import {loadForm, loadFromBackend, saveCompleteForm} from './data';
import {updateWarningsValidationError} from './logic/utils';
import {BACKEND_OPTIONS_FORMS} from './registrations';
import {
  assignInitialTranslations,
  initialConfirmationEmailTranslations,
  initialFormTranslations,
  initialStepTranslations,
} from './translations';
import useConfirm from './useConfirm';
import {
  checkKeyChange,
  findComponent,
  getFormComponents,
  getFormStep,
  getPathToComponent,
  getUniqueKey,
  parseValidationErrors,
  slugify,
  transformInitialValue,
  updateKeyReferencesInLogic,
  updateRemovedKeyInLogic,
} from './utils';
import VariablesEditor from './variables/VariablesEditor';
import {EMPTY_VARIABLE} from './variables/constants';
import {
  checkForDuplicateKeys,
  getFormVariables,
  updateFormVariables,
  variableHasErrors,
} from './variables/utils';

const initialFormState = {
  form: {
    internalName: '',
    uuid: '',
    url: '',
    slug: '',
    showProgressIndicator: true,
    showSummaryProgress: false,
    displayMainWebsiteLink: true,
    includeConfirmationPageContentInPdf: true,
    active: true,
    activateOn: '',
    deactivateOn: '',
    category: '',
    isDeleted: false,
    maintenanceMode: false,
    translationEnabled: false,
    submissionAllowed: 'yes',
    submissionLimit: null,
    submission_counter: 0,
    suspensionAllowed: true,
    askPrivacyConsent: 'global_setting',
    askStatementOfTruth: 'global_setting',
    registrationBackends: [],
    product: null,
    paymentBackend: '',
    paymentBackendOptions: {},
    submissionsRemovalOptions: {},
    sendConfirmationEmail: true,
    confirmationEmailTemplate: {subject: '', content: '', translations: {}},
    autoLoginAuthenticationBackend: '',
    translations: {},
    appointmentOptions: {isAppointment: false},
    brpPersonenRequestOptions: {
      brpPersonenPurposeLimitationHeaderValue: '',
      brpPersonenProcessingHeaderValue: '',
    },
    authBackends: [],
    newRendererEnabled: false,
  },
  newForm: true,
  formSteps: [],
  errors: {},
  formDefinitions: [],
  reusableFormDefinitionsLoaded: false,
  availableRegistrationBackends: [],
  availableAuthPlugins: [],
  availablePrefillPlugins: [],
  availableDMNPlugins: [],
  selectedAuthPlugins: [],
  availablePaymentBackends: [],
  availableCategories: [],
  availableThemes: [],
  languageInfo: {languages: [], current: ''},
  stepsToDelete: [],
  submitting: false,
  logicRules: [],
  formVariables: [],
  staticVariables: [],
  // backend error handling
  validationErrors: [],
  tabsWithErrors: [],
};

const newStepData = {
  configuration: {display: 'form'},
  formDefinition: '',
  slug: '',
  url: '',
  _generatedId: '', // Consumers should generate this if there is no form definition url
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
  showSummaryProgress: 'form',
  active: 'form',
  category: 'form',
  isDeleted: 'form',
  activateOn: 'form',
  deactivateOn: 'form',
  maintenanceMode: 'form',
  translationEnabled: 'form',
  confirmationEmailTemplate: 'submission-confirmation',
  submissionAllowed: 'form',
  registrationBackends: 'registration',
  submissionLimit: 'submission',
  product: 'product-payment',
  paymentBackend: 'product-payment',
  paymentBackendOptions: 'product-payment',
  submissionsRemovalOptions: 'submission-removal-options',
  logicRules: 'logic-rules',
  variables: 'variables',
  appointmentOptions: 'form',
  brpPersonenRequestOptions: 'advanced-configuration',
  newRendererEnabled: 'form',
};

const TRANSLATION_FIELD_TO_TAB_NAMES = {
  name: 'form',
  introductionPageContent: 'form',
  explanationTemplate: 'form',
  submissionConfirmationTemplate: 'submission-confirmation',
  beginText: 'literals',
  previousText: 'literals',
  changeText: 'literals',
  confirmText: 'literals',
};

function reducer(draft, action) {
  switch (action.type) {
    /**
     * Form-level actions
     */
    case 'BACKEND_DATA_LOADED': {
      const {supportingData, formData} = action.payload;
      const {form, selectedAuthPlugins, steps, variables, logicRules} = formData;

      for (const [stateVar, data] of Object.entries(supportingData)) {
        draft[stateVar] = data;
      }

      if (form) draft.form = form;
      if (selectedAuthPlugins) draft.selectedAuthPlugins = selectedAuthPlugins;
      if (variables) draft.formVariables = variables;
      if (logicRules)
        draft.logicRules = logicRules.map(rule => ({
          ...rule,
          _logicType: rule.isAdvanced ? 'simple' : 'advanced',
          // if there's a description set already, it may not be mutated
          _mayGenerateDescription: !rule.description,
        }));

      if (!draft.form.confirmationEmailTemplate) {
        draft.form.confirmationEmailTemplate = {subject: '', content: '', translations: {}};
      }

      // set initial translations if needed
      for (const {code} of draft.languageInfo.languages) {
        assignInitialTranslations(draft.form.translations, code, initialFormTranslations);
        assignInitialTranslations(
          draft.form.confirmationEmailTemplate.translations,
          code,
          initialConfirmationEmailTranslations
        );
      }

      const formDefinitions = Object.fromEntries(draft.formDefinitions.map(fd => [fd.url, fd]));

      // Add component FormVariables and the step validation errors to the state
      draft.formSteps = steps;
      let stepsFormVariables = [];
      for (const step of draft.formSteps) {
        // merge form definition translations into form step state var
        const fd = formDefinitions[step.formDefinition];
        for (const [code, translations] of Object.entries(fd.translations)) {
          step.translations[code] = {...step.translations[code], ...translations};
        }

        // add variables
        stepsFormVariables = stepsFormVariables.concat(
          getFormVariables(step.formDefinition, step.configuration)
        );
        step.validationErrors = [];
      }
      draft.formVariables = draft.formVariables.concat(stepsFormVariables);
      draft.validationErrors = checkForDuplicateKeys(
        draft.formVariables,
        draft.staticVariables,
        draft.validationErrors
      );
      break;
    }
    case 'REUSABLE_FORM_DEFINITIONS_LOADED': {
      const reusableFormDefinitions = action.payload;
      const formDefinitionsIds = draft.formDefinitions.map(fd => fd.uuid);
      draft.formDefinitions = [
        ...draft.formDefinitions,
        ...reusableFormDefinitions.filter(fd => !formDefinitionsIds.includes(fd.uuid)),
      ];
      draft.reusableFormDefinitionsLoaded = true;
      break;
    }
    case 'ADD_REGISTRATION': {
      const {key} = action.payload;
      draft.form.registrationBackends.push({
        key: key,
        name: '',
        backend: '',
        options: {},
      });
      break;
    }
    case 'DELETE_REGISTRATION': {
      const {key} = action.payload;
      draft.form.registrationBackends = draft.form.registrationBackends.filter(
        backend => backend.key != key
      );
      break;
    }

    case 'FIELD_CHANGED': {
      const {name, value} = action.payload;
      const nameBits = name.split('.');

      // assign new value to state draft
      set(draft, name, value);

      const componentContextPath = nameBits.splice(0, nameBits.length - 1).join('.');

      // remove any validation errors
      draft.validationErrors = draft.validationErrors.filter(([key]) => {
        // The validation error contains either the name of the changed field exactly
        // or a field that is nested inside the changed field.
        const clearSpecificFieldError = key.startsWith(name);
        // A field has changed in a section with non field errors, so we need to clear
        // those.
        const errorBits = key.split('.');
        const errorContextPath = errorBits.splice(0, errorBits.length - 1).join('.');
        const clearNonFieldError =
          errorContextPath.startsWith(componentContextPath) &&
          errorBits[errorBits.length - 1] === 'nonFieldErrors';

        return !(clearSpecificFieldError || clearNonFieldError);
      });

      // check which tabs still need the marker and which don't
      const errorsPerTab = groupBy(draft.validationErrors, ([key]) => {
        const [prefix, fieldPrefix] = key.split('.');
        switch (fieldPrefix) {
          case 'translations': {
            const [, , , translationField] = key.split('.');
            return TRANSLATION_FIELD_TO_TAB_NAMES[translationField];
          }
          default: {
            return FORM_FIELDS_TO_TAB_NAMES[fieldPrefix];
          }
        }
      });
      draft.tabsWithErrors = draft.tabsWithErrors.filter(tabId => tabId in errorsPerTab);
      break;
    }
    case 'TOGGLE_AUTH_PLUGIN': {
      const pluginId = action.payload;
      if (draft.selectedAuthPlugins.includes(pluginId)) {
        draft.selectedAuthPlugins = draft.selectedAuthPlugins.filter(id => id !== pluginId);
        if (draft.form.autoLoginAuthenticationBackend === pluginId) {
          draft.form.autoLoginAuthenticationBackend = '';
        }
        // If an auth plugin is unselected, remove its backend config
        draft.form.authBackends = draft.form.authBackends.filter(
          authBackend => authBackend.backend !== pluginId
        );
      } else {
        draft.selectedAuthPlugins = [...draft.selectedAuthPlugins, pluginId];
        const plugin = draft.availableAuthPlugins.find(backend => backend.id === pluginId);
        draft.form.authBackends.push({
          backend: pluginId,
          options: {},
        });
      }
      break;
    }
    /**
     * FormStep-level actions
     */
    case 'DELETE_STEP': {
      const {index} = action.payload;

      const stepToDelete = draft.formSteps[index];

      // Delete all component FormVariables associated with the step
      draft.formVariables = draft.formVariables.filter(
        variable =>
          !(
            variable.formDefinition === stepToDelete.formDefinition ||
            variable.formDefinition === stepToDelete._generatedId
          )
      );

      draft.stepsToDelete.push(stepToDelete.url);

      const unchangedSteps = draft.formSteps.slice(0, index);
      const updatedSteps = draft.formSteps.slice(index + 1).map(step => {
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
        translations: Object.fromEntries(
          draft.languageInfo.languages.map(language => [language.code, initialStepTranslations])
        ),
      };
      draft.formSteps.push(emptyStep);
      break;
    }
    case 'FORM_DEFINITION_CHOSEN': {
      const {index, formDefinitionUrl} = action.payload;
      if (!formDefinitionUrl) {
        // creating a new form definition
        draft.formSteps[index] = {
          ...draft.formSteps[index],
          ...newStepData,
          _generatedId: getUniqueRandomString(),
          // if we're creating a new form definition, mark the step no longer as new since a decision
          // was made (re-use one or create a new one)
          isNew: false,
        };
      } else {
        // re-using an existing form definition
        const fd = draft.formDefinitions.find(fd => fd.url === formDefinitionUrl);
        const {configuration, name, internalName, isReusable, translations} = fd;
        const {url} = draft.formSteps[index];

        const stepTranslations = Object.fromEntries(
          draft.languageInfo.languages.map(({code}) => {
            const formDefinitionTranslations = translations[code];
            const mergedTranslations = {
              ...initialStepTranslations,
              ...formDefinitionTranslations,
            };
            return [code, mergedTranslations];
          })
        );

        draft.formSteps[index] = {
          configuration,
          formDefinition: formDefinitionUrl,
          index,
          name,
          internalName,
          isReusable,
          slug: slugify(name),
          url,
          isNew: false,
          validationErrors: [],
          translations: stepTranslations,
        };

        // Add form variables for the reusable configuration
        draft.formVariables = draft.formVariables.concat(
          getFormVariables(formDefinitionUrl, configuration)
        );
      }
      break;
    }
    case 'EDIT_STEP': {
      const {index, configuration} = action.payload;
      draft.formSteps[index].configuration = configuration;
      break;
    }
    case 'EDIT_STEP_COMPONENT_MUTATED': {
      const {mutationType, schema, args, formDefinition} = action.payload;

      let originalComp;
      let isNew;
      let configuration;
      switch (mutationType) {
        case 'changed': {
          originalComp = args[0];
          configuration = args[1];
          isNew = args[4];
          break;
        }
        case 'removed': {
          originalComp = null;
          configuration = args[0];
          isNew = false;
          break;
        }
        default:
          throw new Error(`Unknown mutation type '${mutationType}'`);
      }

      // Check if a key has been changed and if the logic rules need updating
      const hasKeyChanged = checkKeyChange(mutationType, schema, originalComp);
      if (mutationType === 'changed' && hasKeyChanged) {
        updateKeyReferencesInLogic(draft.logicRules, originalComp.key, schema.key);
      } else if (mutationType === 'removed') {
        updateRemovedKeyInLogic(draft.logicRules, schema.key);
      }

      // Issue #1729 - Workaround for bug in FormIO
      if (mutationType === 'changed' && !schema.multiple && Array.isArray(schema.defaultValue)) {
        // Formio has a getter for the:
        // - emptyValue: https://github.com/formio/formio.js/blob/4.13.x/src/components/textfield/TextField.js#L58
        // - defaultValue:
        //    https://github.com/formio/formio.js/blob/4.13.x/src/components/_classes/component/Component.js#L2302
        // By setting the defaultValue to null, then the component will be populated with the emptyValue
        // in the form data.
        schema.defaultValue = null;
      }

      // TODO: This could break if a reusable definition is used multiple times in a form
      const step = getFormStep(formDefinition, draft.formSteps, true);

      if (!isNew) {
        // In the case the component was removed, originalComp is null
        const componentKey = originalComp ? originalComp.key : schema.key;
        // the component was either changed or removed. Using the original key and
        // step configuration, we can build the full json path, after which we can
        // clear validation errors for that.
        const path = getPathToComponent(step.configuration, componentKey);
        // split into component path + field name
        const pathBits = path.split('.');
        pathBits.pop();
        const componentPath = `configuration.${pathBits.join('.')}`;
        step.validationErrors = step.validationErrors.filter(
          ([path]) =>
            !path.startsWith(componentPath) && !['formDefinition', 'configuration'].includes(path)
        );
        const anyStepHasErrors = draft.formSteps.some(step => step.validationErrors.length > 0);
        if (!anyStepHasErrors && draft.tabsWithErrors.includes('form-steps')) {
          draft.tabsWithErrors = draft.tabsWithErrors.filter(tab => tab !== 'form-steps');
        }
      }

      // Check if the formVariables need updating
      draft.formVariables = updateFormVariables(
        formDefinition,
        mutationType,
        isNew,
        schema,
        originalComp,
        draft.formVariables,
        step.configuration
      );
      draft.validationErrors = checkForDuplicateKeys(
        draft.formVariables,
        draft.staticVariables,
        draft.validationErrors
      );

      // apply updates to the backendRegistration Options if needed
      draft.form.registrationBackends = draft.form.registrationBackends.map(configuredBackend => {
        const {backend: registrationBackend, options: registrationBackendOptions} =
          configuredBackend;
        const handler = BACKEND_OPTIONS_FORMS[registrationBackend]?.onStepEdit;
        if (handler == null) return configuredBackend;
        const updatedOptions = handler(registrationBackendOptions, schema, originalComp);
        if (!updatedOptions) return configuredBackend;

        return {...configuredBackend, options: updatedOptions};
      });
      break;
    }
    case 'STEP_FIELD_CHANGED': {
      const {index, name, value} = action.payload;
      const step = draft.formSteps[index];

      // otherwise, set the attribute directly on the stap
      set(step, name, value);
      step.validationErrors = step.validationErrors.filter(([key]) => key !== name);

      // ensure that the (Dutch) name is set as "the" name
      if (name === `translations.${DEFAULT_LANGUAGE}.name`) {
        step.name = value;
      }

      const anyStepHasErrors = draft.formSteps.some(step => step.validationErrors.length > 0);
      if (!anyStepHasErrors && draft.tabsWithErrors.includes('form-steps')) {
        draft.tabsWithErrors = draft.tabsWithErrors.filter(tab => tab !== 'form-steps');
      }
      break;
    }
    case 'MOVE_UP_STEP': {
      const index = action.payload;
      if (index <= 0 || index >= draft.formSteps.length) break;

      let updatedSteps = draft.formSteps.slice(0, index - 1);
      updatedSteps = updatedSteps.concat([{...draft.formSteps[index], ...{index: index - 1}}]);
      updatedSteps = updatedSteps.concat([{...draft.formSteps[index - 1], ...{index: index}}]);

      draft.formSteps = [...updatedSteps, ...draft.formSteps.slice(index + 1)];
      break;
    }

    /**
     * Form Logic rules actions
     */
    case 'ADD_RULE': {
      const {
        form: {url},
      } = draft;

      const newRule = {
        ...EMPTY_RULE,
        form: url,
        _generatedId: getUniqueRandomString(),
      };

      // append to the end if no explicit order is given
      if (!newRule.order) {
        newRule.order = draft.logicRules.length;
      }

      draft.logicRules.push(newRule);
      break;
    }
    case 'CHANGED_RULE': {
      const {index, name, value} = action.payload;
      const oldValue = draft.logicRules[index][name];
      draft.logicRules[index][name] = value;

      switch (name) {
        // check if the type was set & if we need to update the advanced logic flag:
        case '_logicType': {
          const isAdvanced = value === 'advanced';
          draft.logicRules[index].isAdvanced = isAdvanced;
          break;
        }
        // if the order was changed, we need to update all the rules before/after it
        case 'order': {
          const changedRule = draft.logicRules[index];
          if (value > oldValue) {
            // moving down -> move the rules below one level lup
            const affectedRules = draft.logicRules.filter(
              rule => rule.order <= value && rule.order > oldValue && rule != changedRule
            );
            for (const rule of affectedRules) {
              rule.order -= 1;
            }
          } else {
            // moving up
            const affectedRules = draft.logicRules.filter(
              rule => rule.order >= value && rule.order < oldValue && rule != changedRule
            );
            for (const rule of affectedRules) {
              rule.order += 1;
            }
          }
          // finally, sort the rules explicitly by their updated order so that index
          // references still work (sort-of). There's a known TODO to use more stable
          // identities to look up rules in the collection, since re-arranging or even
          // deleting them doesn't play nice with validation errors by index either.
          draft.logicRules = sortBy(draft.logicRules, ['order']);
        }
        case 'description': {
          // if the description field is emptied, we may now generate descriptions from
          // the backend
          if (value === '') {
            draft.logicRules[index]._mayGenerateDescription = true;
          }
          break;
        }
      }

      // Remove the validation error for the updated field
      // If there are multiple actions with errors in one rule, updating it will clear the error also for the
      // other actions of that rule.
      const [validationErrors, tabsWithErrors] = updateWarningsValidationError(
        draft.validationErrors,
        draft.tabsWithErrors,
        'logicRules',
        index,
        name,
        FORM_FIELDS_TO_TAB_NAMES['logicRules']
      );
      draft.validationErrors = validationErrors;
      draft.tabsWithErrors = tabsWithErrors;
      break;
    }
    case 'DELETED_RULE': {
      const {index} = action.payload;
      const {order: ruleOrder} = draft.logicRules[index];

      // delete object from state
      const updatedRules = [...draft.logicRules];
      updatedRules.splice(index, 1);
      draft.logicRules = updatedRules;

      // update the rules following this rule
      draft.logicRules.filter(rule => rule.order > ruleOrder).forEach(rule => (rule.order -= 1));

      // delete the validation errors (if present)
      draft.validationErrors = draft.validationErrors.filter(
        ([key]) => !key.startsWith(`logicRules.${index}`)
      );
      break;
    }
    case 'ADD_SERVICE_FETCH': {
      const {variableName, values} = action.payload;
      const variable = draft.formVariables.find(element => element.key === variableName);
      variable.serviceFetchConfiguration = values;
      break;
    }
    /**
     * Form Variables
     */
    case 'ADD_USER_DEFINED_VARIABLE': {
      draft.formVariables.push(EMPTY_VARIABLE);
      break;
    }
    case 'DELETE_USER_DEFINED_VARIABLE': {
      const key = action.payload;
      const deletedVariable = draft.formVariables.find(variable => variable.key === key);

      // Update registration backends that might depend on the variable:
      draft.form.registrationBackends = draft.form.registrationBackends.map(configuredBackend => {
        const {backend: registrationBackend, options} = configuredBackend;

        const handler = BACKEND_OPTIONS_FORMS[registrationBackend]?.onUserDefinedVariableEdit;
        if (handler == null) return configuredBackend;
        const updatedOptions = handler(options, deletedVariable, null);
        if (!updatedOptions) return configuredBackend;

        return {...configuredBackend, options: updatedOptions};
      });

      // Clear any references in DMN mappings
      updateRemovedKeyInLogic(draft.logicRules, key);

      draft.formVariables = draft.formVariables.filter(variable => variable.key !== key);
      break;
    }
    case 'CHANGE_USER_DEFINED_VARIABLE': {
      const {key, propertyName, propertyValue} = action.payload;

      const originalVariable = cloneDeep(
        draft.formVariables.find(variable => variable.key === key)
      );
      const index = draft.formVariables.findIndex(variable => variable.key === key);

      // empty property = 'root object'
      if (propertyName === '') {
        Object.assign(draft.formVariables[index], propertyValue);
      } else {
        draft.formVariables[index][propertyName] = propertyValue;
      }

      // When dataType changes, a data transformation is needed
      if (propertyName === 'dataType') {
        draft.formVariables[index]['initialValue'] = transformInitialValue(
          propertyValue,
          originalVariable.initialValue
        );
      }

      // Check if there are errors that need to be reset
      if (draft.formVariables[index].errors) {
        const errorKeys = propertyName === '' ? Object.keys(propertyValue) : [propertyName];
        for (const errorKey of errorKeys) {
          delete draft.formVariables[index].errors[errorKey];
        }
      }

      // Check that after the update there are no duplicate keys.
      // If it is the case, update the key that was last updated
      if (propertyName === 'key') {
        const existingKeysAfterUpdate = draft.staticVariables
          .concat(draft.formVariables)
          .map(variable => variable.key);
        const uniqueKeysAfterUpdate = new Set(existingKeysAfterUpdate);

        if (existingKeysAfterUpdate.length !== uniqueKeysAfterUpdate.size) {
          draft.formVariables[index][propertyName] = getUniqueKey(
            propertyValue,
            Array.from(uniqueKeysAfterUpdate)
          );
        }

        // update logic rules with updated keys, only if the original key was not ""
        if (key !== '') {
          updateKeyReferencesInLogic(draft.logicRules, key, propertyValue);
        }
      }

      // Update registration backends that might depend on the variable:
      draft.form.registrationBackends = draft.form.registrationBackends.map(configuredBackend => {
        const {backend: registrationBackend, options} = configuredBackend;

        const handler = BACKEND_OPTIONS_FORMS[registrationBackend]?.onUserDefinedVariableEdit;
        if (handler == null) return configuredBackend;
        const updatedOptions = handler(options, draft.formVariables[index], originalVariable);
        if (!updatedOptions) return configuredBackend;

        return {...configuredBackend, options: updatedOptions};
      });
      break;
    }

    /**
     * Submit & validation error handling
     */
    case 'SUBMIT_STARTED': {
      draft.submitting = true;
      draft.errors = {};
      draft.validationErrors = [];
      draft.tabsWithErrors = [];
      break;
    }
    case 'SUBMIT_DONE': {
      // either the submit completed without errors, or there are validation errors.
      // Either way, there are usually *some* updates to persisted data with updated
      // backend references - which is reflected in the updated state. Therefore, we
      // take that updated state as base and apply any validation error mutations to
      // the updated state. Eventually we return the replacement state.
      const {updatedState, validationErrors} = action.payload;

      // updatedState is the result of earlier produce calls, so it's immutable. We
      // create and update a new state here inside the reducer to eventually replace
      // the component state.
      const newState = produce(updatedState, draft => {
        // process the errors with their field names
        const tabsWithErrors = [];
        const prefixedErrors = [];

        // process the validation errors
        for (const validationError of validationErrors) {
          if (validationError.context.step) {
            const index = validationError.context.step.index;
            draft.formSteps[index].validationErrors = validationError.errors.map(err => [
              err.name,
              err.reason,
            ]);
            continue;
          }

          // generic form-level validation error processing
          let {context: fieldPrefix, errors} = validationError;
          const _prefixedErrors = errors.map(err => {
            const fieldName = err.name.split('.')[0];

            if (fieldName === 'translations') {
              // structure is translations[langCode][fieldName]
              const [, , translationField] = err.name.split('.');
              const tabName = TRANSLATION_FIELD_TO_TAB_NAMES[translationField];
              tabName && tabsWithErrors.push(tabName);
            } else if (!tabsWithErrors.includes(fieldName) && FORM_FIELDS_TO_TAB_NAMES[fieldName]) {
              tabsWithErrors.push(FORM_FIELDS_TO_TAB_NAMES[fieldName]);
            } else if (
              !tabsWithErrors.includes(fieldPrefix) &&
              FORM_FIELDS_TO_TAB_NAMES[fieldPrefix]
            ) {
              tabsWithErrors.push(FORM_FIELDS_TO_TAB_NAMES[fieldPrefix]);
            }

            const key = `${fieldPrefix}.${err.name}`;
            return [key, err.reason];
          });
          prefixedErrors.push(..._prefixedErrors);
        }

        // Assign errors to variables
        const variablesValidationErrors = parseValidationErrors(prefixedErrors, 'variables');
        // variablesValidationErrors is a dict where the keys are the indices of the variables with errors
        Object.keys(variablesValidationErrors).forEach(index => {
          if (draft.formVariables[index]) {
            draft.formVariables[index].errors = variablesValidationErrors[index];
          }
        });

        // update state depending on the validation errors. If there are errors, we set
        // submitting to false so they can correct the validation errors.
        if (validationErrors.length) {
          draft.submitting = false;
        }
        draft.validationErrors.push(...prefixedErrors);
        draft.tabsWithErrors.push(...tabsWithErrors);

        // flag the tabs with errors, if relevant
        const anyStepErrors = draft.formSteps.some(formStep => !!formStep.validationErrors.length);
        if (anyStepErrors && !draft.tabsWithErrors.includes('form-steps')) {
          draft.tabsWithErrors.push('form-steps');
        }
      });
      return newState;
    }
    /**
     * Errors
     */
    // special case - we have a generic session expiry status monitor thing,
    // so don't display the generic error message.
    case 'AUTH_FAILURE': {
      draft.errors = {};
      draft.submitting = false;
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

export const StepsFieldSet = ({submitting = false, loadingErrors, steps = [], ...props}) => {
  if (loadingErrors) {
    return <div className="fetch-error">{loadingErrors}</div>;
  }
  return <FormSteps steps={steps} submitting={submitting} {...props} />;
};

StepsFieldSet.propTypes = {
  loadingErrors: PropTypes.node,
  steps: PropTypes.arrayOf(PropTypes.object),
  submitting: PropTypes.bool,
};

/**
 * Component to render the form edit page.
 */
const FormCreationForm = ({formUuid, formUrl, formHistoryUrl, outgoingRequestsUrl}) => {
  const {csrftoken} = useContext(APIContext);
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

  // load all the plugin registries & other supporting data in parallel
  const backendDataToLoad = [
    {endpoint: LANGUAGE_INFO_ENDPOINT, stateVar: 'languageInfo'},
    {endpoint: PAYMENT_PLUGINS_ENDPOINT, stateVar: 'availablePaymentBackends'},
    {endpoint: REGISTRATION_BACKENDS_ENDPOINT, stateVar: 'availableRegistrationBackends'},
    {endpoint: AUTH_PLUGINS_ENDPOINT, stateVar: 'availableAuthPlugins'},
    {endpoint: CATEGORIES_ENDPOINT, stateVar: 'availableCategories'},
    {endpoint: THEMES_ENDPOINT, stateVar: 'availableThemes'},
    {endpoint: PREFILL_PLUGINS_ENDPOINT, stateVar: 'availablePrefillPlugins'},
    {endpoint: DMN_PLUGINS_ENDPOINT, stateVar: 'availableDMNPlugins'},
    {endpoint: STATIC_VARIABLES_ENDPOINT, stateVar: 'staticVariables'},
    {endpoint: REGISTRATION_VARIABLES_ENDPOINT, stateVar: 'registrationPluginsVariables'},
  ];

  if (formUuid) {
    // We only fetch FDs used in this form if it already exists, otherwise
    // it will fetch all the FDs because the `used_in` query param will have no effect.
    // Reusable FDs are fetched in the background afterwards to avoid long loading time.
    backendDataToLoad.push({
      endpoint: FORM_DEFINITIONS_ENDPOINT,
      query: {used_in: formUuid},
      stateVar: 'formDefinitions',
    });
  }

  const {loading} = useAsync(async () => {
    let mounted = true;
    const promises = [loadFromBackend(backendDataToLoad), loadForm(formUuid)];

    // TODO: API error handling - this should be done using ErrorBoundary instead of
    // state-changes.
    const [backendData, formData] = await Promise.all(promises);
    const supportingData = Object.fromEntries(
      zip(backendDataToLoad, backendData).map(([plugin, data]) => [plugin.stateVar, data])
    );
    mounted &&
      dispatch({
        type: 'BACKEND_DATA_LOADED',
        payload: {supportingData, formData},
      });
    return () => {
      mounted = false;
    };
  }, []);

  useAsync(async () => {
    // Waiting for the last dispatch to be done to avoid state race conditions.
    if (!loading) {
      const responses = await loadFromBackend([
        {endpoint: FORM_DEFINITIONS_ENDPOINT, query: {is_reusable: true}},
      ]);
      const [reusableFormDefinitions] = responses;
      dispatch({
        type: 'REUSABLE_FORM_DEFINITIONS_LOADED',
        payload: reusableFormDefinitions,
      });
    }
  }, [loading]);

  const {ConfirmationModal, confirmationModalProps, openConfirmationModal} = useConfirm();

  /**
   * Functions for handling events
   */
  const onFieldChange = event => {
    const {name, value} = event.target;
    dispatch({
      type: 'FIELD_CHANGED',
      payload: {name, value},
    });
  };

  const addRegistration = key => {
    dispatch({
      type: 'ADD_REGISTRATION',
      payload: {key},
    });
  };

  const onStepDelete = index => {
    dispatch({
      type: 'DELETE_STEP',
      payload: {index: index},
    });
  };

  const onStepReplace = (index, formDefinitionUrl) => {
    dispatch({
      type: 'FORM_DEFINITION_CHOSEN',
      payload: {
        index: index,
        formDefinitionUrl,
      },
    });
  };

  // TODO: we can probably remove a lot of state updates by tapping into onComponentMutated
  // rather than onChange
  const onStepEdit = (index, configuration) => {
    dispatch({
      type: 'EDIT_STEP',
      payload: {
        index: index,
        configuration: configuration,
      },
    });
  };

  // see https://github.com/formio/formio.js/blob/4.12.x/src/WebformBuilder.js#L1172
  const onComponentMutated = (formDefinition, mutationType, schema, ...rest) => {
    dispatch({
      type: 'EDIT_STEP_COMPONENT_MUTATED',
      payload: {
        mutationType,
        schema,
        formDefinition,
        args: rest,
      },
    });
  };

  const onStepFieldChange = (index, event) => {
    const {name, value} = event.target;
    dispatch({
      type: 'STEP_FIELD_CHANGED',
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
        payload: index + 1,
      });
    }
  };

  const onRuleChange = (index, event) => {
    const {name, value} = event.target;
    dispatch({
      type: 'CHANGED_RULE',
      payload: {name, value, index},
    });
  };

  const onServiceFetchAdd = (variableName, values) => {
    dispatch({
      type: 'ADD_SERVICE_FETCH',
      payload: {variableName, values},
    });
  };

  const onSubmit = async event => {
    const {name: submitAction} = event.target;
    const isCreate = state.newForm;
    dispatch({type: 'SUBMIT_STARTED'});

    let newState = {...state, submitting: true};
    let validationErrors;
    try {
      [newState, validationErrors] = await saveCompleteForm(newState, csrftoken);
    } catch (e) {
      // handle HTTP 401 errors, in case the session was expired. This results in a
      // state update AND we abort the rest of the flow.
      if (e instanceof NotAuthenticatedError) {
        dispatch({type: 'AUTH_FAILURE'});
        return;
      }

      // any generic unexpected error. TODO: this really should be gone at some point.
      if (e instanceof APIError) {
        dispatch({type: 'SET_FETCH_ERRORS', payload: e.message});
        window.scrollTo(0, 0); // TODO: get rid of this side-effect -> should be in useEffect instead
        return;
      }

      // anything going wrong here is unexpected, so display a generic error message
      console.error(e);
      dispatch({type: 'SET_FETCH_ERRORS', payload: e.message});
      window.scrollTo(0, 0);
      return;
    }

    dispatch({
      type: 'SUBMIT_DONE',
      payload: {
        updatedState: newState,
        validationErrors,
      },
    });
    // if there are any validation errors -> abort the success message
    if (validationErrors.length) return;

    const {
      form: {url: formUrl},
    } = newState;
    // finalize the "transaction".
    //
    // * schedule a success message
    // * obtain the admin URL to redirect to (detail if editing again, add if creating
    //   another object or list page for simple save)
    const messageData = {isCreate, submitAction: submitAction};
    const messageResponse = await post(`${formUrl}/admin-message`, csrftoken, messageData);
    // this full-page reload ensures that the admin messages are displayed
    window.location = messageResponse.data.redirectUrl;
  };

  const onAuthPluginChange = event => {
    const pluginId = event.target.value;
    dispatch({
      type: 'TOGGLE_AUTH_PLUGIN',
      payload: pluginId,
    });
  };
  const onUserDefinedVariableChange = async (key, propertyName, propertyValue) => {
    const originalVariable = state.formVariables.find(variable => variable.key === key);
    // Just dispatch if anything other than dataType changes
    // or if the initialValue is null/undefined
    if (
      propertyName !== 'dataType' ||
      originalVariable?.initialValue == null ||
      originalVariable?.initialValue === ''
    ) {
      dispatch({
        type: 'CHANGE_USER_DEFINED_VARIABLE',
        payload: {key, propertyName, propertyValue},
      });
      return;
    }

    // Check if the dataType change is intentional.
    if (propertyName === 'dataType' && !(await openConfirmationModal())) {
      return;
    }

    dispatch({
      type: 'CHANGE_USER_DEFINED_VARIABLE',
      payload: {key, propertyName, propertyValue},
    });
  };

  if (loading || state.submitting) {
    return <Loader />;
  }

  const availableComponents = getFormComponents(state.formSteps);
  // dev/debug helper
  const activeTab = new URLSearchParams(window.location.search).get('tab');

  const {isAppointment = false} = state.form.appointmentOptions;
  const {submissionLimit = null} = state.form;

  const numRulesWithProblems = state.logicRules.filter(
    rule => detectLogicProblems(rule, intl).length > 0
  ).length;
  const formLogicWarningMessage = intl.formatMessage(
    {
      description: 'Logic tab warning icon message',
      defaultMessage: 'Detected problems in {count} logic rule(s).',
    },
    {count: numRulesWithProblems}
  );

  return (
    <ValidationErrorsProvider errors={state.validationErrors}>
      <FormObjectTools
        isLoading={loading}
        isActive={state.form.active}
        historyUrl={formHistoryUrl}
        formUrl={formUrl}
      />

      <h1>
        <FormattedMessage defaultMessage="Change form" description="Change form page title" />
      </h1>

      {Object.keys(state.errors).length ? (
        <div className="fetch-error">
          <FormattedMessage
            description="Generic admin error message"
            defaultMessage={`Sorry! Something unexpected went wrong.<br></br>Contact your
              technical administrator to investigate, or perhaps more information is
              available in the <link>outgoing request logs</link>.`}
            values={{
              br: () => <br />,
              link: chunks => (
                <a href={outgoingRequestsUrl} target="_blank">
                  {chunks}
                </a>
              ),
            }}
          />
        </div>
      ) : null}

      <FormContext.Provider
        value={{
          form: {url: state.form.url, uuid: state.form.uuid},
          components: availableComponents,
          formSteps: state.formSteps,
          formDefinitions: state.formDefinitions,
          reusableFormDefinitionsLoaded: state.reusableFormDefinitionsLoaded,
          formVariables: state.formVariables,
          staticVariables: state.staticVariables,
          registrationPluginsVariables: state.registrationPluginsVariables,
          plugins: {
            availableAuthPlugins: state.availableAuthPlugins,
            selectedAuthPlugins: state.selectedAuthPlugins,
            availablePrefillPlugins: state.availablePrefillPlugins,
            availableDMNPlugins: state.availableDMNPlugins,
          },
          languages: state.languageInfo.languages,
          translationEnabled: state.form.translationEnabled,
          registrationBackends: state.form.registrationBackends,
          selectedAuthPlugins: state.selectedAuthPlugins,
        }}
      >
        <FormWarnings form={state.form} />
        <Tabs defaultIndex={activeTab ? parseInt(activeTab, 10) : null}>
          <TabList>
            <Tab hasErrors={state.tabsWithErrors.includes('form')}>
              <FormattedMessage defaultMessage="Form" description="Form fields tab title" />
            </Tab>
            {!isAppointment && (
              <Tab hasErrors={state.tabsWithErrors.includes('form-steps')}>
                <FormattedMessage
                  defaultMessage="Steps and fields"
                  description="Form design tab title"
                />
              </Tab>
            )}
            <Tab hasErrors={state.tabsWithErrors.includes('submission-confirmation')}>
              <FormattedMessage
                defaultMessage="Confirmation"
                description="Form confirmation options tab title"
              />
            </Tab>
            {!isAppointment && (
              <Tab hasErrors={state.tabsWithErrors.includes('registration')}>
                <FormattedMessage
                  defaultMessage="Registration"
                  description="Form registration options tab title"
                />
              </Tab>
            )}
            <Tab hasErrors={state.tabsWithErrors.includes('submission')}>
              <FormattedMessage
                defaultMessage="Submission"
                description="Form submission options tab title"
              />
            </Tab>
            <Tab hasErrors={state.tabsWithErrors.includes('literals')}>
              <FormattedMessage defaultMessage="Literals" description="Form literals tab title" />
            </Tab>
            {!isAppointment && (
              <Tab hasErrors={state.tabsWithErrors.includes('product-payment')}>
                <FormattedMessage
                  defaultMessage="Product & payment"
                  description="Product & payments tab title"
                />
              </Tab>
            )}
            <Tab hasErrors={state.tabsWithErrors.includes('submission-removal-options')}>
              <FormattedMessage
                defaultMessage="Data removal"
                description="Data removal tab title"
              />
            </Tab>
            {!isAppointment && (
              <Tab hasErrors={state.tabsWithErrors.includes('logic-rules')}>
                <FormattedMessage defaultMessage="Logic" description="Form logic tab title" />
                {numRulesWithProblems > 0 ? (
                  <WarningIcon asLead text={formLogicWarningMessage} />
                ) : null}
              </Tab>
            )}
            {!isAppointment && (
              <Tab hasErrors={state.formVariables.some(variable => variableHasErrors(variable))}>
                <FormattedMessage defaultMessage="Variables" description="Variables tab title" />
              </Tab>
            )}
            <Tab hasErrors={state.tabsWithErrors.includes('advanced-configuration')}>
              <FormattedMessage
                defaultMessage="Advanced configuration"
                description="Advanced configuration tab title"
              />
            </Tab>
          </TabList>

          <TabPanel>
            <FormDetailFields form={state.form} onChange={onFieldChange} />
            <FormConfigurationFields
              form={state.form}
              onChange={onFieldChange}
              availableAuthPlugins={state.availableAuthPlugins}
              selectedAuthPlugins={state.selectedAuthPlugins}
              availableCategories={state.availableCategories}
              availableThemes={state.availableThemes}
              onAuthPluginChange={onAuthPluginChange}
            />
          </TabPanel>

          {!isAppointment && (
            <TabPanel>
              <Fieldset
                title={
                  <FormattedMessage
                    defaultMessage="Form design"
                    description="Form design/editor fieldset title"
                  />
                }
              >
                <StepsFieldSet
                  steps={state.formSteps}
                  loadingErrors={state.errors.loadingErrors}
                  onEdit={onStepEdit}
                  onComponentMutated={onComponentMutated}
                  onFieldChange={onStepFieldChange}
                  onDelete={onStepDelete}
                  onReorder={onStepReorder}
                  onReplace={onStepReplace}
                  onAdd={e => {
                    e.preventDefault();
                    dispatch({type: 'ADD_STEP'});
                  }}
                  submitting={state.submitting}
                />
              </Fieldset>
            </TabPanel>
          )}

          <TabPanel>
            <Confirmation
              displayMainWebsiteLink={state.form.displayMainWebsiteLink}
              includeConfirmationPageContentInPdf={state.form.includeConfirmationPageContentInPdf}
              sendConfirmationEmail={state.form.sendConfirmationEmail}
              emailTemplate={state.form.confirmationEmailTemplate}
              onChange={onFieldChange}
              translations={state.form.translations}
            />
          </TabPanel>

          {!isAppointment && (
            <TabPanel>
              <RegistrationFields
                availableBackends={state.availableRegistrationBackends}
                configuredBackends={state.form.registrationBackends}
                onChange={onFieldChange}
                addBackend={addRegistration}
                onDelete={key => dispatch({type: 'DELETE_REGISTRATION', payload: {key: key}})}
              />
            </TabPanel>
          )}

          <TabPanel>
            <SubmissionLimitFields
              submissionLimit={submissionLimit}
              formUuid={state.form.uuid}
              onChange={onFieldChange}
            />
          </TabPanel>

          <TabPanel>
            <TextLiterals onChange={onFieldChange} translations={state.form.translations} />
          </TabPanel>

          {!isAppointment && (
            <TabPanel>
              <ProductFields selectedProduct={state.form.product} onChange={onFieldChange} />
              <PaymentFields
                backends={state.availablePaymentBackends}
                selectedBackend={state.form.paymentBackend}
                backendOptions={state.form.paymentBackendOptions}
                onChange={onFieldChange}
              />
              <PriceLogic variableKey={state.form.priceVariableKey} onFieldChange={onFieldChange} />
            </TabPanel>
          )}

          <TabPanel>
            <DataRemoval
              submissionsRemovalOptions={state.form.submissionsRemovalOptions}
              onChange={onFieldChange}
            />
          </TabPanel>

          {!isAppointment && (
            <TabPanel>
              <FormLogic
                logicRules={state.logicRules}
                onChange={onRuleChange}
                onServiceFetchAdd={onServiceFetchAdd}
                onDelete={index => dispatch({type: 'DELETED_RULE', payload: {index: index}})}
                onAdd={() => dispatch({type: 'ADD_RULE'})}
              />
            </TabPanel>
          )}

          {!isAppointment && (
            <TabPanel>
              <VariablesEditor
                onAdd={() => dispatch({type: 'ADD_USER_DEFINED_VARIABLE'})}
                onDelete={key => dispatch({type: 'DELETE_USER_DEFINED_VARIABLE', payload: key})}
                onChange={onUserDefinedVariableChange}
                onFieldChange={onFieldChange}
              />
            </TabPanel>
          )}

          <TabPanel>
            <FormAdvancedConfiguration
              form={state.form}
              formSteps={state.formSteps}
              onChange={onFieldChange}
            />
          </TabPanel>
        </Tabs>
      </FormContext.Provider>

      <ConfirmationModal
        {...confirmationModalProps}
        message={
          <FormattedMessage
            description="Changing user variable data type and transforming initial value confirmation message"
            defaultMessage="Changing the data type requires the initial value to be changed. This will reset the initial value back to the empty value. Are you sure that you want to do this?"
          />
        }
      />
      <FormSubmit onSubmit={onSubmit} displayActions={!state.newForm} />
    </ValidationErrorsProvider>
  );
};

FormCreationForm.propTypes = {
  formUuid: PropTypes.string.isRequired,
  formUrl: PropTypes.string.isRequired,
  formHistoryUrl: PropTypes.string.isRequired,
  includeConfirmationPageContentInPdf: PropTypes.bool,
};

export {FormCreationForm};
