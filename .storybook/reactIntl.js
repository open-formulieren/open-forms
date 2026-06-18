import enMessages from '../src/openforms/js/compiled-lang/en.json';
import nlMessages from '../src/openforms/js/compiled-lang/nl.json';

// Populate the messages object
const messages = {
  nl: nlMessages,
  en: enMessages,
};

const formats = {}; // optional, if you have any formats

export const reactIntl = {
  defaultLocale: 'nl',
  locales: Object.keys(messages),
  messages,
  formats,
};
