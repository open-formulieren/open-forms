import {Formio} from 'react-formio';

import {DEFAULT_VALUE} from './edit/options';
import {
  ADVANCED,
  DEFAULT_SENSITIVE_TABS,
  REGISTRATION,
  SENSITIVE_BASIC,
  TRANSLATIONS,
  VALIDATION,
} from './edit/tabs';

class PasswordField extends Formio.Components.components.password {
  static editForm() {
    const BASIC_TAB = {
      ...SENSITIVE_BASIC,
      components: [
        ...SENSITIVE_BASIC.components.filter(option => option.key !== DEFAULT_VALUE.key),
        {
          type: 'textfield',
          key: 'autocomplete',
          label: 'Autocomplete',
          placeholder: 'password',
          tooltip: 'Display options to fill in the field, based on earlier typed values.',
        },
        ,
      ],
    };

    const extendedPasswordDefaults = {
      components: [BASIC_TAB, ADVANCED, VALIDATION, REGISTRATION, TRANSLATIONS],
    };

    return {
      components: [extendedPasswordDefaults],
    };
  }
}

export default PasswordField;
