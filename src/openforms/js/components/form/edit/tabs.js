import {Utils} from 'formiojs';

import {getFullyQualifiedUrl} from '../../../utils/urls';
import {
    LABEL,
    KEY,
    DESCRIPTION,
    SHOW_IN_EMAIL,
    MULTIPLE,
    HIDDEN,
    CLEAR_ON_HIDE,
    IS_SENSITIVE_DATA,
    DEFAULT_VALUE,
    READ_ONLY,
    REGEX_VALIDATION,
} from './options';

/**
 * Define the tabs available when editing components in the form builder.
 */

const BASIC = {
    key: 'basic',
    label: 'Basic',
    components: [
        LABEL,
        KEY,
        DESCRIPTION,
        SHOW_IN_EMAIL,
        MULTIPLE,
        HIDDEN,
        CLEAR_ON_HIDE,
        IS_SENSITIVE_DATA,
        DEFAULT_VALUE,
    ]
};

const SENSITIVE_BASIC = {
    key: 'basic',
    label: 'Basic',
    components: BASIC.components.map(option => {
        if (option === IS_SENSITIVE_DATA) {
            return {...IS_SENSITIVE_DATA, defaultValue: true};
        }
        return option;
    }),
};

const SENSITIVE_READ_ONLY = {
    ...SENSITIVE_BASIC,
    components: [
        ...SENSITIVE_BASIC.components,
        READ_ONLY,
    ]
};


const TEXT_BASIC = {
    key: 'basic',
    label: 'Basic',
    components: [
        ...BASIC.components,
        READ_ONLY,
        {
            weight: 100,
            type: 'textfield',
            input: true,
            key: 'placeholder',
            label: 'Placeholder',
            placeholder: 'Placeholder',
            tooltip: 'The placeholder text that will appear when this field is empty.'
        },
        {
            weight: 1201,
            type: 'checkbox',
            label: 'Show Character Counter',
            tooltip: 'Show a live count of the number of characters.',
            key: 'showCharCount',
            input: true
        }
    ]
};


const CHOICES_BASIC = {
    key: 'basic',
    label: 'Basic',
    components: [
        ...BASIC.components,
        {
            type: 'datagrid',
            input: true,
            label: 'Values',
            key: 'values',
            tooltip: 'The values that can be picked for this field. Values are text submitted with the form data. Labels are text that appears next to the radio buttons on the form.',
            weight: 10,
            reorder: true,
            defaultValue: [{label: '', value: ''}],
            components: [
                {
                    label: 'Label',
                    key: 'label',
                    input: true,
                    type: 'textfield',
                    // Needed to distinguish from the label of the component, since both have key 'label'.
                    // Issue #1422
                    isOptionLabel: true,
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
        }
    ]
};


const LOCATION = {
    key: 'location',
    label: 'Location',
    components: [

        {
            type: 'checkbox',
            key: 'deriveStreetName',
            label: 'Derive street name',
            tooltip: 'If the postcode and house number are entered this field will autofill with the street name'
        },
        {
            type: 'checkbox',
            key: 'deriveCity',
            label: 'Derive city',
            tooltip: 'If the postcode and house number are entered this field will autofill with the city'
        },
        {
            type: 'select',
            input: true,
            label: 'Postcode component',
            key: 'derivePostcode',
            dataSrc: 'custom',
            valueProperty: 'value',
            data: {
                custom(context) {
                    return Utils.getContextComponents(context);
                }
            }
        },
        {
            type: 'select',
            input: true,
            label: 'House number component:',
            key: 'deriveHouseNumber',
            dataSrc: 'custom',
            valueProperty: 'value',
            data: {
                custom(context) {
                    return Utils.getContextComponents(context);
                }
            }
        }
    ]
};


const ADVANCED = {
    key: 'advanced',
    label: 'Advanced',
    components: [
        {
            type: 'panel',
            title: 'Simple',
            key: 'simple-conditional',
            theme: 'default',
            components: [
                {
                    type: 'select',
                    input: true,
                    label: 'This component should Display:',
                    key: 'conditional.show',
                    dataSrc: 'values',
                    data: {
                        values: [
                            {label: 'True', value: 'true'},
                            {label: 'False', value: 'false'}
                        ]
                    }
                },
                {
                    type: 'select',
                    input: true,
                    label: 'When the form component:',
                    key: 'conditional.when',
                    dataSrc: 'custom',
                    valueProperty: 'value',
                    data: {
                        custom(context) {
                            return Utils.getContextComponents(context);
                        }
                    }
                },
                {
                    type: 'textfield',
                    input: true,
                    label: 'Has the value:',
                    key: 'conditional.eq'
                }
            ]
        }
    ]
};


const REGISTRATION = {
    key: 'registration',
    label: 'Registration',
    components: [
        {
            type: 'select',
            key: 'registration.attribute',
            label: 'Registration attribute',
            description: 'Save the value as this attribute in the registration backend system.',
            dataSrc: 'url',
            data: {
                // if the url starts with '/', then formio will prefix it with the formio
                // base URL, which is of course wrong. We there explicitly use the detected
                // host.
                url: getFullyQualifiedUrl('/api/v1/registration/attributes'),
            },
            valueProperty: 'id',
            template: '<span>{{ item.label }}</span>',
        }
    ]
};

const VALIDATION_BASIC = {
    key: 'validation',
    label: 'Validation',
    components: [
        {
            type: 'checkbox',
            input: true,
            label: 'Required',
            tooltip: 'A required field must be filled in before the form can be submitted.',
            key: 'validate.required'
        },
    ]
};


const VALIDATION = {
    key: 'validation',
    label: 'Validation',
    components: [
        ...VALIDATION_BASIC.components,
        {
            type: 'select',
            key: 'validate.plugins',
            label: 'Plugin',
            description: 'Select the plugin(s) to use for the validation functionality.',
            dataSrc: 'url',
            multiple: true,
            data: {
                // if the url starts with '/', then formio will prefix it with the formio
                // base URL, which is of course wrong. We there explicitly use the detected
                // host.
                url: getFullyQualifiedUrl('/api/v1/validation/plugins'),
            },
            valueProperty: 'id',
            template: '<span>{{ item.label }}</span>',
        }
    ]
};


const TEXT_VALIDATION = {
    key: 'validation',
    label: 'Validation',
    components: [
        ...VALIDATION.components,
        {
            weight: 120,
            key: 'validate.maxLength',
            label: 'Maximum Length',
            placeholder: 'Maximum Length',
            type: 'number',
            tooltip: 'The maximum length requirement this field must meet.',
            input: true
        },
        REGEX_VALIDATION
    ]
};


const PREFILL = {
    key: 'prefill',
    label: 'Pre-fill',
    components: [
        {
            type: 'select',
            key: 'prefill.plugin',
            label: 'Plugin',
            description: 'Select the plugin to use for the prefill functionality.',
            dataSrc: 'url',
            data: {
                // if the url starts with '/', then formio will prefix it with the formio
                // base URL, which is of course wrong. We there explicitly use the detected
                // host.
                url: getFullyQualifiedUrl('/api/v1/prefill/plugins'),
            },
            valueProperty: 'id',
            template: '<span>{{ item.label }}</span>',
        },
        {
            type: 'select',
            key: 'prefill.attribute',
            label: 'Plugin attribute',
            description: 'Specify the attribute holding the pre-fill data.',
            dataSrc: 'url',
            data: {
                url: getFullyQualifiedUrl('/api/v1/prefill/plugins/{{ row.prefill.plugin }}/attributes'),
            },
            valueProperty: 'id',
            template: '<span>{{ item.label }}</span>',
        }
    ],
};


const DEFAULT_TABS = {
    type: 'tabs',
    key: 'tabs',
    components: [
        BASIC,
        ADVANCED,
        VALIDATION,
        REGISTRATION,
    ]
};

const DEFAULT_SENSITIVE_TABS = {
    type: 'tabs',
    key: 'tabs',
    components: [
        SENSITIVE_BASIC,
        ADVANCED,
        VALIDATION,
        REGISTRATION,
    ]
};


const DEFAULT_TEXT_TABS = {
    type: 'tabs',
    key: 'tabs',
    components: [
        TEXT_BASIC,
        LOCATION,
        ADVANCED,
        TEXT_VALIDATION,
        REGISTRATION,
        PREFILL
    ]
};

const DEFAULT_CHOICES_TABS = {
    type: 'tabs',
    key: 'tabs',
    components: [
        CHOICES_BASIC,
        ADVANCED,
        VALIDATION,
        REGISTRATION,
    ]
};


export {
    DEFAULT_TABS, DEFAULT_TEXT_TABS, DEFAULT_CHOICES_TABS, DEFAULT_SENSITIVE_TABS, CHOICES_BASIC,
    BASIC, TEXT_BASIC, SENSITIVE_BASIC, LOCATION, ADVANCED, VALIDATION, TEXT_VALIDATION, PREFILL, REGISTRATION,
    VALIDATION_BASIC, SENSITIVE_READ_ONLY
};
export default DEFAULT_TABS;
