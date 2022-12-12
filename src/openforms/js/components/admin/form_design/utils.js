import FormioUtils from 'formiojs/utils';

const stripIdFromComponents = obj => {
  const {id, ...objWithoutId} = obj;
  if (objWithoutId.components) {
    objWithoutId.components = objWithoutId.components.map(stripIdFromComponents);
  }
  return objWithoutId;
};

/**
 * Extract all the available components from all form steps.
 * @param  {Array}  formSteps An array of the formsteps of a form, which contains the FormIO configuration.
 * @return {Object}           Object keyed by the Formio component.key with the component itself as value.
 */
const getFormComponents = (formSteps = []) => {
  const allComponents = formSteps
    .map(step => {
      let compMap = FormioUtils.flattenComponents(step.configuration.components || [], true);
      return Object.fromEntries(
        Object.entries(compMap).map(([key, component]) => {
          let stepLabel;
          if (component.label) {
            stepLabel = `${step.internalName || step.name}: ${component.label} (${component.key})`;
          } else {
            stepLabel = `${step.internalName || step.name}: ${component.key}`;
          }
          return [key, {...component, stepLabel}];
        })
      );
    })
    .reduce((acc, currentValue) => ({...acc, ...currentValue}), {});
  return allComponents;
};

/**
 * Find a particular Formio component in all the form steps, given a test function.
 * @param  {Array}  formSteps An array of the formsteps of a form, which contains the FormIO configuration.
 * @param  {Func}   test      A test function to check if the component matches the search parameters.
 * @return {Object}           The component object from Formio matching the test, or null if no match was found.
 */
const findComponent = (formSteps = [], test) => {
  for (const step of formSteps) {
    const stepComponents = FormioUtils.flattenComponents(step.configuration.components || [], true);
    const hit = Object.values(stepComponents).find(test);
    if (hit != null) return hit;
  }
  return null;
};

const checkKeyChange = (mutationType, newComponent, oldComponent) => {
  if (mutationType !== 'changed') return false;

  return newComponent.key !== oldComponent.key;
};

const updateKeyReferencesInLogic = (existingLogicRules, originalKey, newKey) => {
  return existingLogicRules.map((rule, index) => {
    if (!JSON.stringify(rule).includes(originalKey)) {
      return rule;
    }

    let newRule = {...rule};
    // Replace the key in the JSON trigger
    const stringJsonTrigger = JSON.stringify(rule.jsonLogicTrigger);
    const compToReplace = JSON.stringify({var: originalKey});
    newRule.jsonLogicTrigger = JSON.parse(
      stringJsonTrigger.replace(compToReplace, JSON.stringify({var: newKey}))
    );
    // Replace the key in the actions
    newRule.actions = newRule.actions.map((action, index) => {
      // component references
      if (action.component && action.component === originalKey) {
        return {...action, component: newKey};
      }
      // variable references
      if (action.variable && action.variable === originalKey) {
        return {...action, variable: newKey};
      }
      return action;
    });

    return newRule;
  });
};

const getUniqueKey = (key, existingKeys) => {
  if (!existingKeys.includes(key)) return key;

  let uniqueKey = key;

  if (!uniqueKey.match(/(\d+)$/)) {
    uniqueKey = `${key}1`;
  } else {
    uniqueKey = key.replace(/(\d+)$/, function (suffix) {
      return Number(suffix) + 1;
    });
  }

  return getUniqueKey(uniqueKey, existingKeys);
};

const getFormStep = (identifier, formSteps, matchOnFormDefinition = false) => {
  return formSteps.find(element => {
    // The formDefinition also uses the _generatedId instead of the URL if it is new
    const urlMatch = matchOnFormDefinition
      ? element.formDefinition === identifier
      : element.url && element.url === identifier;
    const generatedIdMatch = element._generatedId === identifier;
    return urlMatch || generatedIdMatch;
  });
};

const parseValidationErrors = (errors, prefix) => {
  let parsedErrors = {};
  for (const [errorName, errorReason] of errors) {
    const errorNameBits = errorName.split('.');
    if (errorNameBits[0] === prefix) {
      _.set(parsedErrors, errorNameBits.slice(1), errorReason);
    }
  }
  return parsedErrors;
};

// FormioUtils.eachComponent doesn't give us any useful information, so let's implement
// it similar to the backend.
function* _componentWithPathGenerator(components, prefix = 'components') {
  for (let index = 0; index < components.length; index++) {
    const component = components[index];
    const fullPath = `${prefix}.${index}`;
    yield [fullPath, component];

    // taken from FormioUtils.eachComponent
    const hasColumns = component.columns && Array.isArray(component.columns);
    // const hasRows = component.rows && Array.isArray(component.rows);
    const hasComps = component.components && Array.isArray(component.components);

    if (hasColumns) {
      for (let colIndex = 0; colIndex < component.columns.length; colIndex++) {
        const nestedPrefix = `${fullPath}.columns.${colIndex}.components`;
        const column = component.columns[colIndex];
        yield* _componentWithPathGenerator(column.components, nestedPrefix);
      }
    } else if (hasComps) {
      yield* _componentWithPathGenerator(component.components, `${fullPath}.components`);
    }
  }
}

const getPathToComponent = (configuration, key) => {
  const generator = _componentWithPathGenerator(configuration.components);
  for (const [path, component] of generator) {
    if (component.key !== key) continue;
    return path;
  }
  return '';
};

const mergeComponentTranslations = (currentTranslations, newTranslations) => {
  let merged = {};

  for (const [languageCode, translations] of Object.entries(newTranslations)) {
    // Ignore empty keys
    delete translations[''];
    merged[languageCode] = {...(currentTranslations[languageCode] || {}), ...translations};
  }

  return merged;
};

export {
  stripIdFromComponents,
  getFormComponents,
  findComponent,
  checkKeyChange,
  updateKeyReferencesInLogic,
  getUniqueKey,
  getFormStep,
  parseValidationErrors,
  mergeComponentTranslations,
  getPathToComponent,
};
