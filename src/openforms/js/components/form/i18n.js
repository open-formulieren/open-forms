import * as en from 'lang/formio/en.json';
import * as nl from 'lang/formio/nl.json';

/**
 * Component.schema is a static method called dozens of times from sync code,
 * but Formio does not properly manage its state with React.
 * Trying to use dynamic loading and Promises will make you cry and not work
 * on every 3rd and 5th blink. It will play FizzBuzz with your tears.
 **/

const localeData = {
  nl: nl,
  en: en,
};

const localiseSchema = schema => {
  const lang = document.documentElement.lang;
  if (!localeData[lang]) return schema;

  const t = s => localeData[lang][s] || s;

  return {
    ...schema,
    label: t(schema.label),
    key: t(schema.key),
  };
};

export {localiseSchema};
