import React from 'react';

// TODO This is duplicated from the ZGW registration, but will be cleaned up
// with the backend UI refactor.

const getFieldErrors = (name, index, errors, field) => {
  const errorMessages = [];

  for (const [errorName, errorReason] of errors) {
    if (errorName.startsWith(name)) {
      const errorNameBits = errorName.split('.');
      if (errorNameBits[2] === String(index) && errorNameBits.at(-1) === field) {
        errorMessages.push(errorReason);
      }
    }
  }

  return errorMessages.length > 0 ? errorMessages : null;
};

const getErrorMarkup = errorMessages => {
  return (
    <ul className="error-detail bs-callout bs-callout-info">
      {errorMessages.map((msg, index) => (
        <li key={index} className="text-danger">
          {msg}
        </li>
      ))}
    </ul>
  );
};

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
const asJsonSchema = (variable, components) => {
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

export {getErrorMarkup, getFieldErrors, asJsonSchema};
