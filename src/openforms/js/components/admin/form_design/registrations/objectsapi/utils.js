import {REGISTRATION_OBJECTS_TARGET_PATHS} from 'components/admin/form_design/constants';
import {post} from 'utils/fetch';

const VARIABLE_TYPE_MAP = {
  boolean: 'boolean',
  int: 'integer',
  float: 'number',
  object: 'object',
  array: 'array',
  string: 'string',
};

const FORMAT_TYPE_MAP = {
  datetime: 'date-time',
  time: 'time',
  date: 'date',
};

/**
 * Return a JSON Schema definition matching the provided variable.
 * @param {Object} variable - The current variable
 * @param {Object} components - The components available in the form. The key is the component key, the value is the
 * component definition.
 * @returns {Object} - The JSON Schema
 */
const asJsonSchema = (variable, components, transformToList = []) => {
  // Special handling for component types.
  if (variable.source === 'component') {
    const componentDefinition = components[variable.key];

    switch (componentDefinition.type) {
      case 'file': {
        const {multiple = false} = componentDefinition;
        const uriSchema = {type: 'string', format: 'uri'};
        // If the component allows multiple files, the type is array, otherwise it's
        // just a single string.
        return multiple ? {type: 'array', items: uriSchema} : uriSchema;
      }
      case 'map': {
        // TODO: in the future we could use `const: 'Point'` for the `type` key to be
        // more strict.
        return {
          type: 'object',
          properties: {
            type: {
              type: 'string',
            },
          },
        };
      }
      case 'selectboxes': {
        return transformToList?.includes(variable.key)
          ? {
              type: 'array',
            }
          : {
              type: 'object',
            };
      }
    }
  }

  // default behaviour - map the variable data type to a json-schema type.
  if (VARIABLE_TYPE_MAP.hasOwnProperty(variable.dataType))
    return {type: VARIABLE_TYPE_MAP[variable.dataType]};
  return {
    type: 'string',
    format: FORMAT_TYPE_MAP[variable.dataType],
  };
};

const fetchTargetPaths = async (
  csrftoken,
  objectsApiGroup,
  objecttype,
  objecttypeVersion,
  schemaType
) => {
  const response = await post(REGISTRATION_OBJECTS_TARGET_PATHS, csrftoken, {
    objectsApiGroup,
    objecttype,
    objecttypeVersion,
    variableJsonSchema: schemaType,
  });

  if (!response.ok) {
    throw new Error(`Error when loading target paths for type: ${schemaType}`);
  }

  return response.data;
};

export {asJsonSchema, fetchTargetPaths};
