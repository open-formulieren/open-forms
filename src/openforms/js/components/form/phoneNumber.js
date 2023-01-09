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

    const BASIC_TAB = {
      ...SENSITIVE_BASIC,
      components: [
        ...SENSITIVE_BASIC.components,
        {
          type: 'textfield',
          key: 'autocomplete',
          label: 'Autocomplete',
          placeholder: 'telinvul',
          tooltip: 'Display options to fill in the field, based on earlier typed values.',
        },
        ...extra,
      ],
    };

    const extendedDefaults = {
      type: 'tabs',
      key: 'tabs',
      components: [BASIC_TAB, ADVANCED, validationTab, REGISTRATION, TRANSLATIONS],
    };

    return {components: [extendedDefaults]};
  }

  get defaultSchema() {
    return PhoneNumberField.schema();
  }
}

export default PhoneNumberField;
