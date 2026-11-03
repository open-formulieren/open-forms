const loadLocaleData = async locale => {
  switch (locale) {
    case 'nl':
      return await import('../../compiled-lang/nl.json').default;
    default:
      return await import('../../compiled-lang/en.json').default;
  }
};

const getIntlProviderProps = async () => {
  const lang = document.querySelector('html').getAttribute('lang');
  const messages = await loadLocaleData(lang);
  return {
    messages,
    locale: lang,
    defaultLocale: 'en',
  };
};

export {loadLocaleData, getIntlProviderProps};
