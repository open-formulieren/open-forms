import {Formio} from 'react-formio';

import {AUTOCOMPLETE, DEFAULT_VALUE} from './edit/options';
import {
  ADVANCED,
  DEFAULT_SENSITIVE_TABS,
  REGISTRATION,
  SENSITIVE_BASIC,
  TRANSLATIONS,
  VALIDATION,
} from './edit/tabs';
import {localiseSchema} from './i18n';

const FormioPasswordField = Formio.Components.components.password;

class PasswordField extends FormioPasswordField {
  static schema(...extend) {
    return localiseSchema(FormioPasswordField.schema(...extend));
  }

  static get builderInfo() {
    return {
      ...FormioPasswordField.builderInfo,
      schema: PasswordField.schema(),
    };
  }

  static editForm() {
    // option
    const extra = [{...AUTOCOMPLETE, placeholder: 'password'}];
    // lowest tab, extend SENSITIVE_BASIC that is inside DEFAULT_SENSITIVE_TABS
    const BASIC_PASSWORD_TAB = {
      ...SENSITIVE_BASIC,
      components: SENSITIVE_BASIC.components
        .filter(option => option.key !== DEFAULT_VALUE.key)
        .concat(extra),
    };
    // replace higher DEFAULT_SENSITIVE_TAB
    const DEFAULT_SENSITIVE_TABS_EXTRA = {
      type: 'tabs',
      key: 'tabs',
      components: [BASIC_PASSWORD_TAB, ADVANCED, VALIDATION, REGISTRATION, TRANSLATIONS],
    };

    return {components: [DEFAULT_SENSITIVE_TABS_EXTRA]};
  }

  get defaultSchema() {
    return PasswordField.schema();
  }
}

export default PasswordField;
