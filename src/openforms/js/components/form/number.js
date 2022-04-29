import {Formio} from 'formiojs';

import {DECIMAL_PLACES, MAX_VALUE, MIN_VALUE} from './edit/components';
import DEFAULT_TABS, {ADVANCED, BASIC, REGISTRATION, VALIDATION} from './edit/tabs';


const FormioNumber = Formio.Components.components.number;


class NumberField extends FormioNumber {

    static get builderInfo() {
        return {
            title: 'Number',
            icon: 'hashtag',
            group: 'basic',
            documentation: '/userguide/#number',
            weight: 30,
            schema: {...NumberField.schema(), validateOn: 'blur'}
        };
    }

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
                ...[DECIMAL_PLACES, MIN_VALUE, MAX_VALUE],
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


export default NumberField;
