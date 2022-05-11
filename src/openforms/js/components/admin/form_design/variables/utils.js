import _ from 'lodash';

const updateFormVariables = (mutationType, newComponent, oldComponent, currentFormVariables) => {
    // TODO Not all components should create variables
    if (newComponent.type === 'content') return currentFormVariables;

    let updatedFormVariables = _.cloneDeep(currentFormVariables);
    const existingKeys = updatedFormVariables.map(variable => variable.key);
    // The 'change' event is emitted for both create and update
    if (mutationType === 'changed') {
        if (!existingKeys.includes(newComponent.key)) {
            updatedFormVariables.push({
                name: newComponent.label,
                slug: newComponent.key,
                source: 'component',
                dataType: 'string',  // Todo Convert between Formio types (newComponent.type) and string/bool/...
                initial_value: newComponent.defaultValue || '',
            });
        }
        if (!existingKeys.includes(oldComponent.key)) {
            // TODO remove component
        }
    } else if (mutationType === 'removed') {
        // TODO
    }

    return updatedFormVariables;
};

export {updateFormVariables};
