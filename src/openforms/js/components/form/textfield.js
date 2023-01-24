import {Formio} from 'react-formio';

import {DEFAULT_TEXT_TABS} from './edit/tabs';
import {localiseSchema} from './i18n';

const FormioTextField = Formio.Components.components.textfield;

class TextField extends FormioTextField {
  static schema(...extend) {
    return localiseSchema(FormioTextField.schema(...extend));
  }

  static get builderInfo() {
    return {
      ...FormioTextField.builderInfo,
      schema: TextField.schema(),
    };
  }

  static editForm() {
    return {components: [DEFAULT_TEXT_TABS]};
  }
}

export default TextField;
