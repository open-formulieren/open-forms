import {BuilderUtils, Utils} from 'formiojs';

import DEFAULT_TABS, {BASIC, ADVANCED, VALIDATION, REGISTRATION} from './edit/tabs';

export const defineEditFormTabs = (ComponentClass, tabs) => {
    ComponentClass.editForm = function () {
        return {
            components: tabs
        };
    };
};

export const defineCommonEditFormTabs = (ComponentClass, extra = []) => {
    console.debug(`
        defineCommonEditFormTabs is deprecated, please use the 'formio_module' system
        instead to register your component overrides. See 'components/form/time.js'
        for an example.
    `);

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
    defineEditFormTabs(ComponentClass, [TABS]);
};


export const defineChoicesEditFormTabs = (ComponentClass, valueKey = 'values') => {
    defineCommonEditFormTabs(ComponentClass, [
        {
            label: 'Default Value',
            key: 'defaultValue',
            tooltip: 'This will be the initial value for this field, before user interaction.',
            input: true
        },{
            type: 'datagrid',
            input: true,
            label: 'Values',
            key: valueKey,
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
        }]
    );
};
