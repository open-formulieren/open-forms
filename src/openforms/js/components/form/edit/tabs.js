import {Utils} from 'formiojs';

import {getFullyQualifiedUrl} from '../../../utils/urls';

/**
 * Define the tabs available when editing components in the form builder.
 */

const BASIC = {
    key: 'basic',
    label: 'Basic',
    components: [
        {
            type: 'textfield',
            key: 'label',
            label: 'Label'
        },
        {
            type: 'textfield',
            key: 'key',
            label: 'Property Name'
        },
        {
            type: 'textfield',
            key: 'description',
            label: 'Description'
        },
        {
            type: 'checkbox',
            key: 'showInEmail',
            label: 'Show in email',
            tooltip: 'Whether to show this value in the confirmation email'
        },
        {
            type: 'checkbox',
            key: 'hidden',
            label: 'Hidden',
            tooltip: 'A hidden field is still a part of the form, but is hidden from view.'
        },
        {
            type: 'checkbox',
            key: 'isSensitiveData',
            label: 'Is Sensitive Data',
            tooltip: 'The data entered in this component will be removed in accordance with the privacy settings.'
        },
    ]
};


const TEXT_BASIC = {
    key: 'basic',
    label: 'Basic',
    components: [
        ...BASIC.components,
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


const VALIDATION = {
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
        {
            weight: 130,
            key: 'validate.pattern',
            label: 'Regular Expression Pattern',
            placeholder: 'Regular Expression Pattern',
            type: 'textfield',
            tooltip: 'The regular expression pattern test that the field value must pass before the form can be submitted.',
            input: true
        }
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


const DEFAULT_TEXT_TABS = {
    type: 'tabs',
    key: 'tabs',
    components: [
        TEXT_BASIC,
        LOCATION,
        ADVANCED,
        TEXT_VALIDATION,
        REGISTRATION,
    ]
};


export { DEFAULT_TABS, DEFAULT_TEXT_TABS, BASIC, TEXT_BASIC, LOCATION, ADVANCED,
    VALIDATION, TEXT_VALIDATION, PREFILL, REGISTRATION};
export default DEFAULT_TABS;
