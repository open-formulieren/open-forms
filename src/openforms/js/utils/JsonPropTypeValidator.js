const jsonPropTypeValidator = (props, propName, componentName) => {
  const value = props[propName];
  if (value === '') return;

  let jsonToValidate = value;
  if (typeof value !== 'string') jsonToValidate = JSON.stringify(value);

  try {
    JSON.parse(jsonToValidate);
  } catch (e) {
    return new Error(
      `Invalid JSON prop ${propName} supplied to ${componentName}. Validation failed.`
    );
  }
};

export default jsonPropTypeValidator;
