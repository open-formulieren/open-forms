const TRANSLATABLE_FIELDS = [
  'label',
  'description',
  'placeholder',
  'defaultValue',
  'tooltip',
  'values.label',
];

const getValuesOfField = (component, fieldName) => {
  let values = [];
  if (fieldName.includes('.')) {
    const [prefix, inner] = fieldName.split('.');
    for (const entry of component[prefix] || []) {
      values.push(entry[inner]);
    }
  } else {
    let value = component[fieldName];
    if (!value) return [];
    else if (typeof value === 'object' && !Array.isArray(value)) return [];

    values.push(component[fieldName]);
  }
  return values;
};

const mutateTranslations = (component, componentTranslations) => {
  let values = [];
  for (const field of TRANSLATABLE_FIELDS) {
    values = values.concat(getValuesOfField(component, field));
  }

  let mutatedTranslations = {};
  for (const [languageCode, translations] of Object.entries(componentTranslations)) {
    for (const [literal, translation] of Object.entries(translations)) {
      if (values.includes(literal)) {
        mutatedTranslations[languageCode] = (mutatedTranslations[languageCode] || []).concat([
          {literal: literal, translation: translation},
        ]);
      }
    }
  }
  return mutatedTranslations;
};

export {mutateTranslations, getValuesOfField};
