const createListFromSchema = (enums, enumNames, callback) => {
  const finalChoices = [];
  Object.keys(enums).forEach(key => {
    finalChoices.push(callback(enums[key], enumNames[key]));
  });

  return finalChoices;
};

export const getChoicesFromSchema = (enums, enumNames, blankChoiceTitle = '') => {
  return createListFromSchema(enums, enumNames, (value, label) => [
    value,
    label || blankChoiceTitle,
  ]);
};

export const getReactSelectOptionsFromSchema = (enums, enumNames, blankChoiceTitle = '') => {
  return createListFromSchema(enums, enumNames, (value, label) => ({
    value,
    label: label || blankChoiceTitle,
  }));
};
