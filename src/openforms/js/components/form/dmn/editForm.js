import {getFullyQualifiedUrl} from '../../../utils/urls';

import {
    LABEL,
    KEY,
    DESCRIPTION,
    SHOW_IN_EMAIL,
    HIDDEN,
    IS_SENSITIVE_DATA,
} from '../edit/options';


const whenEngineEqualsJSONLogic = (engine) => {
    return {'==': [
        { var: 'data.dmn.engine' },
        engine,
    ]};
};


const whenEngineCamunda = whenEngineEqualsJSONLogic('camunda');


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
                        data: {
                            values: [
                                {value: 'camunda', label: 'Camunda'},
                                // TODO: #regels-overheid-nl support if it gets its own format?
                            ]
                        },
                        dataSrc: 'values',
                        defaultValue: 'camunda',
                        validate: {
                            required: true,
                        },
                    },
                    {
                        type: 'select',
                        label: 'Decision table',
                        key: 'dmn.camunda.decisionDefinition',
                        data: {
                            url: getFullyQualifiedUrl('/api/v1/dmn/decision-definitions?engine={{ row.dmn.engine }}'),
                        },
                        dataSrc: 'url',
                        validate: {
                            required: true,
                        },
                        conditional: {
                            json: whenEngineCamunda,
                        },
                    },
                    {
                        type: 'select',
                        label: 'Decision table version',
                        key: 'dmn.camunda.decisionDefinitionVersion',
                        data: {
                            url: getFullyQualifiedUrl('/api/v1/dmn/decision-definitions/versions?engine={{ row.dmn.engine }}&definition={{ row.dmn.camunda.decisionDefinition }}'),
                        },
                        clearOnHide: true,
                        dataSrc: 'url',
                        conditional: {
                            // only display the version dropdown if the engine is camunda and a decision
                            // definition has been selected.
                            json: {
                                'and': [
                                    whenEngineCamunda,
                                    { '!!': {var: 'data.dmn.camunda.decisionDefinition'} }
                                ]
                            },
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
