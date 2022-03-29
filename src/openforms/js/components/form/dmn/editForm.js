import {getFullyQualifiedUrl} from '../../../utils/urls';

import {
    LABEL,
    KEY,
    DESCRIPTION,
    SHOW_IN_EMAIL,
    HIDDEN,
    IS_SENSITIVE_DATA,
} from '../edit/options';


const editForm = [
    {
        type: 'tabs',
        key: 'tabs',
        components: [
            {
                key: 'basic',
                label: 'Basic',
                components: [
                    LABEL,
                    KEY,
                    DESCRIPTION,
                    SHOW_IN_EMAIL,
                    HIDDEN,
                    IS_SENSITIVE_DATA,
                ],
            },
            {
                key: 'dmn',
                label: 'DMN Configuration',
                components: [
                    {
                        type: 'select',
                        label: 'Engine',
                        key: 'dmn.engine',
                        tooltip: 'DMN integration is implemented through supported engines.',
                        data: {url: getFullyQualifiedUrl('/api/v1/dmn/plugins')},
                        dataSrc: 'url',
                        lazyLoad: false,
                        validate: {
                            required: true,
                        },
                    },
                    {
                        type: 'select',
                        label: 'Decision table',
                        key: 'dmn.decisionDefinition',
                        data: {
                            url: getFullyQualifiedUrl('/api/v1/dmn/decision-definitions?engine={{ row.dmn.engine.id }}'),
                        },
                        dataSrc: 'url',
                        refreshOn: 'dmn.engine',
                        validate: {
                            required: true,
                        },
                    },
                    {
                        type: 'select',
                        label: 'Decision table version',
                        key: 'dmn.decisionDefinitionVersion',
                        data: {
                            url: getFullyQualifiedUrl('/api/v1/dmn/decision-definitions/versions?engine={{ row.dmn.engine.id }}&definition={{ row.dmn.decisionDefinition.id }}'),
                        },
                        clearOnHide: true,
                        dataSrc: 'url',
                        conditional: {
                            // only display the version dropdown if a decision definition has been selected.
                            json: { '!!': {var: 'row.dmn.decisionDefinition'} },
                        },
                    }
                ]
            },
            {
                key: 'results',
                label: 'Results',
                components: [
                    {
                        type: 'textarea',
                        key: 'dmn.resultDisplayTemplate',
                        label: 'Result display template',
                        description: `Accepts Django template language syntax. The evaluation result is
                            available under the "result" context variable, while the rest of the submission
                            data is available as "submission_data".`,
                        defaultValue: '{% for key, value in result.items %}{{ key }}: {{ value }}{% endfor %}',
                    },
                ],
            }
        ]
    }
];

export default editForm;
