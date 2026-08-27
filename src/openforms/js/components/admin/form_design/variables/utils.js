import {iterComponents} from '@open-formulieren/formio-builder/formio';
import _ from 'lodash';
import {defineMessage} from 'react-intl';

import {
  flattenComponents,
  getComponentEmptyValue,
  hasChildren,
  isLayoutComponent,
} from 'components/utils';

import {
  COMPONENT_DATATYPES,
  VARIABLE_SOURCES,
  VARIABLE_SOURCES_GROUP_LABELS,
  VARIABLE_SOURCES_GROUP_ORDER,
} from './constants';

const getComponentDatatype = component => {
  if (component.multiple) {
    return 'array';
  }
  return COMPONENT_DATATYPES[component.type] || 'string';
};

const isInEditGrid = (targetComponent, configuration) => {
  for (const {component} of iterComponents(configuration?.components || [])) {
    if (component.type !== 'editgrid') continue;

    // Check if any of the components in the editgrid has the same key as the component
    // we're looking for.
    const flatChildren = flattenComponents(component.components);
    if (flatChildren[targetComponent.key] !== undefined) return true;
  }

  return false;
};

const isPasteEvent = (mutationType, newComponent, oldComponent) => {
  if (mutationType !== 'changed') return false;
  return _.isEqual(newComponent, oldComponent);
};

const makeNewVariableFromComponent = (component, formDefinition) => {
  // The URL of the form will be added during the onSubmit callback (so that the formUrl is available)
  return {
    name: component.label,
    key: component.key,
    formDefinition: formDefinition,
    source: VARIABLE_SOURCES.component,
    isSensitiveData: component.isSensitiveData,
    serviceFetchConfiguration: null,
    prefillPlugin: component.prefill?.plugin || '',
    prefillAttribute: component.prefill?.attribute || '',
    prefillIdentifierRole: component.prefill?.identifierRole || 'main',
    dataType: getComponentDatatype(component),
    initialValue: getDefaultValue(component),
    _id: component.id,
  };
};

const shouldNotUpdateVariables = (newComponent, oldComponent, mutationType, stepConfiguration) => {
  // Issue #1695: content components are not considered layout components
  if (newComponent.type === 'content') return true;
  // Issue #4884 - soft required errors are pretty much the same as content components,
  // with additional special client-side behaviour
  if (newComponent.type === 'softRequiredErrors') return true;

  const isLayout = hasChildren(newComponent);

  // When deleting a layout component, all child components need to be removed
  if (isLayout && mutationType === 'removed') return false;

  // editGrids ARE layout components, but we want to create a variable for them that contains all
  // the data of the children
  const isComponentWithVariable =
    isLayout &&
    !(newComponent.type === 'editgrid') &&
    !isPasteEvent(mutationType, newComponent, oldComponent);

  // Check that this field is not a child of an editgrid component
  // We need to use the oldComponent, because any update to the component performed in the editor has not been saved
  // to the draft configuration yet
  const isEditGridChild = oldComponent && isInEditGrid(oldComponent, stepConfiguration);

  return isComponentWithVariable || isEditGridChild;
};

/**
 * Transform the Formio configuration into FormVariable instances.
 * @param  {String} formDefinition API resource of the form definition that the configuration belongs to.
 * @param  {OBject} configuration  The Formio form configuration.
 */
const getFormVariables = (formDefinition, configuration) => {
  const newFormVariables = [];

  for (const {component} of iterComponents(configuration?.components || [])) {
    // Layout components don't hold data, so there is no variable to create for them (as
    // the variable can never have a value).
    if (isLayoutComponent(component)) continue;

    // See #5035 - the client side upload components variables are created on load, and
    // then they get pushed to the server on save and are persisted too, which causes
    // upload issues. This may even have been the root cause of this issue where
    // "phantom" variables show up in the step data.
    if (isInEditGrid(component, configuration)) continue;

    newFormVariables.push(makeNewVariableFromComponent(component, formDefinition));
  }

  return newFormVariables;
};

const updateFormVariables = (
  formDefinition,
  mutationType,
  {component: changedComponent, originalComponent = null},
  formVariables,
  stepConfiguration
) => {
  // Not all components are associated with variables
  if (
    shouldNotUpdateVariables(changedComponent, originalComponent, mutationType, stepConfiguration)
  ) {
    return formVariables;
  }

  // This is a 'create' or a 'paste' event
  if (mutationType === 'created') {
    // This is the case where a Layout component has been pasted, so the variables for the components INSIDE
    // the layout component need to be generated.
    if (isLayoutComponent(changedComponent)) {
      for (const {component} of iterComponents([changedComponent])) {
        // Layout comopnents don't need variables - they don't hold data/values
        if (isLayoutComponent(component)) continue;
        formVariables.push(makeNewVariableFromComponent(component, formDefinition));
      }
    } else {
      formVariables.push(makeNewVariableFromComponent(changedComponent, formDefinition));
    }
  } else if (mutationType === 'updated') {
    let indicesVariablesWithoutIds = [];
    let variableUpdated = false;

    for (let variableIndex = 0; variableIndex < formVariables.length; variableIndex++) {
      const variable = formVariables[variableIndex];
      if (!variable._id) {
        indicesVariablesWithoutIds.push(variableIndex);
        continue;
      }

      if (variable._id === originalComponent.id) {
        formVariables[variableIndex] = makeNewVariableFromComponent(
          changedComponent,
          formDefinition
        );
        variableUpdated = true;
        break;
      }
    }

    if (!variableUpdated) {
      // Variables that don't have an _id have been loaded from the backend (which means they can't have duplicate keys)
      for (const index of indicesVariablesWithoutIds) {
        const variable = formVariables[index];
        // Case 1: the component key has changed (possibly among other attributes)
        // Case 2: other attributes (not the key) of the component have changed.
        if (variable.key === originalComponent.key) {
          formVariables[index] = makeNewVariableFromComponent(changedComponent, formDefinition);
          break;
        }
      }
    }
  } else if (mutationType === 'deleted') {
    // When a component is removed, originalComponent is null
    let keysToRemove = [changedComponent.key];

    // Case where a layout component is being removed,
    // so the variables for the nested components have to be removed too
    if (hasChildren(changedComponent)) {
      for (const {component} of iterComponents([changedComponent])) {
        keysToRemove.push(component.key);
      }
    }

    formVariables = formVariables.filter(variable => {
      const matchKeyToRemove = keysToRemove.includes(variable.key);

      // In the case that there are duplicate keys, we need to figure out which of the variables with duplicate keys
      // should be removed. Since in a step there can't be duplicate keys, check that the formDefinition matches
      return !matchKeyToRemove || variable.formDefinition !== formDefinition;
    });
  }

  return formVariables;
};

const checkForDuplicateKeys = (formVariables, staticVariables, validationErrors) => {
  let updatedValidationErrors = _.cloneDeep(validationErrors);
  let existingKeys = staticVariables.map(variable => variable.key);

  const uniqueErrorMessage = defineMessage({
    description: 'Unique key error message',
    defaultMessage: 'The variable key must be unique within a form',
  });

  formVariables.map((variable, index) => {
    const errorKey = `variables.${index}.key`;
    if (existingKeys.includes(variable.key)) {
      updatedValidationErrors.push([errorKey, uniqueErrorMessage]);

      if (!variable.errors) variable.errors = {};
      variable.errors['key'] = uniqueErrorMessage;
      return;
    } else if (variable.errors && variable.errors['key']?.id === uniqueErrorMessage.id) {
      if (Object.keys(variable.errors).length > 1) {
        delete variable.errors['key'];
      } else {
        delete variable.errors;
      }
      updatedValidationErrors = updatedValidationErrors.filter(error => error[0] !== errorKey);
    }

    existingKeys.push(variable.key);
  });

  return updatedValidationErrors;
};

const getDefaultValue = component => {
  if (component.hasOwnProperty('defaultValue') && component.defaultValue !== null)
    return component.defaultValue;

  return getComponentEmptyValue(component);
};

const getVariableSource = variable =>
  variable.source === '' ? VARIABLE_SOURCES.static : variable.source;

const getVariableSourceLabel = variableSource => {
  switch (variableSource) {
    case VARIABLE_SOURCES.component:
      return VARIABLE_SOURCES_GROUP_LABELS.component;
    case VARIABLE_SOURCES.userDefined:
      return VARIABLE_SOURCES_GROUP_LABELS.userDefined;
    default:
      return VARIABLE_SOURCES_GROUP_LABELS.static;
  }
};

const groupVariablesBySource = variables => {
  const groupedVariables = variables.reduce((variableGroups, variable) => {
    const variableSource = getVariableSource(variable);
    if (!variableGroups.find(group => group.source === variableSource)) {
      variableGroups.push({source: variableSource, variables: []});
    }

    return variableGroups.map(group => {
      if (group.source === variableSource) {
        group.variables.push(variable);
      }
      return group;
    });
  }, []);

  groupedVariables.sort((group1, group2) => {
    const indexKey1 = VARIABLE_SOURCES_GROUP_ORDER.indexOf(group1.source);
    const indexKey2 = VARIABLE_SOURCES_GROUP_ORDER.indexOf(group2.source);
    return indexKey1 - indexKey2;
  });
  return groupedVariables;
};

const variableHasErrors = variable => !!Object.entries(variable.errors || {}).length;

export {
  updateFormVariables,
  getFormVariables,
  getComponentDatatype,
  checkForDuplicateKeys,
  getVariableSource,
  getVariableSourceLabel,
  groupVariablesBySource,
  variableHasErrors,
  makeNewVariableFromComponent,
};
