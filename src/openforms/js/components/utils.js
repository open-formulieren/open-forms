import {iterComponents} from '@open-formulieren/formio-builder/formio';
import {getRegistryEntry as getBuilderRegistryEntry} from '@open-formulieren/formio-builder/registry';

import jsonScriptToVar from 'utils/json-script';

const COMPONENT_EMPTY_VALUES = jsonScriptToVar('config-COMPONENT_EMPTY_VALUES', {
  default: [],
}).reduce((accumulator, currentValue) => {
  const [componentType, multiple, emptyValue] = currentValue;
  accumulator.set([componentType, multiple], emptyValue);
  return accumulator;
}, new Map());

const getComponentEmptyValue = component => {
  const multiple = !!component.multiple;
  const emptyValue = COMPONENT_EMPTY_VALUES.get([component.type, multiple]);
  if (emptyValue !== undefined) return emptyValue;
  return null;
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
  // if the component is not marked as "holding data", it is by definition a layout
  // component that only serves a presentational aspect. Whether the component has
  // children or not, is not relevant.
  return !entry.holdsData;
};

export {getComponentEmptyValue, hasChildren, isLayoutComponent, flattenComponents};
