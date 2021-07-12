const stripIdFromComponents = (obj) => {
    const {id, ...objWithoutId} = obj;
    if (objWithoutId.components) {
        objWithoutId.components = objWithoutId.components.map(stripIdFromComponents);
    }
    return objWithoutId;
};

const getFormDefinitionChoices = (formDefinitions) => {
    const empty = ['', '-------'];
    const choices = Object.entries(formDefinitions).map(([value, fd]) => [value, fd.name]);
    return [empty].concat(choices);
};

export { stripIdFromComponents, getFormDefinitionChoices };
