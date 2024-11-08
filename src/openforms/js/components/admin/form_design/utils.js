/*
global URLify;
 */
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

const transformInitialValue = (newType, originalValue) => {
  switch (newType) {
    case 'array':
      return [];

    case 'boolean':
    case 'int':
    case 'float':
      return undefined;

    case 'object':
      return {};

    case 'string':
    case 'datetime':
    case 'date':
    case 'time':
      return '';

    default:
      return originalValue;
  }
};

const updateKeyReferencesInLogic = (existingLogicRules, originalKey, newKey) => {
  for (const rule of existingLogicRules) {
    if (!JSON.stringify(rule).includes(originalKey)) continue;

    // Replace the key in the JSON trigger
    const stringJsonTrigger = JSON.stringify(rule.jsonLogicTrigger);
    const patternToReplace = new RegExp(`{"var":"${originalKey}(\\.)?([0-9a-zA-Z_\\-]+?)?"}`, 'g');
    rule.jsonLogicTrigger = JSON.parse(
      stringJsonTrigger.replaceAll(patternToReplace, `\{"var":"${newKey}$1$2"\}`)
    );

    // Replace the key in the actions
    for (const action of rule.actions) {
      switch (action.action.type) {
        // component references
        case 'property': {
          if (action.component === originalKey) {
            action.component = newKey;
          }
          break;
        }

        // variable references
        case 'variable':
        case 'fetch-from-service': {
          if (action.variable === originalKey) {
            action.variable = newKey;
          }
          break;
        }

        case 'evaluate-dmn': {
          const {config} = action.action;
          if (!config) break;
          const {inputMapping = [], outputMapping = []} = config;
          for (const mapping of [...inputMapping, outputMapping]) {
            if (mapping.formVariable === originalKey) {
              mapping.formVariable = newKey;
            }
          }
          break;
        }
      }
    }
  }
};

const updateRemovedKeyInLogic = (existingLogicRules, key) => {
  for (const rule of existingLogicRules) {
    for (const action of rule.actions) {
      switch (action.action.type) {
        case 'evaluate-dmn': {
          const {config} = action.action;
          if (!config) break;
          const {inputMapping = [], outputMapping = []} = config;
          for (const mapping of [...inputMapping, outputMapping]) {
            if (mapping.formVariable !== key) continue;
            mapping.formVariable = '';
          }
          break;
        }
      }
    }
  }
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

/**
 * Identify a unique element in formSteps:
 * Case 1. (the form has already been persisted to the database):
 *    - by formDefinition or
 *    - by url or
 *    - by uuid
 * Case 2. (the form has not yet been persisted to the database):
 *    - by _generatedId (a temporary Id generated by the client)
 */
const getFormStep = (identifier, formSteps, matchOnFormDefinition = false) => {
  return formSteps.find(element => {
    // case 1
    let persistedDataMatch;
    if (matchOnFormDefinition) {
      persistedDataMatch = element.formDefinition === identifier;
    } else {
      persistedDataMatch =
        (element.url && element.url === identifier) ||
        (element.uuid && element.uuid === identifier);
    }
    // case 2
    const generatedIdMatch = element._generatedId === identifier;

    return persistedDataMatch || generatedIdMatch;
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

const slugify = (value, maxLength = 100, allowUnicode = false) =>
  URLify(value, maxLength, allowUnicode);

export {
  stripIdFromComponents,
  getFormComponents,
  findComponent,
  checkKeyChange,
  transformInitialValue,
  updateKeyReferencesInLogic,
  updateRemovedKeyInLogic,
  getUniqueKey,
  getFormStep,
  parseValidationErrors,
  getPathToComponent,
  slugify,
};
