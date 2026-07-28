import {flattenComponents} from 'components/utils';

const useDetectSimpleLogicErrors = configuration => {
  const components = flattenComponents(configuration.components || []);
  const componentsKeys = Object.keys(components);

  let warnings = [];
  for (const component of Object.values(components)) {
    if (!!component?.conditional?.when && !componentsKeys.includes(component.conditional.when)) {
      warnings.push({
        component: component,
        missingKey: component.conditional.when,
      });
    }
  }

  return {warnings};
};

export default useDetectSimpleLogicErrors;
