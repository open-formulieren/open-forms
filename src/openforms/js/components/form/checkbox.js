import {Formio} from 'formiojs';

import {localiseSchema} from './i18n';

const Checkbox = Formio.Components.components.checkbox;

class CheckboxField extends Checkbox {
  constructor(...args) {
    super(...args);

    // somewhere the default emptyValue/defaultValue does not seem to be used and it forces
    // component.defaultValue to be null, which causes issues with multiples #4659
    if (this.component.defaultValue === null) {
      this.component.defaultValue = '';
    }
  }

  static schema(...extend) {
    return localiseSchema(Checkbox.schema(...extend));
  }

  static get builderInfo() {
    return {
      ...Checkbox.builderInfo,
      schema: CheckboxField.schema(),
    };
  }
}

export default CheckboxField;
