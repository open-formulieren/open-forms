import ReactModal from 'react-modal';
import '../src/openforms/scss/screen.scss';
import '../src/openforms/scss/admin/admin_overrides.scss';
import {reactIntl} from './reactIntl.js';

ReactModal.setAppElement('#root');

export const parameters = {
  reactIntl,
  locale: reactIntl.defaultLocale,
  locales: {
    nl: 'Nederlands',
    en: 'English',
  },
  actions: {argTypesRegex: '^on[A-Z].*'},
  controls: {
    matchers: {
      color: /(background|color)$/i,
      date: /Date$/,
    },
  },
};
