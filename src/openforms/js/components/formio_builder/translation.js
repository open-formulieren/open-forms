/**
 * Utilities to manage the translations/localisation of components in the form builder.
 */
import BUILDER_REGISTRY from '@open-formulieren/formio-builder/esm/registry';
import Utils from 'formiojs/utils';
import get from 'lodash/get';
import isEmpty from 'lodash/isEmpty';
import mapValues from 'lodash/mapValues';
import merge from 'lodash/merge';
import pickBy from 'lodash/pickBy';
import set from 'lodash/set';

import jsonScriptToVar from 'utils/json-script';

export const nlStrings = require('lang/formio/nl.json');
export default nlStrings;

let _supportedLanguages = undefined;
export const getSupportedLanguages = () => {
  if (_supportedLanguages !== undefined) return _supportedLanguages;
  _supportedLanguages = jsonScriptToVar('languages', {default: []});
  return _supportedLanguages;
};

export const LANGUAGES = getSupportedLanguages().map(([langCode]) => langCode);

/**
 * Name of translatable Formio component properties that are generic and independent of
 * the exact component type.
 * @type {string[]}
 */
const ALWAYS_TRANSLATABLE_PROPERTIES = ['label', 'description', 'placeholder', 'tooltip'];

/**
 * Mapping of formio component type to a list of additional translatable properties.
 * @type {Object} Mapping of type to list of strings or regular expression patterns to
 *   test the property path against.
 */
const ADDITIONAL_PROPERTIES_BY_COMPONENT_TYPE = {
  textfield: ['defaultValue'],
  textarea: ['defaultValue'],
  content: ['html'],
  fieldset: ['legend'],
  editgrid: ['groupLabel'],
  // manually entered data values -> labels are translatable
  select: [/data\.values\[[0-9]+\]\.label/],
  selectboxes: [/values\[[0-9]+\]\.label/],
  radio: [/values\[[0-9]+\]\.label/],
};

const isRegex = item => {
  return typeof item.test === 'function';
};

/**
 * Determine if the property/path is a component property that is translated.
 *
 * This maps to semantics of Formio itself, depending on whether this.t or ctx.t is
 * called on the _value_ of the property during rendering of the form. We actually
 * perform these same translations in the backend, but stick to the Formio mechanisms
 * to stay compatible.
 *
 * NOTE: keep this in sync with the backend, see relevant test case:
 * openforms.submissions.tests.test_submission_report:
 * DownloadSubmissionReportTests.test_report_is_generated_in_same_language_as_submission
 *
 * @param  {String} componentType Type of the formio component. Different types may have different relevant properties.
 * @param  {String} property      The formio component path, e.g. 'label' or 'validate.required'
 * @return {Boolean}              True if the value can be translated, False otherwise.
 */
export const isTranslatableProperty = (componentType, property) => {
  // we have a different UI for the content/html translations, relying on only ever
  // one property being translatable.
  if (componentType === 'content') {
    return property === 'html';
  }

  const allTranslatableProperties = ALWAYS_TRANSLATABLE_PROPERTIES.concat(
    ADDITIONAL_PROPERTIES_BY_COMPONENT_TYPE[componentType] || []
  );
  return allTranslatableProperties.some(entry => {
    // entry is either a string or a regex. A regex has the 'test' method.
    if (isRegex(entry)) {
      return entry.test(property);
    }
    // otherwise -> strict string equality check
    return entry === property;
  });
};

/**
 * Update the container holding all the component translations with the translations
 * of a particular component.
 *
 * @param  {Object} container Key-value mapping, key is language code, values are mappings
 *                            of literals to their translations *for that language code*.
 * @param  {Object} component Formio component/schema - it contains the configuration
 *                            of one particular component in the form builder.
 * @return {Void}             The container is mutated directly. It is advised to pass
 *                            in an Immer draft or carefully manage mutable objects.
 */
export const persistComponentTranslations = (container, component) => {
  const translations = component?.openForms?.translations;
  if (!translations) return;

  // 1. Transform the array of translations per language code into a mapping to
  //    fit our storage schema.
  const mappedTranslations = mapValues(translations, translations => {
    return Object.fromEntries(translations.map(({literal, translation}) => [literal, translation]));
  });

  // 2. Update the component translations store, shared by all components in the
  //    form step. This performs a deep merge.
  merge(container, mappedTranslations);

  // 3. Once the translations are processed, we don't need to store them in the
  // component itself anymore - this is handled dynamically via the FormioBuilder
  // onChange handler.
  delete component.openForms.translations;
};

export const extractComponentLiterals = component => {
  const allTranslatableProperties = [
    ...ALWAYS_TRANSLATABLE_PROPERTIES,
    ...(ADDITIONAL_PROPERTIES_BY_COMPONENT_TYPE[component.type] || []),
  ];

  const isDateOrDatetimeComponent = ['date', 'datetime'].includes(component.type);
  const literals = allTranslatableProperties
    // Do not show warnings for date/datetime placeholders, they are not translatable:
    .filter(property => (isDateOrDatetimeComponent ? property !== 'placeholder' : property))
    .filter(property => !isRegex(property))
    .map(property => get(component, property));

  // See ADDITIONAL_PROPERTIES_BY_COMPONENT_TYPE for the reverse check
  switch (component.type) {
    case 'select': {
      const values = component?.data?.values || [];
      literals.push(...values.map(v => v.label));
      break;
    }
    case 'selectboxes':
    case 'radio': {
      const values = component?.values || [];
      literals.push(...values.map(v => v.label));
      break;
    }
  }
  return literals.filter(literal => !!literal);
};

/**
 * Update the translations container by removing all the translations/literals for
 * literals that are not/no longer present in the full Formio form configuration.
 * @param  {Object} container Key-value mapping, key is language code, values are mappings
 *                            of literals to their translations *for that language code*.
 * @param  {Object} fullConfiguration A Formio form definition, e.g.
 *                                    {"display": "form", "components": [...]}
 * @return {Object} Container with the obsolete literals and empty translations removed.
 */
export const clearObsoleteLiterals = (container, fullConfiguration) => {
  // first, extract all the literals used for every component in the form.
  const allLiterals = [];
  Utils.eachComponent(
    fullConfiguration.components,
    component => {
      allLiterals.push(...extractComponentLiterals(component));
    },
    true
  );
  const uniqueLiterals = [...new Set(allLiterals)];
  const mapped = mapValues(container, translations => {
    // translations is a key-value mapping of strings (literal -> translation)
    return pickBy(
      translations,
      (translation, literal) => uniqueLiterals.includes(literal) && !!translation
    );
  });
  return mapped;
};

export const addTranslationForLiteral = (
  component,
  allComponentTranslations,
  prevLiteral,
  newLiteral
) => {
  const existingTranslations = component?.openForms?.translations || {};
  for (const langCode of LANGUAGES) {
    if (existingTranslations[langCode]) continue;
    existingTranslations[langCode] = [];
  }
  const componentLiterals = [...new Set(extractComponentLiterals(component))];

  // TODO: refactor to mapValues
  let newTranslations = {};
  for (const [langCode, translations] of Object.entries(existingTranslations)) {
    // find any existing translation for the new literal used, either in local (new)
    // translations, or in the componentTranslations store
    const existingTranslation =
      translations.find(({literal}) => literal == newLiteral)?.translation ||
      allComponentTranslations[langCode]?.[newLiteral];

    // add it only if the literal is not present yet
    const existingEntry = translations.find(({literal}) => newLiteral === literal);
    if (!existingEntry) {
      const prevTranslation =
        translations.find(({literal}) => prevLiteral === literal)?.translation || '';
      translations.push({
        literal: newLiteral,
        // favour component level translations over local IF there are collissions.
        // These translations would typically have been set by another component
        // already.
        translation: existingTranslation || prevTranslation,
      });
    }

    // finally, filter out translations for which the literal is not used in this
    // component.
    const translationsToKeep = translations.filter(({literal}) => {
      if (!componentLiterals.includes(literal)) {
        return false;
      }
      return true;
    });
    newTranslations[langCode] = translationsToKeep;
  }
  return newTranslations;
};

export const handleComponentValueLiterals = (
  component,
  allComponentTranslations,
  propertyPath,
  values,
  previousLiterals
) => {
  // don't bother doing anything if it's not the right component type.
  switch (component.type) {
    case 'select': {
      if (propertyPath !== 'data.values') return null;
      break;
    }
    case 'selectboxes':
    case 'radio': {
      if (propertyPath !== 'values') return null;
      break;
    }
    default:
      return null;
  }
  let translations = component?.openForms?.translations || {};
  const nonEmptyValues = values.filter(item => !isEmpty(item));
  if (!nonEmptyValues.length) return null;
  nonEmptyValues.forEach(({label = ''}, index) => {
    const componentCopy = {
      ...component,
      openForms: {...component.openForms, translations: translations},
    };
    translations = addTranslationForLiteral(
      componentCopy,
      allComponentTranslations,
      undefined,
      label
    );
    // track the value as 'previous literal' in the ref
    const _propertyPath = `${propertyPath}[${index}].label`;
    set(previousLiterals, [_propertyPath], label);
  });
  return translations;
};

export const isNewBuilderComponent = component => {
  return BUILDER_REGISTRY.hasOwnProperty(component.type);
};
