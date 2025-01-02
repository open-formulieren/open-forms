import {produce} from 'immer';

import {DEFAULT_LANGUAGE} from 'components/admin/form_design/LanguageTabs';
import {FORM_ENDPOINT} from 'components/admin/form_design/constants';
import {ValidationErrors} from 'utils/exception';
import {apiDelete, post, put} from 'utils/fetch';

import {createOrUpdateLogicRules} from './logic';
import {updateOrCreateFormSteps} from './steps';
import {createOrUpdateFormVariables} from './variables';
import {createFormVersion} from './versions';

const getStepsByGeneratedId = formSteps => {
  const stepsWithGeneratedId = formSteps.filter(step => !!step._generatedId);
  return Object.fromEntries(stepsWithGeneratedId.map(step => [step._generatedId, step]));
};

/**
 * Resolve temporary step IDs to actual URLs.
 *
 * This requires the stepsByGeneratedId being up-to-date with server-side UUID/URLs,
 * so typically you can only call this after all the form steps are committed to the
 * backend.
 *
 * This relies on the client-side _generatedId still being around while the URL has been
 * set. If the passed in stepIdentifier is a URL, it is left untouched. If not, it is
 * assumed to be a generated ID and the step is looked up in the `stepsByGeneratedId`
 * mapping.
 *
 * The return value is the URL reference (if applicable).
 */
const getStepReference = (stepsByGeneratedId, stepIdentifier, stepAttribute = 'url') => {
  // empty-ish value -> leave untouched
  if (!stepIdentifier) return stepIdentifier;
  try {
    new URL(stepIdentifier);
    // if it's a URL, return it - this was already set by the backend.
    return stepIdentifier;
  } catch {
    // Return the temporary id (_generated id) of form_step if it has one
    const step = stepsByGeneratedId[stepIdentifier];
    if (step) {
      return step[stepAttribute];
    } else {
      // form has been persisted to DB; stepIdentifier must be a uuid
      return stepIdentifier;
    }
  }
};

/**
 * Convert empty str value for a data removal field to null.
 */
const normalizeLimit = (draft, field) => {
  const removalOptions = draft.form?.submissionsRemovalOptions;
  if (!removalOptions) return;
  const currentValue = removalOptions?.[field];
  if (currentValue === '') {
    removalOptions[field] = null;
  }
};

/**
 * Convert empty str value of a field to null.
 */
const normalizeEmptyStrField = (draft, field) => {
  const form = draft.form;
  if (form[field] === '') {
    form[field] = null;
  }
};

/**
 * Mutate the draft state in case the form is an appointment form.
 */
const handleAppointmentForm = draft => {
  const {
    form: {
      appointmentOptions: {isAppointment = false},
    },
  } = draft;
  if (!isAppointment) return;

  // appointment forms have very limited functionality, which is why we clear any
  // lingering configuration if a form is turned into an appointment form
  draft.form.registrationBackends = [];
  draft.form.product = null;
  draft.form.paymentBackend = '';

  // clear any steps, variables and logic rules
  draft.stepsToDelete = draft.formSteps.map(step => step.url).filter(Boolean);
  draft.formSteps = [];
  draft.logicRules = [];
  draft.formVariables = [];
};

/**
 * Options for ZGW registration backend can be empty strings but the serializer does not allow them.
 * This is the way the regular forms treat options, they don't send data for the field when empty str.
 */
const handleZgwRegistrationOptions = draft => {
  if (draft.form?.registrationBackends) {
    draft.form.registrationBackends.forEach(backend => {
      if (backend?.backend === 'zgw-create-zaak') {
        for (const key in backend?.options) {
          if (backend.options[key] === '') {
            delete backend.options[key];
          }
        }
      }
    });
  }
};

/**
 * Save the form itself without any related objects.
 */
const saveForm = async (state, csrftoken) => {
  const {
    newForm: isNewForm,
    form: {uuid},
  } = state;
  const cleanedState = produce(state, draft => {
    // ensure we don't overwrite the submission counter with a stale state
    delete draft.form.submissionCounter;
    normalizeLimit(draft, 'successfulSubmissionsRemovalLimit');
    normalizeLimit(draft, 'incompleteSubmissionsRemovalLimit');
    normalizeLimit(draft, 'erroredSubmissionsRemovalLimit');
    normalizeLimit(draft, 'allSubmissionsRemovalLimit');
    normalizeEmptyStrField(draft, 'activateOn');
    normalizeEmptyStrField(draft, 'deactivateOn');
    handleZgwRegistrationOptions(draft);
    handleAppointmentForm(draft);
  });

  const formDetails = produce(cleanedState, draft => {
    return {
      ...draft.form,
      // FIXME - should not be required in backend for form designer
      name: draft.form?.translations?.[DEFAULT_LANGUAGE]?.name,
      authenticationBackends: draft.selectedAuthPlugins,
    };
  });

  const createOrUpdate = isNewForm ? post : put;
  const endpoint = isNewForm ? FORM_ENDPOINT : `${FORM_ENDPOINT}/${uuid}`;

  // throws on HTTP 400, HTTP 401 or any non-OK status.
  let response;
  try {
    response = await createOrUpdate(endpoint, csrftoken, formDetails, true);
  } catch (e) {
    // wrap validation errors so the component knows where to display the errors
    if (e instanceof ValidationErrors) {
      e.context = 'form';
      throw e;
    }
    // unknown, re-throw
    throw e;
  }

  // update with the backend generated data, like UUID and URL. Note that this is a noop
  // for form updates.
  const newState = produce(cleanedState, draft => {
    const {uuid, url} = response.data;
    draft.form.uuid = uuid;
    draft.form.url = url;
    draft.newForm = false; // it's either created now, or updated -> both are not 'new form anymore'
  });
  return newState;
};

/**
 * Save the form steps and their related form definitions + report back any
 * validation errors.
 */
const saveSteps = async (state, csrftoken) => {
  const createdFormDefinitions = [];

  const {
    form: {url: formUrl},
    formSteps,
    stepsToDelete,
  } = state;

  // delete the steps marked for deletion
  // TODO: error handling in case this fails - the situation before refactor
  // was also a bit dire, the internal state was never cleaned up.
  await Promise.all(stepsToDelete.map(async step => await apiDelete(step, csrftoken)));
  let newState = produce(state, draft => {
    draft.stepsToDelete = [];
  });

  const results = await updateOrCreateFormSteps(csrftoken, formUrl, formSteps, formDefinition =>
    createdFormDefinitions.push(formDefinition)
  );

  let validationErrors = [];
  // store the URL references once persisted in the backend
  newState = produce(newState, draft => {
    // add any newly created form definitions to the state
    for (const formDefinition of createdFormDefinitions) {
      draft.formDefinitions.push(formDefinition);
    }
    // process the FormStep results (success or error)
    for (const result of results) {
      // set the step validation errors in the state if it was not a success
      if (result instanceof ValidationErrors) {
        validationErrors.push(result);
        continue;
      }
      const {index, uuid, url, formDefinition} = result;
      draft.formSteps[index].uuid = uuid;
      draft.formSteps[index].url = url;
      draft.formSteps[index].formDefinition = formDefinition;
    }
  });

  return [newState, validationErrors];
};

/**
 * Save the logic rules, report back any validation errors.
 */
const saveLogic = async (state, csrftoken) => {
  const {
    form: {url: formUrl},
  } = state;

  const stepsByGeneratedId = getStepsByGeneratedId(state.formSteps);

  let newState = produce(state, draft => {
    for (const rule of draft.logicRules) {
      rule.form = formUrl;
      // fix the trigger from step reference
      rule.triggerFromStep = getStepReference(stepsByGeneratedId, rule.triggerFromStep);
      // fix the actions that do something with the step(s)
      for (const action of rule.actions) {
        action.formStep = getStepReference(stepsByGeneratedId, action.formStep);
      }
    }
  });

  // make the actual API call
  let errors = [];
  let responseLogicRules;
  try {
    responseLogicRules = await createOrUpdateLogicRules(formUrl, newState.logicRules, csrftoken);

    newState = produce(newState, draft => {
      draft.logicRules = responseLogicRules.data;
      for (const rule of draft.logicRules) {
        rule._logicType = rule.isAdvanced ? 'simple' : 'advanced';
      }
    });
  } catch (e) {
    if (e instanceof ValidationErrors) {
      e.context = 'logicRules';
      // TODO: convert in list of errors for further processing?
      errors = [e];
    } else {
      // re-throw any other type of error
      throw e;
    }
  }

  return [newState, errors];
};

/**
 * Save the variables belonging to the form, user defined and derived from
 * the form steps.
 */
const saveVariables = async (state, csrftoken) => {
  const {
    form: {url: formUrl},
  } = state;

  const stepsByGeneratedId = getStepsByGeneratedId(state.formSteps);
  let newState = produce(state, draft => {
    for (const variable of draft.formVariables) {
      variable.form = formUrl;
      variable.formDefinition = getStepReference(
        stepsByGeneratedId,
        variable.formDefinition,
        'formDefinition'
      );

      // Cast strings to boolean values, to make sure they are actually saved as booleans
      // in the backend
      if (variable.dataType === 'boolean' && typeof variable.initialValue != 'boolean')
        variable.initialValue = variable.initialValue === 'true';

      if (variable.serviceFetchConfiguration) {
        if (Array.isArray(variable.serviceFetchConfiguration.headers)) {
          variable.serviceFetchConfiguration.headers = Object.fromEntries(
            variable.serviceFetchConfiguration.headers
          );
        }

        if (Array.isArray(variable.serviceFetchConfiguration.queryParams)) {
          variable.serviceFetchConfiguration.queryParams = Object.fromEntries(
            variable.serviceFetchConfiguration.queryParams
          );
        }

        // cacheTimeout is a number, but if empty it needs to be null
        if (variable.serviceFetchConfiguration.cacheTimeout === '') {
          variable.serviceFetchConfiguration.cacheTimeout = null;
        }
      }
    }
  });

  // make the actual API call
  let errors = [];
  try {
    const response = await createOrUpdateFormVariables(formUrl, newState.formVariables, csrftoken);
    // update the state with server-side objects
    newState = produce(newState, draft => {
      draft.formVariables = response.data;
    });
  } catch (e) {
    if (e instanceof ValidationErrors) {
      if (e.errors.some(error => error.name.includes('serviceFetchConfiguration'))) {
        // this marks the logicRules tab if *any* of the errors was fetch config related
        // XXX: Should this construct a new error?
        e.context = 'logicRules';
      } else {
        e.context = 'variables';
      }
      // TODO: convert in list of errors for further processing?
      errors = [e];
    } else {
      // re-throw any other type of error
      throw e;
    }
  }

  return [newState, errors];
};

const saveVersion = async (state, csrftoken) => {
  await createFormVersion(state.form.url, csrftoken);
};

/**
 * Save the complete form, including all the steps, logic,...
 *
 * Note that this function is tightly coupled with the FormCreationForm component state.
 *
 * We use the immer produce function to 'commit' state changes that happen during saving
 * into the next immutable object so that following steps can use the expected data
 * structures where temporary IDs etc. have been resolved.
 *
 * TODO: refactor out csrftoken argument everywhere.
 *
 * @param  {String} csrftoken CSRF-Token from backend
 * @param  {Object} state     The FormCreationForm state at the moment of submission
 * @return {Object}           Updated state with resolved temporary IDs
 */
const saveCompleteForm = async (state, csrftoken) => {
  // various save actions for parts of the form result in (gradual) state updates. At
  // the end, we will have a new component state that we can just set/dispatch. This
  // allows us to update internal references when their persistent identifiers have been
  // created in the backend.
  //
  // We leverage immer's produce function for this and to ensure we work with immutable
  // data-structures.
  let newState;
  let logicValidationErrors = [];
  let stepsValidationErrors = [];
  let variableValidationErrors = [];

  // we must reset validation errors before proceeding, otherwise the same validation
  // error is shown multiple times
  newState = produce(state, draft => {
    draft.errors = {};
    draft.validationErrors = [];
    draft.tabsWithErrors = [];
  });

  // first, persist the form itself as everything is related to this. If this succeeds
  // without validation errors, then `newState.form.uuid` will be set, guaranteed.
  try {
    newState = await saveForm(state, csrftoken);
  } catch (e) {
    if (e instanceof ValidationErrors) {
      return [newState, [e]];
    }
    throw e;
  }

  // then, ensure the form definitions and steps are persisted
  [newState, stepsValidationErrors] = await saveSteps(newState, csrftoken);
  if (stepsValidationErrors.length) {
    // if there are errors in the steps, we cannot continue with logic/variables etc.
    // before the steps are properly committed to the DB
    return [newState, stepsValidationErrors];
  }

  // Variables should be created before logic rules,
  // since the logic rules validate if the variables in the trigger exist.
  [newState, variableValidationErrors] = await saveVariables(newState, csrftoken);

  // save logic rules
  [newState, logicValidationErrors] = await saveLogic(newState, csrftoken);

  const validationErrors = [...logicValidationErrors, ...variableValidationErrors];
  if (!validationErrors.length) {
    // Save this new version of the form in the "form version control"
    await saveVersion(newState, csrftoken);
  }
  return [newState, validationErrors];
};

export {saveCompleteForm};
