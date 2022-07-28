import _ from 'lodash';
import {Utils as FormioUtils} from 'formiojs';
import {defineMessage} from 'react-intl';

import {COMPONENT_DATATYPES, VARIABLE_SOURCES} from './constants';

const getComponentDatatype = component => {
  if (component.multiple) {
    return [];
  }
  return COMPONENT_DATATYPES[component.type] || 'string';
};

const isLayoutComponent = component => {
  return FormioUtils.isLayoutComponent(component);
};

const isInEditGrid = (component, configuration) => {
  // Get all edit grids in the configuration
  let editGrids = [];
  FormioUtils.eachComponent(configuration.components, configComponent => {
    if (configComponent.type === 'editgrid') editGrids.push(configComponent);
  });

  // Check if our component is in the editgrid
  for (const editGrid of editGrids) {
    const foundComponent = FormioUtils.getComponent(editGrid.components, component.key, true);
    if (foundComponent) return true;
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
    prefillPlugin: component.prefill?.plugin || '',
    prefillAttribute: component.prefill?.attribute || '',
    dataType: getComponentDatatype(component),
    initialValue: getDefaultValue(component),
    _id: component.id,
  };
};

const shouldNotUpdateVariables = (newComponent, oldComponent, mutationType, stepConfiguration) => {
  // Issue #1695: content components are not considered layout components
  if (newComponent.type === 'content') return true;

  // editGrids ARE layout components, but we want to create a variable for them that contains all
  // the data of the children
  const isComponentWithVariable =
    isLayoutComponent(newComponent) &&
    !(newComponent.type === 'editgrid') &&
    !isPasteEvent(mutationType, newComponent, oldComponent);

  // Check that this field is not a child of an editgrid component
  // We need to use the oldComponent, because any update to the component performed in the editor has not been saved
  // to the draft configuration yet
  const isEditGridChild = oldComponent && isInEditGrid(oldComponent, stepConfiguration);

  return isComponentWithVariable || isEditGridChild;
};

const getFormVariables = (formDefinition, configuration) => {
  const newFormVariables = [];

  FormioUtils.eachComponent(configuration.components, component =>
    newFormVariables.push(makeNewVariableFromComponent(component, formDefinition))
  );
  return newFormVariables;
};

const updateFormVariables = (
  formDefinition,
  mutationType,
  isNew,
  newComponent,
  oldComponent,
  currentFormVariables,
  stepConfiguration
) => {
  // Not all components are associated with variables
  if (shouldNotUpdateVariables(newComponent, oldComponent, mutationType, stepConfiguration)) {
    return currentFormVariables;
  }

  let updatedFormVariables = _.cloneDeep(currentFormVariables);

  // This is a 'create' or a 'paste' event
  if (isNew) {
    // This is the case where a Layout component has been pasted, so the variables for the components INSIDE
    // the layout component need to be generated.
    if (isLayoutComponent(newComponent) && newComponent.type !== 'editgrid') {
      FormioUtils.eachComponent([newComponent], component =>
        updatedFormVariables.push(makeNewVariableFromComponent(component, formDefinition))
      );
    } else {
      // When a new component is created, the callback is called multiple times by Formio. So we need to avoid adding
      // the variable more than once.
      const existingIds = updatedFormVariables
        .filter(variable => !!variable._id)
        .map(variable => variable._id);
      if (existingIds.includes(newComponent.id)) return updatedFormVariables;

      updatedFormVariables.push(makeNewVariableFromComponent(newComponent, formDefinition));
    }
  }
  // The 'change' event is emitted for both 'create', 'paste' and 'update' events
  // but 'update' events have isNew = false
  else if (mutationType === 'changed') {
    updatedFormVariables = updatedFormVariables.map(variable => {
      // The id of the component changes on every save
      const idMatch = variable._id === oldComponent.id;
      // Case in which the component key has changed (possibly among other attributes)
      if (newComponent.key !== oldComponent.key) {
        if (variable.key === oldComponent.key && idMatch)
          return makeNewVariableFromComponent(newComponent, formDefinition);
        // This is the case where other attributes (not the key) of the component have changed.
      } else {
        if (variable.key === newComponent.key && idMatch)
          return makeNewVariableFromComponent(newComponent, formDefinition);
      }

      return variable;
    });
  } else if (mutationType === 'removed') {
    // When a component is removed, oldComponent is null
    let keysToRemove = [newComponent.key];

    // Case where a layout component is being removed,
    // so the variables for the nested components have to be removed too
    if (isLayoutComponent(newComponent)) {
      FormioUtils.eachComponent([newComponent], component => {
        keysToRemove.push(component.key);
      });
    }

    updatedFormVariables = updatedFormVariables.filter(variable => {
      const matchKeyToRemove = keysToRemove.includes(variable.key);

      // In the case that there are duplicate keys, we need to figure out which of the variables with duplicate keys
      // should be removed. Since in a step there can't be duplicate keys, check that the formDefinition matches
      return !matchKeyToRemove || variable.formDefinition !== formDefinition;
    });
  }

  return updatedFormVariables;
};

const checkForDuplicateKeys = (formVariables, staticVariables) => {
  let validationErrors = [];
  let existingKeys = staticVariables.map(variable => variable.key);

  const uniqueErrorMessage = defineMessage({
    description: 'Unique key error message',
    defaultMessage: 'The variable key must be unique within a form',
  });

  formVariables.map((variable, index) => {
    if (existingKeys.includes(variable.key)) {
      validationErrors.push([`variables.${index}.key`, uniqueErrorMessage]);

      if (!variable.errors) variable.errors = {};
      variable.errors['key'] = uniqueErrorMessage;
      return;
    }

    existingKeys.push(variable.key);
  });

  return validationErrors;
};

const getDefaultValue = component => {
  if (component.hasOwnProperty('defaultValue') && component.defaultValue !== null)
    return component.defaultValue;

  return null;
};

const variableHasErrors = variable => !!Object.entries(variable.errors || {}).length;

export {
  updateFormVariables,
  getFormVariables,
  getComponentDatatype,
  checkForDuplicateKeys,
  variableHasErrors,
};
