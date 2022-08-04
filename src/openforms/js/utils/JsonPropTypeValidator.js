const jsonPropTypeValidator = (props, propName, componentName) => {
  const value = props[propName];
  if (value === '') return;

  try {
    JSON.parse(value);
  } catch (e) {
    return new Error(
      `Invalid JSON prop ${propName} supplied to ${componentName}. Validation failed.`
    );
  }
};

export default jsonPropTypeValidator;
