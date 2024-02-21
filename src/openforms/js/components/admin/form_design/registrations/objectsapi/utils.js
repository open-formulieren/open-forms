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

export {getErrorMarkup, getFieldErrors};
