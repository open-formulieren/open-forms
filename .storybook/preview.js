import '../src/openforms/scss/screen.scss';
import '../src/openforms/scss/admin/admin_overrides.scss';
import {initialize, mswDecorator, mswLoader} from 'msw-storybook-addon';
import {reactIntl} from './reactIntl.js';
import ReactModal from 'react-modal';

initialize({
  onUnhandledRequest: 'bypass',
  serviceWorker: {
    url: './mockServiceWorker.js',
  },
});

ReactModal.setAppElement(document.getElementById('storybook-root'));

export default {
  decorators: [mswDecorator],
  globals: {
    locale: reactIntl.defaultLocale,
    locales: {
      nl: 'Nederlands',
      en: 'English',
    },
  },
  parameters: {
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
