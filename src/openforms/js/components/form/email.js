import {Formio} from 'formiojs';

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
}

export default EmailField;
