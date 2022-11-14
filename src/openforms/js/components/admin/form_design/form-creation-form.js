import zip from 'lodash/zip';
import cloneDeep from 'lodash/cloneDeep';
import getObjectValue from 'lodash/get';
import set from 'lodash/set';
import groupBy from 'lodash/groupBy';
import sortBy from 'lodash/sortBy';
import React, {useContext} from 'react';
import {produce} from 'immer';
import {useImmerReducer} from 'use-immer';
import PropTypes from 'prop-types';
import useAsync from 'react-use/esm/useAsync';
import {Tabs, TabList, TabPanel} from 'react-tabs';
import {FormattedMessage} from 'react-intl';

import Fieldset from 'components/admin/forms/Fieldset';
import ValidationErrorsProvider from 'components/admin/forms/ValidationErrors';
import Loader from 'components/admin/Loader';
import {post} from 'utils/fetch';
import {APIError, NotAuthenticatedError} from 'utils/exception';
import {getUniqueRandomString} from 'utils/random';

import {FormContext} from './Context';
import FormSteps from './FormSteps';
import {
  FORM_DEFINITIONS_ENDPOINT,
  REGISTRATION_BACKENDS_ENDPOINT,
  AUTH_PLUGINS_ENDPOINT,
  PREFILL_PLUGINS_ENDPOINT,
  PAYMENT_PLUGINS_ENDPOINT,
  CATEGORIES_ENDPOINT,
  STATIC_VARIABLES_ENDPOINT,
} from './constants';
import {loadPlugins, loadForm, saveCompleteForm} from './data';
import Appointments, {KEYS as APPOINTMENT_CONFIG_KEYS} from './Appointments';
import FormDetailFields from './FormDetailFields';
import FormConfigurationFields from './FormConfigurationFields';
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
import {BACKEND_OPTIONS_FORMS} from './registrations';
import {
  getFormComponents,
  findComponent,
  checkKeyChange,
  updateKeyReferencesInLogic,
  getUniqueKey,
  getFormStep,
  getPathToComponent,
  parseValidationErrors,
} from './utils';
import {
  checkForDuplicateKeys,
  getFormVariables,
  updateFormVariables,
  variableHasErrors,
} from './variables/utils';
import VariablesEditor from './variables/VariablesEditor';
import {EMPTY_VARIABLE} from './variables/constants';
import Tab from './Tab';
import {updateWarningsValidationError} from './logic/utils';

const initialFormState = {
  form: {
    name: '',
    internalName: '',
    uuid: '',
    url: '',
    slug: '',
    showProgressIndicator: true,
    active: true,
    category: '',
    isDeleted: false,
    maintenanceMode: false,
    translationEnabled: false,
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
    autoLoginAuthenticationBackend: '',
  },
  literals: {
    beginText: {
      value: '',
    },
    previousText: {
      value: '',
    },
    changeText: {
      value: '',
    },
    confirmText: {
      value: '',
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
  availableCategories: [],
  stepsToDelete: [],
  submitting: false,
  logicRules: [],
  priceRules: [],
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
  literals: {
    previousText: {
      value: '',
    },
    saveText: {
      value: '',
    },
    nextText: {
      value: '',
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
  category: 'form',
  isDeleted: 'form',
  maintenanceMode: 'form',
  translationEnabled: 'form',
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
  logicRules: 'logic-rules',
  priceRules: 'product-payment',
  variables: 'variables',
};

function reducer(draft, action) {
  switch (action.type) {
    /**
     * Form-level actions
     */
    case 'FORM_DATA_LOADED': {
      const {form, literals, selectedAuthPlugins, steps, variables, logicRules, priceRules} =
        action.payload;

      if (form) draft.form = form;
      if (literals) draft.literals = literals;
      if (selectedAuthPlugins) draft.selectedAuthPlugins = selectedAuthPlugins;
      if (variables) draft.formVariables = variables;
      if (logicRules)
        draft.logicRules = logicRules.map(rule => ({
          ...rule,
          _logicType: rule.isAdvanced ? 'simple' : 'advanced',
        }));
      if (priceRules) draft.priceRules = priceRules;

      // Add component FormVariables and the step validation errors to the state
      draft.formSteps = steps;
      let stepsFormVariables = [];
      for (const step of draft.formSteps) {
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
    case 'FIELD_CHANGED': {
      const {name, value} = action.payload;
      // names are prefixed like `form.foo` and `literals.bar`
      const nameBits = name.split('.');
      const [prefix, ...rest] = nameBits;
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
      };
      draft.formSteps.push(emptyStep);
      break;
    }
    case 'FORM_DEFINITION_CHOSEN': {
      const {index, formDefinitionUrl} = action.payload;
      if (!formDefinitionUrl) {
        draft.formSteps[index] = {
          ...draft.formSteps[index],
          ...newStepData,
          _generatedId: getUniqueRandomString(),
          // if we're creating a new form definition, mark the step no longer as new since a decision
          // was made (re-use one or create a new one)
          isNew: false,
        };
      } else {
        const {configuration, name, internalName, isReusable, slug} = draft.formDefinitions.find(
          fd => fd.url === formDefinitionUrl
        );
        const {url} = draft.formSteps[index];
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
              value: '',
            },
            saveText: {
              value: '',
            },
            nextText: {
              value: '',
            },
          },
          isNew: false,
          validationErrors: [],
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
      switch (mutationType) {
        case 'changed': {
          originalComp = args[0];
          isNew = args[4];
          break;
        }
        case 'removed': {
          originalComp = null;
          isNew = false;
          break;
        }
        default:
          throw new Error(`Unknown mutation type '${mutationType}'`);
      }

      // Check if a key has been changed and if the logic rules need updating
      const hasKeyChanged = checkKeyChange(mutationType, schema, originalComp);
      if (mutationType === 'changed' && hasKeyChanged) {
        draft.logicRules = updateKeyReferencesInLogic(
          draft.logicRules,
          originalComp.key,
          schema.key
        );
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
          ([path]) => !path.startsWith(componentPath)
        );
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

      // check if we need updates to the backendRegistrationOptions
      const {registrationBackend, registrationBackendOptions} = draft.form;
      const handler = BACKEND_OPTIONS_FORMS[registrationBackend]?.onStepEdit;
      if (handler == null) break;

      const updatedOptions = handler(registrationBackendOptions, schema, originalComp);
      if (updatedOptions) {
        draft.form.registrationBackendOptions = updatedOptions;
      }
      break;
    }
    case 'STEP_FIELD_CHANGED': {
      const {index, name, value} = action.payload;
      const step = draft.formSteps[index];
      step[name] = value;
      step.validationErrors = step.validationErrors.filter(([key]) => key !== name);

      const anyStepHasErrors = draft.formSteps.some(step => step.validationErrors.length > 0);
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

      let updatedSteps = draft.formSteps.slice(0, index - 1);
      updatedSteps = updatedSteps.concat([{...draft.formSteps[index], ...{index: index - 1}}]);
      updatedSteps = updatedSteps.concat([{...draft.formSteps[index - 1], ...{index: index}}]);

      draft.formSteps = [...updatedSteps, ...draft.formSteps.slice(index + 1)];
      break;
    }
    case 'APPOINTMENT_CONFIGURATION_CHANGED': {
      // deconstruct the 'event' which holds the information on which config param
      // was changed and to which component it is (now) set.
      const {
        target: {name, value: selectedComponentKey},
      } = action.payload;

      // name is in the form "appointments.<key>"
      const [prefix, configKey] = name.split('.');

      // utility to find the component for a given appointment config option
      const findComponentForConfigKey = configKey => {
        const name = `${prefix}.${configKey}`;
        return findComponent(draft.formSteps, component => getObjectValue(component, name, false));
      };

      // first, ensure that if the value was changed, the old component is cleared
      const currentComponentForConfigKey = findComponentForConfigKey(configKey);
      if (currentComponentForConfigKey) {
        // wipe the entire appointments configuration
        set(currentComponentForConfigKey, prefix, {});
      }

      // next, handle setting the config to the new component
      const selectedComponent = findComponent(
        draft.formSteps,
        component => component.key === selectedComponentKey
      );
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
            break;
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
            if (locationComponent)
              set(relevantComponent, `${prefix}.locationComponent`, locationComponent.key);
          }
          case 'showLocations': {
            // add the product selection component information
            const productComponent = findComponentForConfigKey('showProducts');
            if (productComponent)
              set(relevantComponent, `${prefix}.productComponent`, productComponent.key);
            break;
          }
          default: {
            throw new Error(`Unknown config key: ${configKey}`);
          }
        }
      }
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
    /**
     * Form Variables
     */
    case 'ADD_USER_DEFINED_VARIABLE': {
      draft.formVariables.push(EMPTY_VARIABLE);
      break;
    }
    case 'DELETE_USER_DEFINED_VARIABLE': {
      const key = action.payload;
      draft.formVariables = draft.formVariables.filter(variable => variable.key !== key);
      break;
    }
    case 'CHANGE_USER_DEFINED_VARIABLE': {
      const {key, propertyName, propertyValue} = action.payload;

      const index = draft.formVariables.findIndex(variable => variable.key === key);

      draft.formVariables[index][propertyName] = propertyValue;

      // Check if there are errors that need to be reset
      if (draft.formVariables[index].errors) {
        delete draft.formVariables[index].errors[propertyName];
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

        // upate logic rules with updated keys
        draft.logicRules = updateKeyReferencesInLogic(draft.logicRules, key, propertyValue);
      }
      break;
    }

    /**
     * Price rules actions
     */
    case 'ADD_PRICE_RULE': {
      const {
        form: {url},
      } = draft;
      draft.priceRules.push({
        ...EMPTY_PRICE_RULE,
        form: url,
        _generatedId: getUniqueRandomString(),
      });
      break;
    }
    case 'CHANGED_PRICE_RULE': {
      const {index, name, value} = action.payload;
      draft.priceRules[index][name] = value;

      const [validationErrors, tabsWithErrors] = updateWarningsValidationError(
        draft.validationErrors,
        draft.tabsWithErrors,
        'priceRules',
        index,
        name,
        FORM_FIELDS_TO_TAB_NAMES['priceRules']
      );
      draft.validationErrors = validationErrors;
      draft.tabsWithErrors = tabsWithErrors;
      break;
    }
    case 'DELETED_PRICE_RULE': {
      const {index} = action.payload;

      // delete object from state
      const updatedRules = [...draft.priceRules];
      updatedRules.splice(index, 1);
      draft.priceRules = updatedRules;
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
            if (!tabsWithErrors.includes(fieldName) && FORM_FIELDS_TO_TAB_NAMES[fieldName]) {
              tabsWithErrors.push(FORM_FIELDS_TO_TAB_NAMES[fieldName]);
            } else if (
              !tabsWithErrors.includes(fieldPrefix) &&
              FORM_FIELDS_TO_TAB_NAMES[fieldPrefix]
            ) {
              tabsWithErrors.push(FORM_FIELDS_TO_TAB_NAMES[fieldPrefix]);
            }

            let key;
            switch (fieldPrefix) {
              // literals are tracked separately in the state
              case 'literals': {
                key = err.name;
                break;
              }
              default: {
                key = `${fieldPrefix}.${err.name}`;
              }
            }

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

const StepsFieldSet = ({submitting = false, loadingErrors, steps = [], ...props}) => {
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
const FormCreationForm = ({csrftoken, formUuid, formUrl, formHistoryUrl}) => {
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
  // TODO: 'plugin' is no longer the best name, it's more loading the data that's dynamic
  // but not dependent on the form itself.
  const pluginsToLoad = [
    {endpoint: PAYMENT_PLUGINS_ENDPOINT, stateVar: 'availablePaymentBackends'},
    {endpoint: FORM_DEFINITIONS_ENDPOINT, stateVar: 'formDefinitions'},
    {endpoint: REGISTRATION_BACKENDS_ENDPOINT, stateVar: 'availableRegistrationBackends'},
    {endpoint: AUTH_PLUGINS_ENDPOINT, stateVar: 'availableAuthPlugins'},
    {endpoint: CATEGORIES_ENDPOINT, stateVar: 'availableCategories'},
    {endpoint: PREFILL_PLUGINS_ENDPOINT, stateVar: 'availablePrefillPlugins'},
    {endpoint: STATIC_VARIABLES_ENDPOINT, stateVar: 'staticVariables'},
  ];

  const {loading} = useAsync(async () => {
    const promises = [
      // TODO: this is a bad function name, refactor
      loadPlugins(pluginsToLoad),
      loadForm(formUuid),
    ];

    // TODO: API error handling - this should be done using ErrorBoundary instead of
    // state-changes.
    const [pluginsData, formData] = await Promise.all(promises);
    dispatch({
      type: 'FORM_DATA_LOADED',
      payload: formData,
    });

    // load various module plugins & update the state
    for (const group of zip(pluginsToLoad, pluginsData)) {
      const [plugin, data] = group;
      dispatch({
        type: 'PLUGINS_LOADED',
        payload: {
          stateVar: plugin.stateVar,
          data: data,
        },
      });
    }
  }, []);

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

  const onStepLiteralFieldChange = (index, event) => {
    const {name, value} = event.target;
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

  const onPriceRuleChange = (index, event) => {
    const {name, value} = event.target;
    dispatch({
      type: 'CHANGED_PRICE_RULE',
      payload: {name, value, index},
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

  if (loading || state.submitting) {
    return <Loader />;
  }

  const availableComponents = getFormComponents(state.formSteps);
  // dev/debug helper
  const activeTab = new URLSearchParams(window.location.search).get('tab');

  return (
    <ValidationErrorsProvider errors={state.validationErrors}>
      <FormObjectTools isLoading={loading} historyUrl={formHistoryUrl} formUrl={formUrl} />

      <h1>
        <FormattedMessage defaultMessage="Change form" description="Change form page title" />
      </h1>

      {Object.keys(state.errors).length ? (
        <div className="fetch-error">
          <FormattedMessage
            defaultMessage="The form is invalid. Please correct the errors below."
            description="Generic error message"
          />
        </div>
      ) : null}

      <FormContext.Provider
        value={{
          form: {url: state.form.url},
          components: availableComponents,
          formSteps: state.formSteps,
          formDefinitions: state.formDefinitions,
          formVariables: state.formVariables,
          staticVariables: state.staticVariables,
          plugins: {
            availableAuthPlugins: state.availableAuthPlugins,
            selectedAuthPlugins: state.selectedAuthPlugins,
            availablePrefillPlugins: state.availablePrefillPlugins,
          },
        }}
      >
        <Tabs defaultIndex={activeTab ? parseInt(activeTab, 10) : null}>
          <TabList>
            <Tab hasErrors={state.tabsWithErrors.includes('form')}>
              <FormattedMessage defaultMessage="Form" description="Form fields tab title" />
            </Tab>
            <Tab hasErrors={state.tabsWithErrors.includes('form-steps')}>
              <FormattedMessage
                defaultMessage="Steps and fields"
                description="Form design tab title"
              />
            </Tab>
            <Tab hasErrors={state.tabsWithErrors.includes('submission-confirmation')}>
              <FormattedMessage
                defaultMessage="Confirmation"
                description="Form confirmation options tab title"
              />
            </Tab>
            <Tab hasErrors={state.tabsWithErrors.includes('registration')}>
              <FormattedMessage
                defaultMessage="Registration"
                description="Form registration options tab title"
              />
            </Tab>
            <Tab hasErrors={state.tabsWithErrors.includes('literals')}>
              <FormattedMessage defaultMessage="Literals" description="Form literals tab title" />
            </Tab>
            <Tab hasErrors={state.tabsWithErrors.includes('product-payment')}>
              <FormattedMessage
                defaultMessage="Product & payment"
                description="Product & payments tab title"
              />
            </Tab>
            <Tab hasErrors={state.tabsWithErrors.includes('submission-removal-options')}>
              <FormattedMessage
                defaultMessage="Data removal"
                description="Data removal tab title"
              />
            </Tab>
            <Tab hasErrors={state.tabsWithErrors.includes('logic-rules')}>
              <FormattedMessage defaultMessage="Logic" description="Form logic tab title" />
            </Tab>
            <Tab>
              <FormattedMessage
                defaultMessage="Appointments"
                description="Appointments tab title"
              />
            </Tab>
            <Tab hasErrors={state.formVariables.some(variable => variableHasErrors(variable))}>
              <FormattedMessage defaultMessage="Variables" description="Variables tab title" />
            </Tab>
          </TabList>

          <TabPanel>
            <FormDetailFields
              form={state.form}
              literals={state.literals}
              onChange={onFieldChange}
              availableAuthPlugins={state.availableAuthPlugins}
              selectedAuthPlugins={state.selectedAuthPlugins}
              availableCategories={state.availableCategories}
              onAuthPluginChange={onAuthPluginChange}
            />
            <FormConfigurationFields
              form={state.form}
              literals={state.literals}
              onChange={onFieldChange}
              availableAuthPlugins={state.availableAuthPlugins}
              selectedAuthPlugins={state.selectedAuthPlugins}
              availableCategories={state.availableCategories}
              onAuthPluginChange={onAuthPluginChange}
            />
          </TabPanel>

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
                onLiteralFieldChange={onStepLiteralFieldChange}
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

          <TabPanel>
            <Confirmation
              pageTemplate={state.form.submissionConfirmationTemplate}
              displayMainWebsiteLink={state.form.displayMainWebsiteLink}
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
              onChange={onPriceRuleChange}
              onDelete={index => dispatch({type: 'DELETED_PRICE_RULE', payload: {index: index}})}
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
            <FormLogic
              logicRules={state.logicRules}
              onChange={onRuleChange}
              onDelete={index => dispatch({type: 'DELETED_RULE', payload: {index: index}})}
              onAdd={() => dispatch({type: 'ADD_RULE'})}
            />
          </TabPanel>

          <TabPanel>
            <Appointments
              onChange={event => {
                dispatch({
                  type: 'APPOINTMENT_CONFIGURATION_CHANGED',
                  payload: event,
                });
              }}
            />
          </TabPanel>

          <TabPanel>
            <VariablesEditor
              variables={state.formVariables}
              onAdd={() => dispatch({type: 'ADD_USER_DEFINED_VARIABLE'})}
              onDelete={key => dispatch({type: 'DELETE_USER_DEFINED_VARIABLE', payload: key})}
              onChange={(key, propertyName, propertyValue) =>
                dispatch({
                  type: 'CHANGE_USER_DEFINED_VARIABLE',
                  payload: {key, propertyName, propertyValue},
                })
              }
            />
          </TabPanel>
        </Tabs>
      </FormContext.Provider>

      <FormSubmit onSubmit={onSubmit} displayActions={!state.newForm} />
    </ValidationErrorsProvider>
  );
};

FormCreationForm.propTypes = {
  csrftoken: PropTypes.string.isRequired,
  formUuid: PropTypes.string.isRequired,
  formUrl: PropTypes.string.isRequired,
  formHistoryUrl: PropTypes.string.isRequired,
};

export {FormCreationForm};
