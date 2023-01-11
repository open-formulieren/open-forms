import merge from 'lodash/merge';

const TRANSLATABLE_FIELDS = [
  'label',
  'description',
  'placeholder',
  'defaultValue',
  'tooltip',
  'values.label',
  'html',
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

const generateComponentTranslations = (configuration, componentTranslations) => {
  let finalTranslations = {};
  FormioUtils.eachComponent(configuration.components, component => {
    finalTranslations = merge(
      finalTranslations,
      generateComponentTranslations(component, componentTranslations)
    );
  });

  if (configuration.display !== 'form') {
    let values = [];
    for (const field of TRANSLATABLE_FIELDS) {
      values = values.concat(getValuesOfField(configuration, field));
    }

    let mutatedTranslations = {};
    for (const [languageCode, translations] of Object.entries(componentTranslations)) {
      let additionalTranslations = {};
      for (const value of values) {
        if (!translations[value]) {
          additionalTranslations[value] = '';
        }
      }
      mutatedTranslations[languageCode] = {...translations, ...additionalTranslations};
    }
    finalTranslations = merge(finalTranslations, mutatedTranslations);
  }
  return finalTranslations;
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

    // Sort the translations to ensure a consistent ordering for all languages
    if (mutatedTranslations[languageCode]) {
      mutatedTranslations[languageCode] = mutatedTranslations[languageCode].sort((a, b) =>
        a.literal > b.literal ? 1 : -1
      );
    }
  }
  return mutatedTranslations;
};

const removeEmptyTranslations = componentTranslations => {
  let cleanedTranslations = {};
  for (const [languageCode, translations] of Object.entries(componentTranslations)) {
    cleanedTranslations[languageCode] = {};
    for (const [literal, translation] of Object.entries(translations)) {
      if (!!translation) cleanedTranslations[languageCode][literal] = translation;
    }
  }
  return cleanedTranslations;
};

export {
  mutateTranslations,
  getValuesOfField,
  TRANSLATABLE_FIELDS,
  generateComponentTranslations,
  removeEmptyTranslations,
};
