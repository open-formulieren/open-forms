import {Formio} from 'formiojs';

import {AUTOCOMPLETE} from './edit/options';
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
      schema: EmailField.schema(),
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
      AUTOCOMPLETE,
      components: [...SENSITIVE_BASIC.components, AUTOCOMPLETE, ...extra],
    };
    const TABS = {
      ...DEFAULT_TABS,
      components: [BASIC_TAB, ADVANCED, VALIDATION, REGISTRATION, TRANSLATIONS],
    };
    return {components: [TABS]};
  }
}

export default EmailField;
