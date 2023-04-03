import {Formio} from 'formiojs';

import {ALLOW_NEGATIVE, DECIMAL_PLACES} from './edit/components';
import DEFAULT_TABS, {
  ADVANCED,
  BASIC,
  NUMBER_VALIDATION,
  REGISTRATION,
  TRANSLATIONS,
} from './edit/tabs';
import {localiseSchema} from './i18n';

const FormioNumber = Formio.Components.components.number;

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

  get defaultValue() {
    let defaultValue = super.defaultValue;

    // Issue #1550: this fix is present in FormIO from v4.14 so can be removed once we upgrade
    if (!this.component.multiple && _.isArray(defaultValue)) {
      defaultValue = !defaultValue[0] && defaultValue[0] !== 0 ? null : defaultValue[0];
    }

    return defaultValue;
  }

  static editForm() {
    const BASIC_TAB = {
      ...BASIC,
      components: [...BASIC.components, ...[DECIMAL_PLACES, ALLOW_NEGATIVE]],
    };
    const TABS = {
      ...DEFAULT_TABS,
      components: [BASIC_TAB, ADVANCED, NUMBER_VALIDATION, REGISTRATION, TRANSLATIONS],
    };
    return {components: [TABS]};
  }
}

export default NumberField;
