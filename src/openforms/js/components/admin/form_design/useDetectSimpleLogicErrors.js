import FormioUtils from 'formiojs/utils';


const useDetectSimpleLogicErrors = (configuration) => {
    const components = FormioUtils.flattenComponents(configuration.components || [], true);
    const componentsKeys = Object.keys(components);

    let warnings = [];
    for (const [componentKey, component] of Object.entries(components)) {
        if (!!component?.conditional?.when && !componentsKeys.includes(component.conditional.when)) {
            warnings.push({
                component: component,
                missingKey: component.conditional.when
            });
        }
    }

    return {warnings};
};

export default useDetectSimpleLogicErrors;
