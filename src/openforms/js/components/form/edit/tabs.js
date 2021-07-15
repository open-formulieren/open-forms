import {Utils} from 'formiojs';

import {getFullyQualifiedUrl} from '../../../utils/urls';
import {as_choices, KNOWN_TYPES} from "./file-mime-types";

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

const FILE = {
    key: 'file',
    label: 'File',
    components: [
        // copied from https://raw.githubusercontent.com/formio/formio.js/master/src/components/file/editForm/File.edit.file.js
        {
            type: 'textfield',
            input: true,
            key: 'fileNameTemplate',
            label: 'File Name Template',
            placeholder: '(optional) {name}-{guid}',
            tooltip: 'Specify template for name of uploaded file(s). Regular template variables are available (`data`, `component`, `user`, `value`, `moment` etc.), also `fileName`, `guid` variables are available. `guid` part must be present, if not found in template, will be added at the end.',
            weight: 25
        },

        {
            "type": "select",
            "key": "file.type",
            "input": true,
            "label": "Select",
            "widget": "choicesjs",
            "tableView": true,
            "multiple": true,
            "data": {
                "values": as_choices(KNOWN_TYPES),
            },
            "defaultValue": [
                "*"
            ],
            weight: 30
        },
        {
            type: 'checkbox',
            input: true,
            key: 'image.resize.apply',
            label: 'Resize image',
            tooltip: 'When this is checked, the image will be resized.',
            weight: 33,
            customConditional: "show = data.file.type.some(function(v) { return (v.indexOf(\"image/\") > -1) || (v == \"*\"); });",
        },
        {
            "key": "image.resize.columns",
            "type": "columns",
            "input": false,
            "tableView": false,
            "label": "Columns",
            "columns": [
                {
                    "components": [
                        {
                            "key": "image.resize.width",
                            "type": "number",
                            "label": "Maximum width",
                            "mask": false,
                            "tableView": false,
                            "delimiter": false,
                            "requireDecimal": false,
                            "inputFormat": "plain",
                            "truncateMultipleSpaces": false,
                            "input": true,
                            "defaultValue": 2000
                        }
                    ],
                    "width": 6,
                    "offset": 0,
                    "push": 0,
                    "pull": 0,
                    "size": "md",
                    "currentWidth": 6
                },
                {
                    "components": [
                        {
                            "key": "image.resize.height",
                            "type": "number",
                            "label": "Maximum height",
                            "mask": false,
                            "tableView": false,
                            "delimiter": false,
                            "requireDecimal": false,
                            "inputFormat": "plain",
                            "truncateMultipleSpaces": false,
                            "input": true ,
                            "defaultValue": 2000
                        }
                    ],
                    "width": 6,
                    "offset": 0,
                    "push": 0,
                    "pull": 0,
                    "size": "md",
                    "currentWidth": 6
                }
            ],
            conditional: {
                json: {'==': [{var: 'data.image.resize.apply'}, true]}
            }
        },
        {
            type: 'textfield',
            input: false,
            key: 'filePattern',
            label: 'File Pattern',
            //placeholder: IMAGE_TYPES.join(","),
            logic: [
                {
                    "name": "filePatternTrigger",
                    "trigger": {
                        "type": "javascript",
                        "javascript": "result = true;"
                    },
                    "actions": [
                        {
                            "name": "filePatternAction",
                            "type": "customAction",
                            "customAction": "value = data.file.type.join(\",\")"
                        }
                    ]
                }
            ],
            tooltip: 'See <a href=\'https://github.com/danialfarid/ng-file-upload#full-reference\' target=\'_blank\'>https://github.com/danialfarid/ng-file-upload#full-reference</a> for how to specify file patterns.',
            weight: 50
        },

        {
            type: 'textfield',
            input: true,
            key: 'fileMaxSize',
            label: 'File Maximum Size',
            placeholder: '10MB',
            tooltip: 'See <a href=\'https://github.com/danialfarid/ng-file-upload#full-reference\' target=\'_blank\'>https://github.com/danialfarid/ng-file-upload#full-reference</a> for how to specify file sizes.',
            weight: 70
        },
        // {
        //     type: 'checkbox',
        //     input: true,
        //     key: 'webcam',
        //     label: 'Enable web camera',
        //     tooltip: 'This will allow using an attached camera to directly take a picture instead of uploading an existing file.',
        //     weight: 32,
        //     conditional: {
        //         json: {'==': [{var: 'data.file.type'}, 'image']}
        //     }
        // },
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
        ADVANCED,
        TEXT_VALIDATION,
        REGISTRATION,
    ]
};

const DEFAULT_FILE_TABS = {
    type: 'tabs',
    key: 'file',
    components: [
        BASIC,
        ADVANCED,
        FILE,
    ]
};

export { DEFAULT_TABS, DEFAULT_TEXT_TABS, DEFAULT_FILE_TABS, BASIC, TEXT_BASIC, ADVANCED, VALIDATION, TEXT_VALIDATION, PREFILL, REGISTRATION};
export default DEFAULT_TABS;
