import {IntlProvider} from 'react-intl';

import {FormContext} from './Context';
import LanguageTabs from './LanguageTabs';

const languageMapping = [
  {code: 'nl', label: 'Nederlands'},
  {code: 'en', label: 'Engels'},
];

const render = args => {
  return (
    <IntlProvider messages={{}} locale={'nl'} defaultLocale="nl">
      <FormContext.Provider
        value={{
          languages: languageMapping,
        }}
      >
        <LanguageTabs haveErrors={args.haveErrors}>
          {(langCode, defaultLang) => <div>{langCode}</div>}
        </LanguageTabs>
      </FormContext.Provider>
    </IntlProvider>
  );
};

export default {
  title: 'Form design/LanguageTabs',
  component: LanguageTabs,
  render: render,
};

export const Default = {
  name: 'Default',

  args: {
    haveErrors: [],
  },
};

export const WithErrors = {
  name: 'With errors',

  args: {
    haveErrors: ['nl'],
  },
};
