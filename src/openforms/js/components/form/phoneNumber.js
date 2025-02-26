import {Formio} from 'formiojs';

import {localiseSchema} from './i18n';
import {patchValidateDefaults} from './textfield';

const PhoneNumber = Formio.Components.components.phoneNumber;

class PhoneNumberField extends PhoneNumber {
  static schema(...extend) {
    const schema = PhoneNumber.schema(
      {
        defaultValue: '',
        inputMask: null,
      },
      ...extend
    );
    return localiseSchema(schema);
  }

  static get builderInfo() {
    return {
      title: 'Phone Number Field',
      icon: 'phone-square',
      group: 'basic',
      weight: 10,
      schema: PhoneNumberField.schema(),
    };
  }

  constructor(...args) {
    super(...args);

    patchValidateDefaults(this);
  }

  get defaultSchema() {
    return PhoneNumberField.schema();
  }
}

export default PhoneNumberField;
