import {Formio} from 'formiojs';

import {localiseSchema} from './i18n';
import {patchValidateDefaults} from './textfield';

const FormioEmail = Formio.Components.components.email;

class EmailField extends FormioEmail {
  static schema(...extend) {
    const schema = FormioEmail.schema(
      {
        defaultValue: '',
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

  constructor(...args) {
    super(...args);

    patchValidateDefaults(this);
  }

  get defaultSchema() {
    return EmailField.schema();
  }
}

export default EmailField;
