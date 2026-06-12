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
  // check if we're dealing with deletion or update
  const isRemove = originalComponent == null;
  const isFileComponentType = componentSchema.type === 'file';

  if (isRemove) {
    const matchingMapping = registrationBackendOptions.propertyMappings?.find(
      mapping => mapping.componentKey === componentSchema.key
    );

    if (matchingMapping) {
      const index = registrationBackendOptions.propertyMappings.indexOf(matchingMapping);
      // remove the mapped property, since the component is removed completely.
      registrationBackendOptions.propertyMappings.splice(index, 1);
    }

    // remove any file component configuration
    if (isFileComponentType && registrationBackendOptions.files) {
      const updatedFiles = registrationBackendOptions.files.filter(
        options => options.key !== componentSchema.key
      );
      registrationBackendOptions.files = updatedFiles;
    }
  } else {
    const keyChange = componentSchema.key !== originalComponent.key;
    if (!keyChange) return null;

    // check if we need to update any mapped properties
    for (const mapping of registrationBackendOptions.propertyMappings ?? []) {
      if (mapping.componentKey === originalComponent.key) {
        mapping.componentKey = componentSchema.key;
      }
    }

    // move/rename the key in the files options mapping
    if (isFileComponentType && registrationBackendOptions.files) {
      const fileOptions = registrationBackendOptions.files.find(
        options => options.key === originalComponent.key
      );
      if (fileOptions !== undefined) {
        fileOptions.key = componentSchema.key;
      }
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
  const isFileComponentType = componentSchema.type === 'file';

  // continue if:
  // * it's version 2, meaning there's always variableMappings to check
  // * it's version 1 and a file component, as files options may need updating
  const shouldContinue =
    registrationBackendOptions.version === 2 ||
    (registrationBackendOptions.version === 1 && isFileComponentType);
  if (!shouldContinue) return;

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

    // remove any file component configuration
    if (isFileComponentType && registrationBackendOptions.files) {
      const updatedFiles = registrationBackendOptions.files.filter(
        options => options.key !== componentSchema.key
      );
      registrationBackendOptions.files = updatedFiles;
    }

    // Objects API mappings
    if (registrationBackendOptions.variablesMapping) {
      const matchingMappingIndex = registrationBackendOptions.variablesMapping.findIndex(
        mapping => mapping.variableKey === componentSchema.key
      );

      if (matchingMappingIndex === -1) return;
      registrationBackendOptions.variablesMapping.splice(matchingMappingIndex, 1);
    }

    return registrationBackendOptions;
  } else {
    const keyChanged = componentSchema.key !== originalComponent.key;
    if (!keyChanged) return null;

    if (registrationBackendOptions.variablesMapping) {
      for (const mapping of registrationBackendOptions.variablesMapping) {
        if (mapping.variableKey === originalComponent.key) {
          mapping.variableKey = componentSchema.key;
        }
      }
    }

    if (isSelectboxesComponentType) {
      registrationBackendOptions.transformToList.forEach((variableKey, index) => {
        if (variableKey === originalComponent.key) {
          registrationBackendOptions.transformToList[index] = componentSchema.key;
        }
      });
    }

    // move/rename the key in the files options mapping
    if (isFileComponentType && registrationBackendOptions.files) {
      const fileOptions = registrationBackendOptions.files.find(
        options => options.key === originalComponent.key
      );
      if (fileOptions !== undefined) {
        fileOptions.key = componentSchema.key;
      }
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

const onStUFZDSStepEdit = (registrationBackendOptions, componentSchema, originalComponent) => {
  // check if we're dealing with deletion or update
  const isRemove = originalComponent == null;
  const isFileComponentType = componentSchema.type === 'file';

  if (isRemove) {
    // remove any file component configuration
    if (isFileComponentType && registrationBackendOptions.files) {
      const updatedFiles = registrationBackendOptions.files.filter(
        options => options.key !== componentSchema.key
      );
      registrationBackendOptions.files = updatedFiles;
    }
  } else {
    const keyChange = componentSchema.key !== originalComponent.key;
    if (!keyChange) return null;

    // move/rename the key in the files options mapping
    if (isFileComponentType && registrationBackendOptions.files) {
      const fileOptions = registrationBackendOptions.files.find(
        options => options.key === originalComponent.key
      );
      if (fileOptions !== undefined) {
        fileOptions.key = componentSchema.key;
      }
    }
  }
  return registrationBackendOptions;
};

export {onZGWStepEdit, onObjectsAPIStepEdit, onGenericJSONStepEdit, onStUFZDSStepEdit};
