import {Formio} from 'formiojs';

import {localiseSchema} from './i18n';

const FormioNumber = Formio.Components.components.number;

export const patchValidateDefaults = instance => {
  // Similar fix to the one in the textfield component. For some reason, Formio defaults
  // to empty strings for numeric values instead of using null or undefined :/
  const validate = instance.component?.validate;

  if (validate?.min === '') {
    delete validate.min;
  }
  if (validate?.max === '') {
    delete validate.max;
  }
};

class NumberField extends FormioNumber {
  static schema(...extend) {
    return localiseSchema(FormioNumber.schema(...extend));
  }

  static get builderInfo() {
    return {
      title: 'Number',
      icon: 'hashtag',
      group: 'basic',
      documentation: '/userguide/#number',
      weight: 30,
      schema: {...NumberField.schema(), validateOn: 'blur'},
    };
  }

  constructor(...args) {
    super(...args);

    patchValidateDefaults(this);
  }

  get defaultValue() {
    let defaultValue = super.defaultValue;

    // Issue #1550: this fix is present in FormIO from v4.14 so can be removed once we upgrade
    if (!this.component.multiple && _.isArray(defaultValue)) {
      defaultValue = !defaultValue[0] && defaultValue[0] !== 0 ? null : defaultValue[0];
    }

    return defaultValue;
  }
}

export default NumberField;
