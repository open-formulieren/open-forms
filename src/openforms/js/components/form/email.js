import {Formio} from "formiojs";
import DEFAULT_TABS, {ADVANCED, SENSITIVE_BASIC, REGISTRATION, VALIDATION} from "./edit/tabs";


class EmailField extends Formio.Components.components.email {
    static editForm() {
        const extra = [
            {
                type: 'checkbox',
                key: 'multiple',
                label: 'Multiple values',
                tooltip: 'Allow multiple values to be entered for this field'
            },
            {
                type: 'checkbox',
                key: 'confirmationRecipient',
                label: 'Receives confirmation email',
                tooltip: 'Email-address in this field will receive the confirmation email.',
            }
        ];
        const BASIC_TAB = {
            ...SENSITIVE_BASIC,
            components: [
                ...SENSITIVE_BASIC.components,
                ...extra,
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

export default EmailField;
