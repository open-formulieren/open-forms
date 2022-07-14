import _ from 'lodash';
import {Utils as FormioUtils} from 'formiojs';

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
  };
};

const shouldNotUpdateVariables = (newComponent, oldComponent, mutationType, stepConfiguration) => {
  // Issue #1695: content components are not considered layout components
  if (newComponent.type === 'content') return false;

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
  newComponent,
  oldComponent,
  currentFormVariables,
  stepConfiguration
) => {
  let updatedFormVariables = _.cloneDeep(currentFormVariables);
  const existingKeys = updatedFormVariables
    .filter(variable => variable.source === VARIABLE_SOURCES.component)
    .map(variable => variable.key);

  // The 'change' event is emitted for both create and update events (and 'paste' events)
  if (mutationType === 'changed') {
    // Not all components are associated with variables
    if (shouldNotUpdateVariables(newComponent, oldComponent, mutationType, stepConfiguration)) {
      return currentFormVariables;
    }

    // This is the case where a Layout component has been pasted, so the variables for the components INSIDE
    // the layout component need to be generated.
    if (!existingKeys.includes(newComponent.key) && isLayoutComponent(newComponent)) {
      FormioUtils.eachComponent([newComponent], component =>
        updatedFormVariables.push(makeNewVariableFromComponent(component, formDefinition))
      );
    }
    // This is either a create event, a change of a component key
    else if (!existingKeys.includes(newComponent.key)) {
      // The URL of the form will be added during the onSubmit callback (so that the formUrl is available)
      updatedFormVariables.push(makeNewVariableFromComponent(newComponent, formDefinition));

      // This is the case where the key of a component has been changed
      if (newComponent.key !== oldComponent.key) {
        updatedFormVariables = updatedFormVariables.filter(
          variable => variable.key !== oldComponent.key
        );
      }
    } else {
      // This is the case where other attributes (not the key) of the component have changed.
      updatedFormVariables = updatedFormVariables.map(variable => {
        if (variable.key !== newComponent.key) return variable;

        return {
          ...variable,
          name: newComponent.label,
          prefillPlugin: newComponent.prefill?.plugin || '',
          prefillAttribute: newComponent.prefill?.attribute || '',
          isSensitiveData: newComponent.isSensitiveData,
          initialValue: getDefaultValue(newComponent),
        };
      });
    }
  } else if (mutationType === 'removed') {
    let keysToRemove = [newComponent.key];

    // Case where a layout component is being removed,
    // so the variables for the nested components have to be removed too
    if (isLayoutComponent(newComponent)) {
      FormioUtils.eachComponent([newComponent], component => {
        keysToRemove.push(component.key);
      });
    }

    // When a component is removed, oldComponent is null
    updatedFormVariables = updatedFormVariables.filter(
      variable => !keysToRemove.includes(variable.key)
    );
  }

  return updatedFormVariables;
};

const getDefaultValue = component => {
  if (component.hasOwnProperty('defaultValue') && component.defaultValue !== null)
    return component.defaultValue;

  return null;
};

export {updateFormVariables, getFormVariables};
