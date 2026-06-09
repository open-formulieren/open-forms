/**
 * Update the mapped properties after the form definitions change
 * @param  {Object} registrationBackendOptions The currently configured backend options,
 *                                             including the mapped properties. Note that this is
 *                                             an immer draft which can be mutated.
 * @param  {Object} componentSchema            The Formio component (schema) that was mutated in some way
 * @param  {Object|null} originalComponent     The component before it was mutated, null if the component is removed.
 * @return {Object|null}                       The updated registrationBackendOptions draft. Return null to indicate
 *                                             no changes need to be made.
 */
const onZGWStepEdit = (registrationBackendOptions, componentSchema, originalComponent) => {
  const isFileComponentType = componentSchema.type === 'file';
  if (!registrationBackendOptions.propertyMappings && !isFileComponentType) return null;

  // check if we're dealing with deletion or update
  const isRemove = originalComponent == null;

  if (isRemove) {
    const matchingMapping = registrationBackendOptions.propertyMappings.find(
      mapping => mapping.componentKey === componentSchema.key
    );
    if (matchingMapping) {
      const index = registrationBackendOptions.propertyMappings.indexOf(matchingMapping);
      // remove the mapped property, since the component is removed completely.
      registrationBackendOptions.propertyMappings.splice(index, 1);
    }

    // remove any file component configuration
    if (isFileComponentType) {
      delete registrationBackendOptions.files[componentSchema.key];
    }
  } else {
    const keyChange = componentSchema.key !== originalComponent.key;
    if (!keyChange) return null;

    // check if we need to update any mapped properties
    for (const mapping of registrationBackendOptions.propertyMappings) {
      if (mapping.componentKey === originalComponent.key) {
        mapping.componentKey = componentSchema.key;
      }
    }

    // move/rename the key in the files options mapping
    if (isFileComponentType) {
      registrationBackendOptions.files[componentSchema.key] =
        registrationBackendOptions.files[originalComponent.key];
      delete registrationBackendOptions.files[originalComponent.key];
    }
  }
  return registrationBackendOptions;
};

/**
 * Update the mapped properties after the form definitions change
 * @param  {Object} registrationBackendOptions The currently configured backend options,
 *                                             including the mapped properties. Note that this is
 *                                             an immer draft which can be mutated.
 * @param  {Object} componentSchema            The Formio component (schema) that was mutated in some way
 * @param  {Object|null} originalComponent     The component before it was mutated, null if the component is removed.
 * @return {Object|null}                       The updated registrationBackendOptions draft. Return null to indicate
 *                                             no changes need to be made.
 */
const onObjectsAPIStepEdit = (registrationBackendOptions, componentSchema, originalComponent) => {
  const isSelectboxesComponentType = componentSchema.type === 'selectboxes';

  if (registrationBackendOptions.version !== 2 || !isSelectboxesComponentType) return;

  const removed = originalComponent == null;
  if (removed) {
    // selectboxes component type and the transformToList array
    if (isSelectboxesComponentType) {
      const matchingTransformToListVariableIndex =
        registrationBackendOptions.transformToList.findIndex(
          transformToListVariable => transformToListVariable === componentSchema.key
        );
      if (matchingTransformToListVariableIndex !== -1) {
        registrationBackendOptions.transformToList.splice(matchingTransformToListVariableIndex, 1);
      }
    }

    // Objects API mappings
    const matchingMappingIndex = registrationBackendOptions.variablesMapping.findIndex(
      mapping => mapping.variableKey === componentSchema.key
    );

    if (matchingMappingIndex === -1) return;
    registrationBackendOptions.variablesMapping.splice(matchingMappingIndex, 1);
    return registrationBackendOptions;
  } else {
    const keyChanged = componentSchema.key !== originalComponent.key;
    if (!keyChanged) return null;

    for (const mapping of registrationBackendOptions.variablesMapping) {
      if (mapping.variableKey === originalComponent.key) {
        mapping.variableKey = componentSchema.key;
      }
    }

    if (isSelectboxesComponentType) {
      registrationBackendOptions.transformToList.forEach((variableKey, index) => {
        if (variableKey === originalComponent.key) {
          registrationBackendOptions.transformToList[index] = componentSchema.key;
        }
      });
    }
    return registrationBackendOptions;
  }
};

/**
 * Update the included variable keys after the form definitions change
 * @param  {Object} registrationBackendOptions The currently configured backend options,
 *                                             including the various variable keys. Note that this is
 *                                             an immer draft which can be mutated.
 * @param  {Object} componentSchema            The Formio component (schema) that was mutated in some way
 * @param  {Object|null} originalComponent     The component before it was mutated, null if the component is removed.
 * @return {Object|null}                       The updated registrationBackendOptions draft. Return null to indicate
 *                                             no changes need to be made.
 */
const onGenericJSONStepEdit = (registrationBackendOptions, componentSchema, originalComponent) => {
  const removed = originalComponent == null;
  const optionsArrays = [
    registrationBackendOptions.variables,
    registrationBackendOptions.fixedMetadataVariables,
    registrationBackendOptions.additionalMetadataVariables,
    registrationBackendOptions.transformToList,
  ];

  if (removed) {
    const matchingVariableIndex = registrationBackendOptions.variables.findIndex(
      variable => variable === componentSchema.key
    );
    const matchingFixedMetadataVariableIndex =
      registrationBackendOptions.fixedMetadataVariables.findIndex(
        fixedMetadataVariable => fixedMetadataVariable === componentSchema.key
      );
    const matchingAdditionalMetadataVariableIndex =
      registrationBackendOptions.additionalMetadataVariables.findIndex(
        additionalMetadataVariable => additionalMetadataVariable === componentSchema.key
      );
    const matchingTransformToListVariableIndex =
      registrationBackendOptions.transformToList.findIndex(
        transformToListVariable => transformToListVariable === componentSchema.key
      );

    const matchingPropertiesIndexes = [
      matchingVariableIndex,
      matchingFixedMetadataVariableIndex,
      matchingAdditionalMetadataVariableIndex,
      matchingTransformToListVariableIndex,
    ];

    if (matchingPropertiesIndexes.every(index => index === -1)) return;

    matchingPropertiesIndexes.forEach((index, i) => {
      if (index !== -1) optionsArrays[i].splice(index, 1);
    });

    return registrationBackendOptions;
  } else {
    const keyChanged = componentSchema.key !== originalComponent.key;
    if (!keyChanged) return null;

    for (const optionArray of optionsArrays) {
      optionArray.forEach((variableKey, index) => {
        if (variableKey === originalComponent.key) {
          optionArray[index] = componentSchema.key;
        }
      });
    }
  }

  return registrationBackendOptions;
};

export {onZGWStepEdit, onObjectsAPIStepEdit, onGenericJSONStepEdit};
