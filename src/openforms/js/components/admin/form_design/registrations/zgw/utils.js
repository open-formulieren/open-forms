import React from 'react';

const getChoicesFromSchema = (enums, enumNames) => {
  let finalChoices = {};
  Object.keys(enums).forEach(key => {
    finalChoices[enums[key]] = enumNames[key];
  });

  return finalChoices;
};

const getErrorMarkup = errorMessages => {
  return (
    <div className="rjsf-field__errors">
      <div>
        <ul className="error-detail bs-callout bs-callout-info">
          {errorMessages.map((msg, index) => (
            <li key={index} className="text-danger">
              {msg}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export {getChoicesFromSchema, getErrorMarkup};
