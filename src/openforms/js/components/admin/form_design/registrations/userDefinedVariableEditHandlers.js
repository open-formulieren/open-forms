/**
 * Update the mapped properties after the user defined variable change
 * @param  {Object} registrationBackendOptions The currently configured backend options,
 *                                             including the mapped properties. Note that this is
 *                                             an immer draft which can be mutated.
 * @param  {Object} variable                   The user defined variable that was mutated in some way
 * @param  {Object|null} originalVariable      The user defined variable before it was mutated, null if it is removed.
 * @return {Object|null}                       The updated registrationBackendOptions draft. Return null to indicate
 *                                             no changes need to be made.
 */
const onObjectsAPIUserDefinedVariableEdit = (
  registrationBackendOptions,
  variable,
  originalVariable
) => {
  if (registrationBackendOptions.version !== 2) return;
  // If the data type has changed, the mapped target might not be compatible anymore:
  const shouldRemove = originalVariable == null || variable.dataType !== originalVariable.dataType;

  if (shouldRemove) {
    const matchingMappingIndex = registrationBackendOptions.variablesMapping.findIndex(
      mapping => mapping.variableKey === variable.key
    );

    if (matchingMappingIndex === -1) return;
    registrationBackendOptions.variablesMapping.splice(matchingMappingIndex, 1);
    return registrationBackendOptions;
  } else {
    const keyChanged = variable.key !== originalVariable.key;
    if (!keyChanged) return;

    for (const mapping of registrationBackendOptions.variablesMapping) {
      if (mapping.variableKey === originalVariable.key) {
        mapping.variableKey = variable.key;
      }
    }
    return registrationBackendOptions;
  }
};

export {onObjectsAPIUserDefinedVariableEdit};
