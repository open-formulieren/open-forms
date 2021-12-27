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
const onStepEdit = (registrationBackendOptions, componentSchema, originalComponent) => {
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


export {onStepEdit};
