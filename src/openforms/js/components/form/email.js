import {Formio} from "formiojs";
import DEFAULT_TABS, {ADVANCED, SENSITIVE_BASIC, REGISTRATION, VALIDATION} from "./edit/tabs";

const FormioEmail = Formio.Components.components.email;

class EmailField extends FormioEmail {
    static schema(...extend) {
        return FormioEmail.schema({
            validateOn: 'blur'
        }, ...extend);
    }

    static get builderInfo() {
        return {
          title: 'Email',
          group: 'advanced',
          icon: 'at',
          documentation: '/userguide/#email',
          weight: 10,
          schema: EmailField.schema()
        };
    }

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
