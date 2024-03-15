import {Formio} from 'formiojs';
import CurrencyEditData from 'formiojs/components/currency/editForm/Currency.edit.data';
import _ from 'lodash';

import {localiseSchema} from './i18n';
import {patchValidateDefaults} from './number';

const FormioCurrency = Formio.Components.components.currency;

CurrencyEditData[0].defaultValue = 'EUR';

class CurrencyField extends FormioCurrency {
  static schema(...extend) {
    return localiseSchema(FormioCurrency.schema(...extend));
  }

  static get builderInfo() {
    return {
      ...FormioCurrency.builderInfo,
      schema: CurrencyField.schema(),
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

export default CurrencyField;
