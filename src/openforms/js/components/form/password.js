import {Formio} from 'react-formio';

import {AUTOCOMPLETE, DEFAULT_VALUE} from './edit/options';
import {ADVANCED, REGISTRATION, SENSITIVE_BASIC, TRANSLATIONS, VALIDATION} from './edit/tabs';

const FormioPasswordField = Formio.Components.components.password;

class PasswordField extends FormioPasswordField {
  get defaultSchema() {
    // In Formio, the 'protected' attribute is removed from the default schema. This makes it not end up in the
    // component configuration
    return PasswordField.schema();
  }

  static editForm() {
    // option
    const extra = [{...AUTOCOMPLETE, placeholder: 'password'}];
    // lowest tab, extend SENSITIVE_BASIC that is inside DEFAULT_SENSITIVE_TABS
    const BASIC_PASSWORD_TAB = {
      ...SENSITIVE_BASIC,
      components: [
        {
          ...SENSITIVE_BASIC,
          components: SENSITIVE_BASIC.components.filter(option => option.key !== DEFAULT_VALUE.key),
        },
        ...extra,
      ],
    };
    // replace higher DEFAULT_SENSITIVE_TAB
    const DEFAULT_SENSITIVE_TABS_EXTRA = {
      type: 'tabs',
      key: 'tabs',
      components: [BASIC_PASSWORD_TAB, ADVANCED, VALIDATION, REGISTRATION, TRANSLATIONS],
    };

    return {components: [DEFAULT_SENSITIVE_TABS_EXTRA]};
  }
}

export default PasswordField;
