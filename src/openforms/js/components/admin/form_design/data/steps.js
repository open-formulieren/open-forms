import cloneDeep from 'lodash/cloneDeep';

import {DEFAULT_LANGUAGE} from 'components/admin/form_design/LanguageTabs';
import {FORM_DEFINITIONS_ENDPOINT} from 'components/admin/form_design/constants';
import {FormException} from 'utils/exception';
import {ValidationErrors, post, put} from 'utils/fetch';

import {removeEmptyTranslations} from '../../../../utils/translation';

const updateOrCreateSingleFormStep = async (
  csrftoken,
  index,
  formUrl,
  step,
  onFormDefinitionCreate
) => {
  // First update/create the form definitions
  const isNewFormDefinition = !step.formDefinition;
  const definitionCreateOrUpdate = isNewFormDefinition ? post : put;
  const definitionEndpoint = step.formDefinition
    ? step.formDefinition
    : `${FORM_DEFINITIONS_ENDPOINT}`;
  var definitionResponse, stepResponse;

  const formDefinitionTranslations = Object.fromEntries(
    Object.entries(step.translations).map(([code, translations]) => [
      code,
      {name: translations.name},
    ])
  );

  const definitionData = {
    // FIXME - name should not be required in backend for form designer
    name: step.translations?.[DEFAULT_LANGUAGE]?.name,
    internalName: step.internalName,
    slug: step.slug,
    // Remove any references to the custom translations key in the configuration
    configuration: step.configuration,
    loginRequired: step.loginRequired,
    isReusable: step.isReusable,
    translations: formDefinitionTranslations,
    // Extract the translations for this FormDefinition from the configuration
    componentTranslations: removeEmptyTranslations(step.componentTranslations),
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
  const formStepTranslations = Object.fromEntries(
    Object.entries(step.translations).map(([code, translations]) => {
      const {name, ...stepTranslations} = translations;
      return [code, stepTranslations];
    })
  );
  const stepCreateOrUpdate = step.url ? put : post;
  const stepEndpoint = step.url ? step.url : `${formUrl}/steps`;
  const stepData = {
    index: index,
    formDefinition: definitionResponse.data.url,
    translations: formStepTranslations,
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
  }

  return stepResponse.data;
};

/**
 * Update (or create) all the form step configurations.
 *
 * Validation errors raised for each individual step are caught and returned to the
 * caller.
 */
const updateOrCreateFormSteps = async (csrftoken, formUrl, formSteps, onFormDefinitionCreate) => {
  const stepPromises = formSteps.map(async (step, index) => {
    try {
      return await updateOrCreateSingleFormStep(
        csrftoken,
        index,
        formUrl,
        step,
        onFormDefinitionCreate
      );
    } catch (e) {
      if (e instanceof ValidationErrors) {
        e.context = {step: step};
        return e;
      }
      throw e;
    }
  });

  const results = await Promise.all(stepPromises);
  return results;
};

export {updateOrCreateFormSteps};
