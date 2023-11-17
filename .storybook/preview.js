import '../src/openforms/scss/screen.scss';
import '../src/openforms/scss/admin/admin_overrides.scss';
import {initialize, mswDecorator, mswLoader} from 'msw-storybook-addon';
import {reactIntl} from './reactIntl.js';

initialize({
  onUnhandledRequest: 'bypass',
  serviceWorker: {
    url: './mockServiceWorker.js',
  },
});

export default {
  decorators = [mswDecorator],
  globals: {
    locale: reactIntl.defaultLocale,
    locales: {
      nl: 'Nederlands',
      en: 'English',
    },
  },
  parameters: {
    actions: {argTypesRegex: '^on[A-Z].*'},
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/,
      },
    },
    reactIntl,
  },
  loaders: [mswLoader],
};
