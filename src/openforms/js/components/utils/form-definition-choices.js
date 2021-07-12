const getFormDefinitionChoices = (formDefinitions) => {
    const empty = ['', '-------'];
    const choices = Object.entries(formDefinitions).map(([value, fd]) => [value, fd.name]);
    return [empty].concat(choices);
};

export {getFormDefinitionChoices};
