/**
 * Update the mapped process variables after the form definitions change
 * @param  {Object} registrationBackendOptions The currently configured backend options,
 *                                             including the mapped process variables. Note that this is
 *                                             an immer draft which can be mutated.
 * @param  {Object} componentSchema            The Formio component (schema) that was mutated in some way
 * @param  {Object|null} originalComponent     The component before it was mutated, null if the component is removed.
 * @return {Object|null}                       The updated registrationBackendOptions draft. Return null to indicate
 *                                             no changes need to be made.
 */
const onCamundaStepEdit = (registrationBackendOptions, componentSchema, originalComponent) => {
  // check if we're dealing with deletion or update
  const isRemove = originalComponent == null;
  if (isRemove) {
    const matchingVariable = registrationBackendOptions.processVariables.find(
      processVar => processVar.componentKey === componentSchema.key
    );
    if (!matchingVariable) return null;
    const index = registrationBackendOptions.processVariables.indexOf(matchingVariable);
    // remove the mapped variable, since the component is removed completely.
    registrationBackendOptions.processVariables.splice(index, 1);
  } else {
    const keyChange = componentSchema.key !== originalComponent.key;
    if (!keyChange) return null;

    // check if we need to update any mapped variables
    for (const processVariable of registrationBackendOptions.processVariables) {
      if (processVariable.componentKey === originalComponent.key) {
        processVariable.componentKey = componentSchema.key;
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
const onZGWStepEdit = (registrationBackendOptions, componentSchema, originalComponent) => {
  if (!registrationBackendOptions.propertyMappings) return null;
  // check if we're dealing with deletion or update
  const isRemove = originalComponent == null;

  if (isRemove) {
    const matchingMapping = registrationBackendOptions.propertyMappings.find(
      mapping => mapping.componentKey === componentSchema.key
    );
    if (!matchingMapping) return null;
    const index = registrationBackendOptions.propertyMappings.indexOf(matchingMapping);
    // remove the mapped property, since the component is removed completely.
    registrationBackendOptions.propertyMappings.splice(index, 1);
  } else {
    const keyChange = componentSchema.key !== originalComponent.key;
    if (!keyChange) return null;

    // check if we need to update any mapped properties
    for (const mapping of registrationBackendOptions.propertyMappings) {
      if (mapping.componentKey === originalComponent.key) {
        mapping.componentKey = componentSchema.key;
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

  if (registrationBackendOptions.version !== 2 && !isSelectboxesComponentType) return;

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

export {onCamundaStepEdit, onZGWStepEdit, onObjectsAPIStepEdit, onGenericJSONStepEdit};
