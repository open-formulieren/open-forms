import {FormException} from '../../../utils/exception';
import {get, post, put, ValidationErrors} from '../../../utils/fetch';
import {FORM_DEFINITIONS_ENDPOINT, LOGICS_ENDPOINT, PRICE_RULES_ENDPOINT} from './constants';
import {saveRules} from './logic-data';

class PluginLoadingError extends Error {
  constructor(message, plugin, response) {
    super(message);
    this.plugin = plugin;
    this.response = response;
  }
}

// TODO: add error handling in the fetch wrappers to throw exceptions + add error
// boundaries in the component tree.
const loadPlugins = async (plugins = []) => {
  const promises = plugins.map(async plugin => {
    let response = await get(plugin.endpoint);
    if (!response.ok) {
      throw new PluginLoadingError('Failed to load plugins', plugin, response);
    }
    let responseData = response.data;

    // paginated or not?
    const isPaginated =
      responseData.hasOwnProperty('results') && responseData.hasOwnProperty('count');
    if (!isPaginated) {
      return responseData;
    }

    // yep, resolve all pages
    // TODO: check if we have endpoints that return stupid amounts of data and treat those
    // differently/async to reduce the browser memory footprint
    let allResults = [...responseData.results];
    while (responseData.next) {
      response = await get(responseData.next);
      if (!response.ok) {
        throw new PluginLoadingError('Failed to load plugins', plugin, response);
      }
      responseData = response.data;
      allResults = [...allResults, ...responseData.results];
    }
    return allResults;
  });
  const results = await Promise.all(promises);
  return results;
};

const updateOrCreateSingleFormStep = async (
  csrftoken,
  index,
  formUrl,
  step,
  onCreateFormStep,
  onFormDefinitionCreate
) => {
  // First update/create the form definitions
  const isNewFormDefinition = !step.formDefinition;
  const definitionCreateOrUpdate = isNewFormDefinition ? post : put;
  const definitionEndpoint = step.formDefinition
    ? step.formDefinition
    : `${FORM_DEFINITIONS_ENDPOINT}`;
  var definitionResponse, stepResponse;

  const definitionData = {
    name: step.name,
    internalName: step.internalName,
    slug: step.slug,
    configuration: step.configuration,
    loginRequired: step.loginRequired,
    isReusable: step.isReusable,
  };

  try {
    definitionResponse = await definitionCreateOrUpdate(
      definitionEndpoint,
      csrftoken,
      definitionData,
      true
    );
    // handle any unexpected API errors
    if (!definitionResponse.ok) {
      throw new FormException(
        'An error occurred while updating the form definitions',
        definitionResponse.data
      );
    }
  } catch (e) {
    // re-throw both expected validation errors and unexpected errors, calling code
    // deals with it. We must abort here, since the dependent formStep cannot continue
    // if this fails.
    throw e;
  }

  // okay, form definition create-update succeeded, let's proceed...
  const stepCreateOrUpdate = step.url ? put : post;
  const stepEndpoint = step.url ? step.url : `${formUrl}/steps`;
  const stepData = {
    index: index,
    formDefinition: definitionResponse.data.url,
    literals: {
      nextText: {
        value: step.literals.nextText.value,
      },
      saveText: {
        value: step.literals.saveText.value,
      },
      previousText: {
        value: step.literals.previousText.value,
      },
    },
  };

  try {
    stepResponse = await stepCreateOrUpdate(stepEndpoint, csrftoken, stepData, true);
    // handle any unexpected API errors
    if (!stepResponse.ok) {
      throw new FormException(
        'An error occurred while updating the form steps.',
        stepResponse.data
      );
    }
  } catch (e) {
    // re-throw both expected validation errors and unexpected errors, calling code
    // deals with it.
    throw e;
  }

  // Once a FormDefinition and a FormStep have been created, they should no longer be seen as 'new'.
  // This is important if another step/definition cause an error and then a 2nd attempt is made to
  // save all FormDefinition/FormSteps.
  if (isNewFormDefinition) {
    onFormDefinitionCreate(definitionResponse.data);
    onCreateFormStep(index, stepResponse.data.url, stepResponse.data.formDefinition);
  }

  return stepResponse.data;
};

/**
 * Update (or create) all the form step configurations.
 *
 * Validation errors raised for each individual step are caught and returned to the
 * caller.
 */
const updateOrCreateFormSteps = async (
  csrftoken,
  formUrl,
  formSteps,
  onCreateFormStep,
  onFormDefinitionCreate
) => {
  const stepPromises = formSteps.map(async (step, index) => {
    try {
      return await updateOrCreateSingleFormStep(
        csrftoken,
        index,
        formUrl,
        step,
        onCreateFormStep,
        onFormDefinitionCreate
      );
    } catch (e) {
      if (e instanceof ValidationErrors) {
        return {
          step: step,
          error: e,
        };
      }
      throw e; // re-throw unexpected errors
    }
  });

  const results = await Promise.all(stepPromises);

  const updatedSteps = [];
  const errors = [];

  results.map(result => {
    if (result.error) {
      errors.push(result);
    } else {
      updatedSteps.push(result);
    }
  });

  return {updatedSteps, errors};
};

const saveLogicRules = async (formUrl, csrftoken, logicRules, logicRulesToDelete) => {
  const createdRules = await saveRules(
    LOGICS_ENDPOINT,
    formUrl,
    csrftoken,
    logicRules,
    logicRulesToDelete,
    'logicRules'
  );
  return createdRules;
};

const savePriceRules = async (formUrl, csrftoken, priceRules, priceRulesToDelete) => {
  const createdRules = await saveRules(
    PRICE_RULES_ENDPOINT,
    formUrl,
    csrftoken,
    priceRules,
    priceRulesToDelete,
    'priceRules'
  );
  return createdRules;
};

const createOrUpdateFormVariables = async (
  formUrl,
  csrftoken,
  variables,
  stateformSteps,
  updatedFormSteps
) => {
  const endPoint = `${formUrl}/variables`;
  const formVariables = variables.map(variable => {
    // There are 2 cases here:
    // 1. The variable was added to an existing form definition (i.e. which already has a URL). So variable.formDefinition
    //   is the URL of the formDefinition.
    // 2. The variable was added to a new form definition (i.e. which didn't have a URL). So variable.formDefinition
    //   is the _generatedId of the formDefinition.
    let formDefinitionUrl = variable.formDefinition;
    try {
      new URL(variable.formDefinition);
    } catch (e) {
      // Retrieve the URL of the definition from the formSteps which have already been saved
      stateformSteps.map((step, index) => {
        if (step._generatedId === variable.formDefinition) {
          formDefinitionUrl = updatedFormSteps[index].formDefinition;
        }
      });
    }
    return {...variable, form: formUrl, formDefinition: formDefinitionUrl};
  });

  return await put(endPoint, csrftoken, formVariables);
};

export {loadPlugins, PluginLoadingError};
export {updateOrCreateFormSteps, createOrUpdateFormVariables};
export {saveLogicRules, savePriceRules};
