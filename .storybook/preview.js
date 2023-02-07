// In order to include these styles, the Django command `collectstatic` has to be used first
import '../static/admin/css/admin-index.css';
import '../static/admin/css/base.css';
import '../static/admin/css/forms.css';
import '../static/admin/css/widgets.css';

import '../src/openforms/scss/screen.scss';
import '../src/openforms/scss/admin/admin_overrides.scss';
import {reactIntl} from './reactIntl.js';

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
