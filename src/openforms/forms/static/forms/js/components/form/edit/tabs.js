import {BuilderUtils, Utils} from 'formiojs';

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
            type: 'textfield',
            key: 'prefill.attribute',
            label: 'Plugin attribute',
            description: 'Specify the attribute holding the pre-fill data.',
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
    ]
};


export { DEFAULT_TABS, BASIC, ADVANCED, VALIDATION, PREFILL };
export default DEFAULT_TABS;
