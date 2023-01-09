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
      ...DEFAULT_SENSITIVE_TABS,
      components: [
        ...DEFAULT_SENSITIVE_TABS.components,
        {
          type: 'textfield',
          key: 'autocomplete',
          label: 'Autocomplete',
          placeholder: 'currentpassword',
          tooltip: 'Display options to fill in the field, based on earlier typed values.',
        },
        ...extra,
      ],
    };

    return {
      components: [
        {
          ...BASIC_TAB,
          components: [
            {
              ...SENSITIVE_BASIC,
              components: SENSITIVE_BASIC.components.filter(
                option => option.key !== DEFAULT_VALUE.key
              ),
            },
            ADVANCED,
            VALIDATION,
            REGISTRATION,
            TRANSLATIONS,
          ],
        },
      ],
    };
  }
}

export default PasswordField;
