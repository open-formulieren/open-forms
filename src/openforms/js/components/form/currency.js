import {Formio} from 'formiojs';
import _ from 'lodash';

import CurrencyEditData from 'formiojs/components/currency/editForm/Currency.edit.data';
import DEFAULT_TABS, {ADVANCED, BASIC, REGISTRATION, VALIDATION} from './edit/tabs';
import {DECIMAL_PLACES} from './edit/components';

const FormioCurrency = Formio.Components.components.currency;

CurrencyEditData[0].defaultValue = 'EUR';

class CurrencyField extends FormioCurrency {

    get defaultValue() {
        let defaultValue = super.defaultValue;

        // Issue #1550: this fix is present in FormIO from v4.14 so can be removed once we upgrade
        if (!this.component.multiple && _.isArray(defaultValue)) {
          defaultValue = !defaultValue[0] &&  defaultValue[0] !== 0 ? null :  defaultValue[0];
        }

        return defaultValue;
    }

    static editForm() {
        const BASIC_TAB = {
            ...BASIC,
            components: [
                ...BASIC.components,
                ...CurrencyEditData,
                ...[DECIMAL_PLACES],
            ]
        };
        const TABS = {
            ...DEFAULT_TABS,
            components: [
                BASIC_TAB,
                ADVANCED,
                VALIDATION,
                REGISTRATION,
            ]
        };
        return {components: [TABS]};
    }
}

export default CurrencyField;
