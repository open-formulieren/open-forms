import {Formio} from 'react-formio';

import editForm from './editForm';

const Field = Formio.Components.components.field;


export default class DMNEvaluation extends Field {
    static schema(...extend) {
        return Field.schema({
            type: 'dmn',
            label: 'DMN Evaluation',
            key: 'dmn',
            input: false,
            dmn: {
                engine: '',
                decisionDefinition: '',
                decisionDefinitionVersion: '',
                resultDisplayTemplate: '{% for key, value in result.items %}{{ key }}: {{ value }}{% endfor %}',
                resultDisplay: '',  // evaluated resultDisplayTemplate after the DMN table was evaluated
            },
        }, ...extend);
    }

    static get builderInfo() {
        return {
            title: 'DMN/Business rules evaluation',
            icon: 'th-list',
            weight: 1000,
            schema: DMNEvaluation.schema(),
        };
    }

    get defaultSchema() {
        return DMNEvaluation.schema();
    }

    static editForm() {
        return {components: editForm};
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
