import {Formio} from 'formiojs';

import DEFAULT_TABS, {
  ADVANCED,
  REGISTRATION,
  SENSITIVE_BASIC,
  TRANSLATIONS,
  VALIDATION,
} from './edit/tabs';

const FormioEmail = Formio.Components.components.email;

class EmailaddressField extends FormioEmail {
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
      group: 'preset',
      icon: 'at',
      documentation: '/userguide/#email',
      weight: 10,
      autocomplete: 'email',
      schema: EmailaddressField.schema(),
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
      components: [...SENSITIVE_BASIC.components, ...extra],
    };
    const TABS = {
      ...DEFAULT_TABS,
      components: [BASIC_TAB, ADVANCED, VALIDATION, REGISTRATION, TRANSLATIONS],
    };
    return {components: [TABS]};
  }
}

export default EmailaddressField;
