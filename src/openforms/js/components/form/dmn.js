import {Formio} from 'react-formio';

import {
    LABEL,
    KEY,
    DESCRIPTION,
    SHOW_IN_EMAIL,
    HIDDEN,
    IS_SENSITIVE_DATA,
} from './edit/options';

const Field = Formio.Components.components.field;


export default class DMNEvaluation extends Field {
    static schema(...extend) {
        return Field.schema({
            type: 'camunda:dmn',
            label: 'DMN Evaluation',
            key: 'dmn',
            input: false,
            decisionTableKey: '',
            resultDisplayTemplate: '',
        }, ...extend);
    }

    static get builderInfo() {
        return {
            title: 'DMN Evaluation',
            icon: 'th-list',
            weight: 1000,
            schema: DMNEvaluation.schema(),
        };
    }

    get defaultSchema() {
        return DMNEvaluation.schema();
    }

    static editForm() {
        return {
            components: [
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
                                    type: 'textfield',
                                    key: 'decisionTableKey',
                                    label: 'Decision table key',
                                    defaultValue: '',
                                    description: 'Decision table to evaluate, must exist in the API',
                                    placeholder: 'myDecisionTable'
                                },
                                {
                                    type: 'textarea',
                                    key: 'resultDisplayTemplate',
                                    label: 'Result display template',
                                    description: `Accepts Django template language syntax. The evaluation result is
                                        available under the "result" context variable, while the rest of the submission
                                        data is available as "submission_data".`,
                                    defaultValue: '{% for key, value in result.items %}{{ key }}: {{ value }}{% endfor %}',
                                },
                            ]
                        },
                    ]
                }
            ]
        };
    }

    render() {
        const dmnConfig = this.t(
            'Will evaluate DMN table "{{ decisionTableKey }}"',
            {decisionTableKey: this.component.decisionTableKey}
        );
        return super.render(this.renderTemplate('dmn', {
            dmnConfig: dmnConfig,
        }));
    }
}
