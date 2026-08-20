import {produce} from 'immer';

import {DEFAULT_LANGUAGE} from 'components/admin/form_design/LanguageTabs';
import {ValidationErrors} from 'utils/exception';
import {put} from 'utils/fetch';

import {createFormVersion} from './versions';

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
  const {form} = draft;
  if (form.type !== 'appointment') return;

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
 * Mutate the draft state in case the form is a single page(step) form.
 */
const handleSingleStepForm = draft => {
  const {form} = draft;
  if (form.type !== 'single_step') return;

  // single step forms have a different functionality, which is why we clear any lingering
  // configuration if a form is turned into a single step form
  draft.selectedAuthPlugins = [];
  draft.form.loginOptions = [];
  draft.form.authBackends = [];
  draft.form.autoLoginAuthenticationBackend = '';
  draft.form.product = null;
  draft.form.paymentBackend = '';
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
  // grab the existing UUID or generate one (for new forms)
  const uuid = state.form.uuid || window.crypto.randomUUID();
  const endpoint = `/api/v3/forms/${uuid}`;

  const cleanedState = produce(state, draft => {
    draft.form.uuid = uuid;
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
    handleSingleStepForm(draft);
  });

  const formName = cleanedState.form.translations[DEFAULT_LANGUAGE].name;
  const formPutBody = {
    /* top level resource fields */
    ...cleanedState.form,
    // FIXME - name should not be required in backend for form designer
    name: formName,
    /* form steps */
    steps: cleanedState.formSteps.map(formStep => ({
      slug: formStep.slug,
      formDefinition: {
        uuid: formStep.formDefinition.split('/').reverse()[0] || window.crypto.randomUUID(),
        internalName: formStep.internalName ?? '',
        configuration: formStep.configuration,
        loginRequired: formStep.loginRequired ?? false,
        isReusable: formStep.isReusable ?? false,
        translations: formStep.translations,
      },
      isApplicable: formStep?.isApplicable ?? true,
      translations: formStep.translations,
    })),
    /* form variables */
    variables: cleanedState.formVariables
      .filter(variable => variable.source !== 'component')
      .map(variable => {
        let initialValue = variable.initialValue;
        // Cast strings to boolean values, to make sure they are actually saved as booleans
        // in the backend
        if (variable.dataType === 'boolean' && typeof initialValue !== 'boolean') {
          initialValue = variable.initialValue === 'true';
        }

        let serviceFetchConfiguration = variable.serviceFetchConfiguration ?? null;
        if (serviceFetchConfiguration) {
          if (Array.isArray(serviceFetchConfiguration.headers)) {
            serviceFetchConfiguration.headers = Object.fromEntries(
              serviceFetchConfiguration.headers
            );
          }
          if (Array.isArray(serviceFetchConfiguration.queryParams)) {
            serviceFetchConfiguration.queryParams = Object.fromEntries(
              serviceFetchConfiguration.queryParams
            );
          }
          // cacheTimeout is a number, but if empty it needs to be null
          if (serviceFetchConfiguration.cacheTimeout === '') {
            serviceFetchConfiguration.cacheTimeout = null;
          }
        }

        return {
          name: variable.name,
          key: variable.key,
          source: variable.source,
          serviceFetchConfiguration,
          prefillPlugin: variable.prefillPlugin,
          prefillAttribute: variable.prefillAttribute,
          prefillIdentifierRole: variable.prefillIdentifierRole,
          prefillOptions: variable.prefillOptions,
          dataType: variable.dataType,
          dataFormat: variable.dataFormat,
          isSensitiveData: variable.isSensitiveData,
          initialValue,
        };
      }),
    /* logic rules */
    logicRules: cleanedState.logicRules.map(rule => ({
      jsonLogicTrigger: rule.jsonLogicTrigger,
      description: rule.description,
      order: rule.order,
      actions: rule.actions,
      isAdvanced: rule.isAdvanced,
    })),
  };

  // throws on HTTP 400, HTTP 401 or any non-OK status.
  let response;
  try {
    response = await put(endpoint, csrftoken, formPutBody, true);
  } catch (e) {
    // TODO: properly route validation errors since we get everything at once now!
    // TODO: if there are variables.$i.serviceFetchConfiguration errors, assign them to
    // the logicrules context instead of variables
    // wrap validation errors so the component knows where to display the errors
    if (e instanceof ValidationErrors) {
      e.context = 'form';
      throw e;
    }
    // unknown, re-throw
    throw e;
  }

  // TODO: on success:
  // * add (created) form definitions to state.formDefinitions
  // * update state.formSteps (UUID, URL, form definition URL)

  // update with the backend generated data, like UUID and URL. Note that this is a noop
  // for form updates.
  const newState = produce(cleanedState, draft => {
    draft.form.url = response.data.url; // should not be needed anymore
  });
  return newState;
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
  // we must reset validation errors before proceeding, otherwise the same validation
  // error is shown multiple times
  let newState = produce(state, draft => {
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
  // Save this new version of the form in the "form version control"
  await createFormVersion(newState.form.url, csrftoken);
  return [newState, []];
};

export {saveCompleteForm};
