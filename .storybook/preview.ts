import type {Preview} from '@storybook/react-vite';
import 'bootstrap/dist/css/bootstrap.css';
import 'leaflet';
import {initialize, mswLoader} from 'msw-storybook-addon';
import 'proj4leaflet';

import {
  TinyMceDecorator,
  withModalDecorator,
  withReactSelectDecorator,
} from 'components/admin/form_design/story-decorators';

import '../src/openforms/scss/admin/admin_overrides.scss';
import '../src/openforms/scss/screen.scss';
import {reactIntl} from './reactIntl.js';

initialize({
  onUnhandledRequest: 'bypass',
  serviceWorker: {
    url: './mockServiceWorker.js',
  },
  quiet: true, // don't output logs
});

export default {
  decorators: [withModalDecorator, withReactSelectDecorator, TinyMceDecorator],
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
} satisfies Preview;
