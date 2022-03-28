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
                                }
                            ]
                        }

                    ]
                }
            ]
        };
    }
}
