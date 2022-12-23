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
import TextField from './textfield';

class PasswordinputField extends TextField {
  static schema(...extend) {
    return TextField.schema(
      {
        type: 'textfield',
        label: 'Password',
        key: 'passwordField',
        autocomplete: 'password',
      },
      ...extend
    );
  }

  static get builderInfo() {
    return {
      title: 'Password',
      icon: 'asterisk',
      group: 'preset',
      weight: 10,
      schema: PasswordinputField.schema(),
    };
  }

  static editForm() {
    return {
      components: [
        {
          ...DEFAULT_SENSITIVE_TABS,
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

  get defaultSchema() {
    return PasswordinputField.schema();
  }
}

export default PasswordinputField;
