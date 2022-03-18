import {Formio} from 'formiojs';

import {ADVANCED, DEFAULT_SENSITIVE_TABS, REGISTRATION, SENSITIVE_BASIC, VALIDATION} from './edit/tabs';
import {REGEX_VALIDATION} from './edit/options';

const PhoneNumber = Formio.Components.components.phoneNumber;


class PhoneNumberField extends PhoneNumber {

    static schema(...extend) {
        return PhoneNumber.schema({
            inputMask: null
        }, ...extend);
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
        const validationTab = {
            ...VALIDATION,
            components: [
                ...VALIDATION.components,
                REGEX_VALIDATION
            ]
        };

        const extendedDefaults = {
            type: 'tabs',
            key: 'tabs',
            components: [
                SENSITIVE_BASIC,
                ADVANCED,
                validationTab,
                REGISTRATION,
            ]
        };

        return {components: [extendedDefaults]};
    }

    get defaultSchema() {
        return PhoneNumberField.schema();
    }

}

export default PhoneNumberField;
