import FormioUtils from 'formiojs/utils';


const stripIdFromComponents = (obj) => {
    const {id, ...objWithoutId} = obj;
    if (objWithoutId.components) {
        objWithoutId.components = objWithoutId.components.map(stripIdFromComponents);
    }
    return objWithoutId;
};


/**
 * Extract all the available components from all form steps.
 * @param  {Array}  formSteps An array of the formsteps of a form, which contains the FormIO configuration.
 * @return {Object}           Object keyed by the Formio component.key with the component itself as value.
 */
const getFormComponents = (formSteps = []) => {
    const allComponents = formSteps.map(
        step => {
            let compMap = FormioUtils.flattenComponents(step.configuration.components || [], true)
            return Object.fromEntries(Object.entries(compMap).map(([key, component]) => {
                const stepLabel = `${step.internalName || step.name}: ${component.label || component.key}`;
                return [key, {...component, stepLabel}];
            }));
        }).reduce((acc, currentValue) => ({...acc, ...currentValue}), {});
    return allComponents;
};



/**
 * Find a particular Formio component in all the form steps, given a test function.
 * @param  {Array}  formSteps An array of the formsteps of a form, which contains the FormIO configuration.
 * @param  {Func}   test      A test function to check if the component matches the search parameters.
 * @return {Object}           The component object from Formio matching the test, or null if no match was found.
 */
const findComponent = (formSteps = [], test) => {
    for (const step of formSteps) {
        const stepComponents = FormioUtils.flattenComponents(step.configuration.components || [], true);
        const hit = Object.values(stepComponents).find(test);
        if (hit != null) return hit;
    }
    return null;
};


export {stripIdFromComponents, getFormComponents, findComponent};
