import {Formio} from 'react-formio';

import {localiseSchema} from './i18n';

const FormioPasswordField = Formio.Components.components.password;

class PasswordField extends FormioPasswordField {
  static schema(...extend) {
    return localiseSchema(FormioPasswordField.schema(...extend));
  }

  static get builderInfo() {
    return {
      ...FormioPasswordField.builderInfo,
      schema: PasswordField.schema(),
    };
  }

  get defaultSchema() {
    return PasswordField.schema();
  }
}

export default PasswordField;
