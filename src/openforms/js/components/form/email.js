import {Formio} from 'formiojs';

import {AUTOCOMPLETE} from './edit/options';
import DEFAULT_TABS, {
  ADVANCED,
  REGISTRATION,
  SENSITIVE_BASIC,
  TRANSLATIONS,
  VALIDATION,
} from './edit/tabs';
import {localiseSchema} from './i18n';

const FormioEmail = Formio.Components.components.email;

class EmailField extends FormioEmail {
  static schema(...extend) {
    const schema = FormioEmail.schema(
      {
        validateOn: 'blur',
      },
      ...extend
    );
    return localiseSchema(schema);
  }

  static get builderInfo() {
    return {
      title: 'Email',
      group: 'advanced',
      icon: 'at',
      documentation: '/userguide/#email',
      weight: 10,
      schema: EmailField.schema(),
    };
  }

  static editForm() {
    const extra = [
      {...AUTOCOMPLETE, placeholder: 'email'},
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

export default EmailField;
