export const getChoicesFromSchema = (enums, enumNames) => {
  const finalChoices = [];
  Object.keys(enums).forEach(key => {
    finalChoices.push([enums[key], enumNames[key]]);
  });

  return finalChoices;
};
