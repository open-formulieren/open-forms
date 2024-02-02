import React from 'react';

const getChoicesFromSchema = (enums, enumNames) => {
  let finalChoices = {};
  Object.keys(enums).forEach(key => {
    finalChoices[enums[key]] = enumNames[key];
  });

  return finalChoices;
};

const getFieldErrors = (name, index, errors, field) => {
  const errorMessages = [];

  for (const [errorName, errorReason] of errors) {
    if (errorName.startsWith(name)) {
      const errorNameBits = errorName.split('.');
      if (errorNameBits[2] === String(index) && errorNameBits[errorNameBits.length - 1] === field) {
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

export {getChoicesFromSchema, getErrorMarkup, getFieldErrors};
