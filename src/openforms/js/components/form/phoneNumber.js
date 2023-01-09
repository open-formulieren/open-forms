import {Formio} from 'formiojs';

import {REGEX_VALIDATION} from './edit/options';
import {ADVANCED, REGISTRATION, SENSITIVE_BASIC, TRANSLATIONS, VALIDATION} from './edit/tabs';
import {getValidationEditForm} from './edit/validationEditFormUtils';

const PhoneNumber = Formio.Components.components.phoneNumber;

class PhoneNumberField extends PhoneNumber {
  static schema(...extend) {
    return PhoneNumber.schema(
      {
        inputMask: null,
        autocomplete: 'tel',
      },
      ...extend
    );
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

  static editForm() {
    const validationTab = getValidationEditForm({
      ...VALIDATION,
      components: [...VALIDATION.components, REGEX_VALIDATION],
    });

    const extendedDefaults = {
      type: 'tabs',
      key: 'tabs',
      components: [SENSITIVE_BASIC, ADVANCED, validationTab, REGISTRATION, TRANSLATIONS],
    };

    return {components: [extendedDefaults]};
  }

  get defaultSchema() {
    return PhoneNumberField.schema();
  }
}

export default PhoneNumberField;
