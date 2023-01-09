import {Formio} from 'formiojs';

import DEFAULT_TABS, {
  ADVANCED,
  REGISTRATION,
  SENSITIVE_BASIC,
  TRANSLATIONS,
  VALIDATION,
} from './edit/tabs';

const FormioEmail = Formio.Components.components.email;

class EmailField extends FormioEmail {
  static schema(...extend) {
    return FormioEmail.schema(
      {
        validateOn: 'blur',
      },
      ...extend
    );
  }

  static get builderInfo() {
    return {
      title: 'Email',
      group: 'basic',
      icon: 'at',
      documentation: '/userguide/#email',
      weight: 10,
    };
  }

  static editForm() {
    const extra = [
      {
        type: 'checkbox',
        key: 'confirmationRecipient',
        label: 'Receives confirmation email',
        tooltip: 'Email-address in this field will receive the confirmation email.',
      },
    ];

    const BASIC_TAB = {
      ...SENSITIVE_BASIC,
      components: [
        ...SENSITIVE_BASIC.components,
        {
          type: 'textfield',
          key: 'autocomplete',
          label: 'Autocomplete',
          placeholder: 'email',
          tooltip: 'Display options to fill in the field, based on earlier typed values.',
        },
        ...extra,
      ],
    };

    const TABS = {
      ...DEFAULT_TABS,
      components: [BASIC_TAB, ADVANCED, VALIDATION, REGISTRATION, TRANSLATIONS],
    };
    return {components: [TABS]};
  }
}

export default EmailField;
