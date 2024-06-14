/**
 * Utilities to manage the translations/localisation of components in the form builder.
 */
import get from 'lodash/get';

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

export const extractComponentLiterals = component => {
  const allTranslatableProperties = [
    ...ALWAYS_TRANSLATABLE_PROPERTIES,
    ...(ADDITIONAL_PROPERTIES_BY_COMPONENT_TYPE[component.type] || []),
  ];

  const isDateOrDatetimeComponent = ['date', 'datetime'].includes(component.type);
  const finalTranslatableProperties = allTranslatableProperties
    // Do not show warnings for date/datetime placeholders, they are not translatable:
    .filter(property => (isDateOrDatetimeComponent ? property !== 'placeholder' : property))
    .filter(property => !isRegex(property))
    .map(property => ({property, literal: get(component, property)}));

  // See ADDITIONAL_PROPERTIES_BY_COMPONENT_TYPE for the reverse check
  switch (component.type) {
    case 'select': {
      const values = component?.data?.values || [];
      finalTranslatableProperties.push(
        ...values.map(v => ({property: 'values_label', literal: v.label}))
      );
      break;
    }
    case 'selectboxes':
    case 'radio': {
      const values = component?.values || [];
      finalTranslatableProperties.push(
        ...values.map(v => ({property: 'values_label', literal: v.label}))
      );
      break;
    }
  }

  return finalTranslatableProperties.filter(property => !!property.literal);
};
