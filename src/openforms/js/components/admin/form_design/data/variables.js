import {put} from '../../../../utils/fetch';

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

export {createOrUpdateFormVariables};
