import FormioUtils from 'formiojs/utils';
import mapValues from 'lodash/mapValues';
import merge from 'lodash/merge';
import pick from 'lodash/pick';
import pickBy from 'lodash/pickBy';

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

const generateComponentTranslations = (
  configuration,
  componentTranslations,
  accumulatedLiterals
) => {
  // accumulatedLiterals is used in the recursion for collecting all literals used in the step.
  // Consider a step where the same literal is used in different components,
  // and then one of them gets changed.
  //
  // Only at the start and end (post/put) of editing a step is it safe to
  // remove unused literals, not in the context of a single component.

  let finalTranslations = {};
  let finalLiterals = [];

  FormioUtils.eachComponent(
    configuration.components,
    component => {
      let foundTranslations;
      [foundTranslations, finalLiterals] = generateComponentTranslations(
        component,
        componentTranslations,
        finalLiterals
      );
      merge(finalTranslations, foundTranslations);
    },
    true // content is considered a layoutComponent
  );

  if (configuration.display !== 'form') {
    let values = [];
    for (const field of TRANSLATABLE_FIELDS) {
      values = values.concat(getValuesOfField(configuration, field));
    }
    finalLiterals = finalLiterals.concat(values);

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
    merge(finalTranslations, mutatedTranslations);
  }

  return accumulatedLiterals !== undefined
    ? [finalTranslations, accumulatedLiterals.concat(finalLiterals)] // recursing
    : mapValues(finalTranslations, translations => pick(translations, finalLiterals)); // keep/"pick" only translations in finalLiterals
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

const removeEmptyTranslations = componentTranslations =>
  mapValues(componentTranslations, translations => pickBy(translations)); // keep/"pick" truthy identity

export {
  mutateTranslations,
  getValuesOfField,
  TRANSLATABLE_FIELDS,
  generateComponentTranslations,
  removeEmptyTranslations,
};
