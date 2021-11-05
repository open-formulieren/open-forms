import {Formio, Utils} from 'formiojs';
import DEFAULT_TABS, {ADVANCED, BASIC, REGISTRATION, VALIDATION} from './edit/tabs';

const Select = Formio.Components.components.select;

const values = [
    {
        label: 'Widget Type',
        key: 'widget',
        type: 'select',
        data: {
            values: [
                {
                    value: 'choicesjs',
                    label: 'ChoicesJS'
                },
                {
                    value: 'html5',
                    label: 'HTML 5'
                }
            ]
        },
        dataSrc: 'values',
        template: '<span>{{ item.label }}</span>',
        input: true,
        defaultValue: 'html5'
    },
    {
        type: 'datagrid',
        input: true,
        label: 'Values',
        key: 'data.values',
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
            },
        ],
    },
];


class SelectField extends Select {

    static editForm() {
        const BASIC_TAB = {
            ...BASIC,
            components: [
                ...BASIC.components,
                ...values,
            ]
        };
        const TABS = {
            ...DEFAULT_TABS,
            components: [
                BASIC_TAB,
                ADVANCED,
                VALIDATION,
                REGISTRATION
            ]
        };
        return {components: [TABS]};
    }
}


export default SelectField;
