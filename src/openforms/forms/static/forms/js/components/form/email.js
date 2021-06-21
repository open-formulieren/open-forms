import {Formio} from "formiojs";
import {defineCommonEditFormTabs} from "./abstract";

defineCommonEditFormTabs(
    Formio.Components.components.email,
    [{
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
    }]
);
