import {Formio} from 'formiojs';

import {patchValidateDefaults} from './textfield';

const TextField = Formio.Components.components.textfield;

class IbanField extends TextField {
  static schema(...extend) {
    return TextField.schema(
      {
        type: 'iban',
        label: 'IBAN',
        key: 'iban',
        validateOn: 'blur',
      },
      ...extend
    );
  }

  static get builderInfo() {
    return {
      title: 'IBAN Field',
      icon: 'wallet',
      group: 'basic',
      weight: 10,
      schema: IbanField.schema(),
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

  get defaultSchema() {
    return IbanField.schema();
  }
}

export default IbanField;
