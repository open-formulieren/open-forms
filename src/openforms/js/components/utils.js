import {iterComponents} from '@open-formulieren/formio-builder/formio';
import {getRegistryEntry as getBuilderRegistryEntry} from '@open-formulieren/formio-builder/registry';
import {Formio} from 'formiojs';

const getComponentEmptyValue = component => {
  const componentInstance = Formio.Components.create(component);
  return componentInstance.emptyValue;
};

const flattenComponents = components =>
  Array.from(iterComponents(components)).reduce((carry, configuration) => {
    carry[configuration.component.key] = configuration.component;
    return carry;
  }, {});

const hasChildren = component => {
  const entry = getBuilderRegistryEntry(component['type']);
  // Return true if the component has children
  return entry?.getComponentSlots !== undefined;
};

const isLayoutComponent = component => {
  const entry = getBuilderRegistryEntry(component['type']);
  // Return true if the component has children and doesn't hold data itself
  return hasChildren(component) && !entry.holdsData;
};

export {getComponentEmptyValue, hasChildren, isLayoutComponent, flattenComponents};
