import {Formio} from 'formiojs';
import {defineChoicesEditFormTabs} from './abstract';
import DEFAULT_TABS, {ADVANCED, BASIC, REGISTRATION, VALIDATION} from "./edit/tabs";


const extra = [
    {
        label: 'Default Value',
        key: 'defaultValue',
        tooltip: 'This will be the initial value for this field, before user interaction.',
        input: true
    }, {
        type: 'datagrid',
        input: true,
        label: 'Values',
        key: 'values',
        tooltip: 'The radio button values that can be picked for this field. Values are text submitted with the form data. Labels are text that appears next to the radio buttons on the form.',
        weight: 10,
        reorder: true,
        defaultValue: [{label: '', value: ''}],
        components: [
            {
                label: 'Label',
                key: 'label',
                input: true,
                type: 'textfield',
            },
            {
                label: 'Value',
                key: 'value',
                input: true,
                type: 'textfield',
                allowCalculateOverride: true,
                calculateValue: {_camelCase: [{var: 'row.label'}]},
                validate: {
                    required: true
                }
            },
        ],
    }];

class RadioField extends Formio.Components.components.radio {
    static editForm() {
        // insert the extras here
        const BASIC_TAB = {
            ...BASIC,
            components: [
                ...BASIC.components,
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

export default RadioField;

// defineChoicesEditFormTabs(Formio.Components.components.radio);
defineChoicesEditFormTabs(Formio.Components.components.selectboxes);
