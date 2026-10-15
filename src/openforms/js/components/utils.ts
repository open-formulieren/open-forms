import {isPlaceholder, iterComponents} from '@open-formulieren/formio-builder/formio.js';
import {getRegistryEntry as getBuilderRegistryEntry} from '@open-formulieren/formio-builder/registry/index.js';
import type {AnyComponentSchema, JSONValue} from '@open-formulieren/types';

import jsonScriptToVar from '@/utils/json-script';

/**
 * Definition for the empty value of a component in a particular configuration.
 *
 * It's a tuple `[componentType, multiple, emptyValue]`:
 *
 * - `componentType`: value of the `type` key of a component.
 * - `multiple`: boolean for the `multiple` key, even if the component type does not
 *   support this property at all.
 * - `emptyValue`: the actual value for this combination of component type & multiple.
 */
type ComponentEmptyValueDefinition = [AnyComponentSchema['type'], boolean, JSONValue];

type ComponentEmptyValueMapping = Map<[AnyComponentSchema['type'], boolean], JSONValue>;

const COMPONENT_EMPTY_VALUES: ComponentEmptyValueMapping = jsonScriptToVar<
  ComponentEmptyValueDefinition[]
>('config-COMPONENT_EMPTY_VALUES', {
  default: [],
}).reduce<ComponentEmptyValueMapping>((accumulator, currentValue) => {
  const [componentType, multiple, emptyValue] = currentValue;
  accumulator.set([componentType, multiple], emptyValue);
  return accumulator;
}, new Map());

const getComponentEmptyValue = (component: AnyComponentSchema): JSONValue => {
  const multiple = 'multiple' in component ? !!component.multiple : false;
  const emptyValue = COMPONENT_EMPTY_VALUES.get([component.type, multiple]);
  if (emptyValue !== undefined) return emptyValue;
  return null;
};

// A mapping of lookup key (either component key or data path) to the component definition itself.
type FlattenedComponents = Record<string, AnyComponentSchema>;

// You can either index by `key` or `dataPath`, where the latter is the fully qualified
// path with parent keys (for editgrids).
const flattenComponents = (
  components: AnyComponentSchema[],
  indexBy: 'key' | 'dataPath' = 'key'
): FlattenedComponents =>
  Array.from(iterComponents(components)).reduce<FlattenedComponents>(
    (carry, {component, dataPath}) => {
      // since we only input components without placeholders, this should never happen
      if (isPlaceholder(component)) return carry;
      let lookupKey;
      switch (indexBy) {
        case 'key': {
          lookupKey = component.key;
          break;
        }
        case 'dataPath': {
          lookupKey = dataPath;
          break;
        }
        default: {
          const exhaustiveCheck: never = indexBy;
          throw new Error(`Unknown indexBy mode: ${exhaustiveCheck}`);
        }
      }
      carry[lookupKey] = component;
      return carry;
    },
    {}
  );

const hasChildren = (component: AnyComponentSchema): boolean => {
  const entry = getBuilderRegistryEntry(component['type']);
  // Return true if the component has children
  return entry?.getComponentSlots !== undefined;
};

const isLayoutComponent = (component: AnyComponentSchema): boolean => {
  const entry = getBuilderRegistryEntry(component['type']);
  // if the component is not marked as "holding data", it is by definition a layout
  // component that only serves a presentational aspect. Whether the component has
  // children or not, is not relevant.
  return !entry.holdsData;
};

export {getComponentEmptyValue, hasChildren, isLayoutComponent, flattenComponents};
