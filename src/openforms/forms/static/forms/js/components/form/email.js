import {Formio} from "formiojs";
import {defineCommonEditFormTabs} from "./abstract";

defineCommonEditFormTabs(
    Formio.Components.components.email,
    [{
        type: 'checkbox',
        key: 'multiple',
        label: 'Multiple values',
        tooltip: 'Allow multiple values to be entered for this field'
    }]
);
