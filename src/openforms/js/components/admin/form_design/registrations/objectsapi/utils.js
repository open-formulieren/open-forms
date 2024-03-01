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
 * @returns {Object} - The JSON Schema
 */
const asJsonSchema = variable => {
  if (VARIABLE_TYPE_MAP.hasOwnProperty(variable.dataType))
    return {type: VARIABLE_TYPE_MAP[variable.dataType]};
  return {
    type: 'string',
    format: FORMAT_TYPE_MAP[variable.dataType],
  };
};

export {getErrorMarkup, getFieldErrors, asJsonSchema};
