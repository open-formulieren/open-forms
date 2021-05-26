import {Formio} from 'formiojs';
import {defineCommonEditFormTabs} from './abstract';

defineCommonEditFormTabs(Formio.Components.components.checkbox, [
    {
        input: true,
        key: 'defaultValue',
        label: 'Default Value',
        placeholder: 'Default Value',
        tooltip: 'This will be the value for this field before user interaction. Having a default value will override the placeholder text.',
        type: 'checkbox',
        weight: 5
    }
]);
