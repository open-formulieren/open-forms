import {Formio} from 'formiojs';

import {localiseSchema} from './i18n';
import {patchValidateDefaults} from './textfield';

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

  constructor(...args) {
    super(...args);

    patchValidateDefaults(this);

    // somewhere the default emptyValue/defaultValue does not seem to be used and it forces
    // component.defaultValue to be null, which causes issues with multiples #4659
    if (this.component.defaultValue === null) {
      this.component.defaultValue = '';
    }
  }
}

export default EmailField;
