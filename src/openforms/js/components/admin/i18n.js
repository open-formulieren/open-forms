const loadLocaleData = (locale) => {
    switch (locale) {
        case 'nl':
            return import('../../compiled-lang/nl.json');
        default:
            return import('../../compiled-lang/en.json');
    }
};


const getIntlProviderProps = async () => {
    const lang = document.querySelector('html').getAttribute('lang');
    const messages = await loadLocaleData(lang);
    return {
        messages,
        locale: lang,
        defaultLocale: 'en'
    };
};


export {loadLocaleData, getIntlProviderProps};
