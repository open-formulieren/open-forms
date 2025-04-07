import {Formio} from 'formiojs';

import {localiseSchema} from './i18n';

const Checkbox = Formio.Components.components.checkbox;

class CheckboxField extends Checkbox {
  static schema(...extend) {
    return localiseSchema(Checkbox.schema({defaultValue: false}, ...extend));
  }

  static get builderInfo() {
    return {
      ...Checkbox.builderInfo,
      schema: CheckboxField.schema(),
    };
  }

  get defaultSchema() {
    return CheckboxField.schema();
  }
}

export default CheckboxField;
