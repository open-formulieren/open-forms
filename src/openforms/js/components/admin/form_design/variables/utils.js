import _ from 'lodash';
import {Utils as FormioUtils} from 'formiojs';

import {COMPONENT_DATATYPES, VARIABLE_SOURCES} from './constants';

const getComponentDatatype = component => {
  if (component.multiple) {
    return [];
  }
  return COMPONENT_DATATYPES[component.type] || 'string';
};

const isLayoutOrContentComponent = component => {
  // Issue #1695: content components are not considered layout components
  return FormioUtils.isLayoutComponent(component) || component.type === 'content';
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

const updateFormVariables = (
  formDefinition,
  mutationType,
  newComponent,
  oldComponent,
  currentFormVariables,
  stepConfiguration
) => {
  // Not all components are associated with variables
  // editGrids ARE layout components, but we want to create a variable for them that contains all
  // the data of the children
  if (isLayoutOrContentComponent(newComponent) && !(newComponent.type === 'editgrid'))
    return currentFormVariables;

  // Check that this field is not a child of an editgrid component
  // We need to use the oldComponent, because any update to the component performed in the editor has not been saved
  // to the draft configuration yet
  if (oldComponent && isInEditGrid(oldComponent, stepConfiguration)) {
    return currentFormVariables;
  }

  let updatedFormVariables = _.cloneDeep(currentFormVariables);
  const existingKeys = updatedFormVariables
    .filter(variable => variable.source === VARIABLE_SOURCES.component)
    .map(variable => variable.key);

  // The 'change' event is emitted for both create and update events
  if (mutationType === 'changed') {
    // This is either a create event, or the key of the component has changed
    if (!existingKeys.includes(newComponent.key)) {
      // The URL of the form will be added during the onSubmit callback (so that the formUrl is available)
      updatedFormVariables.push({
        name: newComponent.label,
        key: newComponent.key,
        formDefinition: formDefinition,
        source: VARIABLE_SOURCES.component,
        isSensitiveData: newComponent.isSensitiveData,
        prefillPlugin: newComponent.prefill?.plugin || '',
        prefillAttribute: newComponent.prefill?.attribute || '',
        dataType: getComponentDatatype(newComponent),
        initialValue: getDefaultValue(newComponent),
      });

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
    // When a component is removed, oldComponent is null
    updatedFormVariables = updatedFormVariables.filter(
      variable => variable.key !== newComponent.key
    );
  }

  return updatedFormVariables;
};

const getDefaultValue = component => {
  if (component.hasOwnProperty('defaultValue') && component.defaultValue !== null)
    return component.defaultValue;

  return null;
};

export {updateFormVariables};
