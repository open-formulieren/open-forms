const getChoicesFromSchema = (enums, enumNames) => {
  const finalChoices = [];
  Object.keys(enums).forEach(key => {
    finalChoices.push([enums[key], enumNames[key]]);
  });

  return finalChoices;
};

const filterErrors = (name, errors) => {
  return errors
    .filter(([key]) => key.startsWith(`${name}.`))
    .map(([key, msg]) => [key.slice(name.length + 1), msg]);
};

export {getChoicesFromSchema, filterErrors};
