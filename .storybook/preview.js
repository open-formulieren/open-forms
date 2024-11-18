import '../src/openforms/scss/screen.scss';
import '../src/openforms/scss/admin/admin_overrides.scss';
import {withModalDecorator} from 'components/admin/form_design/story-decorators';
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
  decorators: [mswDecorator, withModalDecorator],
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
  initialGlobals: {
    locale: reactIntl.defaultLocale,
    locales: {
      nl: 'Nederlands',
      en: 'English',
    },
  },
};
